#!/usr/bin/env python3
"""
Macropad GPIO -> grid mapping wizard.
3 rows x 5 columns. Order: column-major.
  (0,0) (1,0) (2,0)  (0,1) (1,1) (2,1)  ... (2,4)

Workflow:
  1. Run this script.
  2. Open http://127.0.0.1:8000.
  3. Wizard highlights one cell at a time, asks you to press its switch.
  4. First GPIO that goes LOW (-> GND) is bound to that cell.
  5. Repeat for all 15 cells.
  6. Click "Save mapping" -> writes keymap.json + a ready-to-paste KMK PINS list.

Auto-discovers Pico via USB VID (239a / 2e8a). Survives replug.
"""
import json
import queue
import threading
import time
from pathlib import Path
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import serial
import serial.tools.list_ports

PICO_VIDS = {0x239a, 0x2e8a}
BAUD = 115200
HTTP_PORT = 8000
ROWS, COLS = 3, 5
OUT_DIR = Path(__file__).parent
KEYMAP_JSON = OUT_DIR / 'keymap.json'
KMK_SNIPPET = OUT_DIR / 'keymap_pins.py'

ALL_PINS = [f'GP{i}' for i in list(range(0, 23)) + [26, 27, 28]]

ORDER = [(r, c) for c in range(COLS) for r in range(ROWS)]

state_lock = threading.Lock()
mapping = {}
current_idx = 0
clients = []
clients_lock = threading.Lock()


def find_pico_port():
    for p in serial.tools.list_ports.comports():
        if p.vid in PICO_VIDS:
            return p.device
    return None


INDEX = """<!doctype html>
<html lang="en"><head><meta charset="utf-8">
<title>Macropad mapping wizard</title>
<style>
:root{--bg:#0f1115;--panel:#161a22;--ink:#e6e6e6;--muted:#9aa0a6;--accent:#6ee7b7;--warn:#f87171;--ok:#34d399;--border:#262b36;--target:#f59e0b;--done:#34d399;}
@media (prefers-color-scheme: light){:root{--bg:#fafafa;--panel:#fff;--ink:#1a1a1a;--muted:#555;--accent:#047857;--warn:#b91c1c;--ok:#15803d;--border:#e5e7eb;--target:#b45309;--done:#15803d;}}
*{box-sizing:border-box}body{margin:0;background:var(--bg);color:var(--ink);font:14px/1.5 -apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,sans-serif}
.wrap{max-width:920px;margin:0 auto;padding:28px 22px 60px}
h1{font-size:24px;margin:0 0 4px}.sub{color:var(--muted);font-size:13px;margin-bottom:18px}
.status{display:inline-block;padding:3px 10px;border-radius:999px;font-size:12px;border:1px solid var(--border);margin-left:6px}
.status.ok{color:var(--ok);border-color:var(--ok)}.status.bad{color:var(--warn);border-color:var(--warn)}
h2{font-size:16px;margin:24px 0 8px;color:var(--accent);border-bottom:1px solid var(--border);padding-bottom:4px}
.prompt{background:var(--panel);border:1px solid var(--border);border-radius:8px;padding:14px 18px;margin:14px 0;font-size:15px}
.prompt b{color:var(--target);font-family:ui-monospace,monospace}
.grid{display:grid;grid-template-columns:repeat(5,minmax(80px,1fr));gap:10px;margin:14px 0;max-width:560px}
.cell{background:var(--panel);border:1px solid var(--border);border-radius:8px;padding:14px 8px;text-align:center;font-family:ui-monospace,monospace;min-height:78px;display:flex;flex-direction:column;justify-content:center;transition:all .12s}
.cell .rc{font-size:11px;color:var(--muted)}.cell .pin{font-size:14px;font-weight:600;margin-top:4px;color:var(--accent)}.cell .empty{font-size:11px;color:var(--muted);margin-top:4px}
.cell.target{border-color:var(--target);background:rgba(245,158,11,.12);box-shadow:0 0 14px rgba(245,158,11,.4);transform:scale(1.04)}
.cell.target .rc{color:var(--target)}
.cell.done{border-color:var(--done)}.cell.done .pin{color:var(--done)}
.btnrow{display:flex;gap:10px;margin-top:16px;flex-wrap:wrap}
button{background:var(--panel);border:1px solid var(--border);color:var(--ink);padding:7px 14px;border-radius:6px;cursor:pointer;font:inherit}
button:hover{border-color:var(--accent)}button.primary{background:var(--accent);color:#000;border-color:var(--accent)}
button:disabled{opacity:.4;cursor:not-allowed}
.log{background:var(--panel);border:1px solid var(--border);border-radius:8px;padding:10px 14px;font-family:ui-monospace,monospace;font-size:12px;max-height:160px;overflow-y:auto;margin-top:10px}
.log .row{padding:1px 0}
pre{background:var(--panel);border:1px solid var(--border);border-radius:8px;padding:12px 14px;overflow-x:auto;font-size:12.5px}
</style></head>
<body><div class="wrap">
<h1>Macropad mapping wizard <span id="conn" class="status bad">disconnected</span></h1>
<div class="sub">3 rows x 5 columns. Order: <b>column-major</b> &mdash; (0,0) (1,0) (2,0) (0,1) (1,1) (2,1) ... Press the highlighted cell's switch.</div>

<div class="prompt" id="prompt">Waiting for serial...</div>

<div class="grid" id="grid"></div>

<div class="btnrow">
  <button id="skip">Skip cell</button>
  <button id="back">Back</button>
  <button id="reset">Reset all</button>
  <button id="save" class="primary" disabled>Save mapping</button>
</div>

<h2>Live event log</h2>
<div class="log" id="log"></div>

<h2>Output preview</h2>
<pre id="preview">(complete the mapping to generate)</pre>
</div>

<script>
const ROWS=3, COLS=5;
const ORDER=[]; for(let c=0;c<COLS;c++) for(let r=0;r<ROWS;r++) ORDER.push([r,c]);
let mapping={}, idx=0;

const grid=document.getElementById('grid');
const cells={};
for(let r=0;r<ROWS;r++) for(let c=0;c<COLS;c++){
  const el=document.createElement('div');
  el.className='cell';el.id=`cell-${r}-${c}`;
  el.innerHTML=`<div class="rc">(${r},${c})</div><div class="empty">--</div>`;
  el.style.gridRow=r+1;el.style.gridColumn=c+1;
  cells[`${r},${c}`]=el;grid.appendChild(el);
}

function render(){
  for(const k in cells){
    cells[k].classList.remove('target','done');
    const [r,c]=k.split(',').map(Number);
    const pin=mapping[k];
    if(pin){cells[k].classList.add('done');cells[k].innerHTML=`<div class="rc">(${r},${c})</div><div class="pin">${pin}</div>`;}
    else{cells[k].innerHTML=`<div class="rc">(${r},${c})</div><div class="empty">--</div>`;}
  }
  if(idx<ORDER.length){
    const [r,c]=ORDER[idx];
    cells[`${r},${c}`].classList.add('target');
    document.getElementById('prompt').innerHTML=`Press switch for cell <b>(${r},${c})</b> &mdash; position ${idx+1}/${ORDER.length}.`;
  } else {
    document.getElementById('prompt').innerHTML=`<b style="color:var(--done)">All 15 cells mapped.</b> Click <b>Save mapping</b>.`;
    document.getElementById('save').disabled=false;
  }
  updatePreview();
}

function updatePreview(){
  const done=Object.keys(mapping).length;
  if(done===0){document.getElementById('preview').textContent='(complete the mapping to generate)';return;}
  const lines=['# Order: row-major (row 0 left->right, then row 1, then row 2)','PINS = ['];
  for(let r=0;r<ROWS;r++){
    const row=[];
    for(let c=0;c<COLS;c++){
      const p=mapping[`${r},${c}`]||'????';
      row.push(`board.${p}`);
    }
    lines.push('    '+row.join(', ')+',');
  }
  lines.push(']');
  document.getElementById('preview').textContent=lines.join('\\n');
}

const log=document.getElementById('log');
function addLog(t,name,kind){
  const row=document.createElement('div');row.className='row';
  row.textContent=`${t} ${kind} ${name}`;
  log.insertBefore(row,log.firstChild);
  while(log.children.length>80) log.removeChild(log.lastChild);
}

const conn=document.getElementById('conn');
const es=new EventSource('/events');
es.onopen=()=>{conn.textContent='connected';conn.className='status ok';};
es.onerror=()=>{conn.textContent='disconnected';conn.className='status bad';};
es.addEventListener('snapshot',(e)=>{const d=JSON.parse(e.data);mapping=d.mapping;idx=d.idx;render();});
es.addEventListener('press',(e)=>{
  const d=JSON.parse(e.data);
  addLog(d.time,d.pin,'PRESS');
  if(idx>=ORDER.length) return;
  if(Object.values(mapping).includes(d.pin)){
    addLog(d.time,d.pin,'(already used, ignored)');return;
  }
  const [r,c]=ORDER[idx];
  mapping[`${r},${c}`]=d.pin;idx++;render();
  fetch('/state',{method:'POST',body:JSON.stringify({mapping,idx})});
});
es.addEventListener('release',(e)=>{const d=JSON.parse(e.data);addLog(d.time,d.pin,'RELEASE');});

document.getElementById('skip').onclick=()=>{if(idx<ORDER.length){idx++;render();fetch('/state',{method:'POST',body:JSON.stringify({mapping,idx})});}};
document.getElementById('back').onclick=()=>{
  if(idx>0){idx--;const [r,c]=ORDER[idx];delete mapping[`${r},${c}`];render();fetch('/state',{method:'POST',body:JSON.stringify({mapping,idx})});}
};
document.getElementById('reset').onclick=()=>{
  if(!confirm('Clear all mappings?'))return;
  mapping={};idx=0;render();fetch('/state',{method:'POST',body:JSON.stringify({mapping,idx})});
};
document.getElementById('save').onclick=async()=>{
  const r=await fetch('/save',{method:'POST',body:JSON.stringify({mapping})});
  const j=await r.json();alert('Saved:\\n'+j.files.join('\\n'));
};
render();
</script>
</body></html>"""


def broadcast(msg):
    payload = json.dumps(msg)
    with clients_lock:
        dead = []
        for q in clients:
            try:
                q.put_nowait(payload)
            except queue.Full:
                dead.append(q)
        for q in dead:
            clients.remove(q)


def serial_reader():
    last_state = {p: True for p in ALL_PINS}
    while True:
        port = find_pico_port()
        if not port:
            time.sleep(2)
            continue
        try:
            ser = serial.Serial(port, BAUD, timeout=1)
            print(f"[serial] {port}")
            while True:
                raw = ser.readline().decode(errors='replace').strip()
                if not raw:
                    continue
                parts = raw.split()
                if len(parts) != 2 or parts[0] not in ('PRESS', 'RELEASE'):
                    continue
                kind, pin = parts
                if pin not in last_state:
                    continue
                ts = time.strftime('%H:%M:%S')
                last_state[pin] = (kind != 'PRESS')
                ev = 'press' if kind == 'PRESS' else 'release'
                broadcast({'type': ev, 'pin': pin, 'time': ts})
        except serial.SerialException as e:
            print(f"[serial] {e}")
            time.sleep(2)


def write_outputs():
    with state_lock:
        m = dict(mapping)
    KEYMAP_JSON.write_text(json.dumps(m, indent=2))
    lines = [
        '# Generated by map_wizard.py',
        '# 3 rows x 5 cols, row-major order for KMK PINS list.',
        '# Replace the PINS = [...] block in your KMK code.py with this.',
        '',
        'import board',
        '',
        'PINS = [',
    ]
    for r in range(ROWS):
        row_parts = []
        for c in range(COLS):
            p = m.get(f'{r},{c}', '????')
            row_parts.append(f'board.{p}')
        lines.append('    ' + ', '.join(row_parts) + ',  # row ' + str(r))
    lines.append(']')
    KMK_SNIPPET.write_text('\n'.join(lines) + '\n')
    return [str(KEYMAP_JSON), str(KMK_SNIPPET)]


class Handler(BaseHTTPRequestHandler):
    def log_message(self, *a):
        pass

    def _send(self, code, body, ctype='application/json'):
        b = body.encode() if isinstance(body, str) else body
        self.send_response(code)
        self.send_header('Content-Type', ctype)
        self.send_header('Content-Length', str(len(b)))
        self.end_headers()
        self.wfile.write(b)

    def do_GET(self):
        if self.path in ('/', '/index.html'):
            self._send(200, INDEX, 'text/html; charset=utf-8')
            return
        if self.path == '/events':
            self.send_response(200)
            self.send_header('Content-Type', 'text/event-stream')
            self.send_header('Cache-Control', 'no-cache')
            self.end_headers()
            q = queue.Queue(maxsize=200)
            with clients_lock:
                clients.append(q)
            try:
                with state_lock:
                    snap = json.dumps({'mapping': mapping, 'idx': current_idx})
                self.wfile.write(f"event: snapshot\ndata: {snap}\n\n".encode())
                self.wfile.flush()
                while True:
                    try:
                        msg = q.get(timeout=15)
                        d = json.loads(msg)
                        ev = d.get('type', 'message')
                        self.wfile.write(f"event: {ev}\ndata: {msg}\n\n".encode())
                        self.wfile.flush()
                    except queue.Empty:
                        self.wfile.write(b": ping\n\n")
                        self.wfile.flush()
            except (BrokenPipeError, ConnectionResetError):
                pass
            finally:
                with clients_lock:
                    if q in clients:
                        clients.remove(q)
            return
        self._send(404, '{"err":"not found"}')

    def do_POST(self):
        global current_idx, mapping
        n = int(self.headers.get('Content-Length', 0))
        body = self.rfile.read(n).decode()
        try:
            data = json.loads(body) if body else {}
        except json.JSONDecodeError:
            self._send(400, '{"err":"bad json"}')
            return
        if self.path == '/state':
            with state_lock:
                mapping = data.get('mapping', {})
                current_idx = data.get('idx', 0)
            self._send(200, '{"ok":true}')
            return
        if self.path == '/save':
            with state_lock:
                mapping = data.get('mapping', mapping)
            files = write_outputs()
            self._send(200, json.dumps({'ok': True, 'files': files}))
            return
        self._send(404, '{"err":"not found"}')


def main():
    threading.Thread(target=serial_reader, daemon=True).start()
    httpd = ThreadingHTTPServer(('127.0.0.1', HTTP_PORT), Handler)
    print(f"[http] http://127.0.0.1:{HTTP_PORT}")
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        pass


if __name__ == '__main__':
    main()
