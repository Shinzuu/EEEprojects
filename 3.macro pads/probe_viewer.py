#!/usr/bin/env python3
"""
Pico GPIO probe viewer.
Auto-discovers Pico CircuitPython serial (VID:PID 239a:80f4 or 2e8a:*),
serves a live HTML page on http://localhost:8000 via Server-Sent Events.

Run: python3 probe_viewer.py
Open: http://localhost:8000
"""
import json
import queue
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import serial
import serial.tools.list_ports

PICO_VIDS = {0x239a, 0x2e8a}
BAUD = 115200
HTTP_PORT = 8000


def find_pico_port():
    for p in serial.tools.list_ports.comports():
        if p.vid in PICO_VIDS:
            return p.device
    return None

PINS = [f'GP{i}' for i in list(range(0, 23)) + [26, 27, 28]]
KEY_PINS = [f'GP{i}' for i in range(15)]

state = {p: False for p in PINS}
press_count = {p: 0 for p in PINS}
last_event_time = {p: None for p in PINS}
state_lock = threading.Lock()
clients = []
clients_lock = threading.Lock()

INDEX = """<!doctype html>
<html lang="en"><head><meta charset="utf-8">
<title>Pico GPIO Probe</title>
<style>
:root{--bg:#0f1115;--panel:#161a22;--ink:#e6e6e6;--muted:#9aa0a6;--accent:#6ee7b7;--warn:#f87171;--ok:#34d399;--border:#262b36;--press:#f59e0b;}
@media (prefers-color-scheme: light){:root{--bg:#fafafa;--panel:#fff;--ink:#1a1a1a;--muted:#555;--accent:#047857;--warn:#b91c1c;--ok:#15803d;--border:#e5e7eb;--press:#b45309;}}
*{box-sizing:border-box}body{margin:0;background:var(--bg);color:var(--ink);font:14px/1.5 -apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,sans-serif}
.wrap{max-width:1080px;margin:0 auto;padding:28px 22px 60px}
h1{font-size:24px;margin:0 0 4px}.sub{color:var(--muted);font-size:13px;margin-bottom:18px}
.status{display:inline-block;padding:3px 10px;border-radius:999px;font-size:12px;border:1px solid var(--border);margin-left:6px}
.status.ok{color:var(--ok);border-color:var(--ok)}.status.bad{color:var(--warn);border-color:var(--warn)}
h2{font-size:16px;margin:24px 0 8px;color:var(--accent);border-bottom:1px solid var(--border);padding-bottom:4px}
.grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(110px,1fr));gap:8px;margin-bottom:20px}
.pin{background:var(--panel);border:1px solid var(--border);border-radius:8px;padding:10px;font-family:ui-monospace,monospace;transition:all .08s}
.pin .name{font-size:13px;font-weight:600;color:var(--ink)}
.pin .key{font-size:10px;color:var(--muted);margin-top:2px}
.pin .meta{font-size:10px;color:var(--muted);margin-top:6px;display:flex;justify-content:space-between}
.pin.pressed{background:var(--press);color:#000;border-color:var(--press);transform:scale(1.03);box-shadow:0 0 12px rgba(245,158,11,.5)}
.pin.pressed .name,.pin.pressed .key,.pin.pressed .meta{color:#000}
.log{background:var(--panel);border:1px solid var(--border);border-radius:8px;padding:10px 14px;font-family:ui-monospace,monospace;font-size:12px;max-height:240px;overflow-y:auto}
.log .row{padding:2px 0;border-bottom:1px solid var(--border)}.log .row:last-child{border:0}
.log .t{color:var(--muted);margin-right:8px}.log .press{color:var(--press);font-weight:600}.log .release{color:var(--muted)}
button{background:var(--panel);border:1px solid var(--border);color:var(--ink);padding:5px 12px;border-radius:6px;cursor:pointer;font:inherit}
button:hover{border-color:var(--accent)}
</style></head>
<body><div class="wrap">
<h1>Pico GPIO Probe <span id="conn" class="status bad">disconnected</span></h1>
<div class="sub">Short any GPIO pin to GND. Press = pin reads LOW. Live updates via SSE from <code>/dev/ttyACM0</code>.</div>

<h2>Macropad keys (GP0-GP14)</h2>
<div class="grid" id="key-grid"></div>

<h2>Free pins (GP15-GP22, GP26-GP28)</h2>
<div class="grid" id="free-grid"></div>

<h2>Event log <button onclick="document.getElementById('log').innerHTML=''">clear</button></h2>
<div class="log" id="log"></div>
</div>

<script>
const KEYS = ["GP0","GP1","GP2","GP3","GP4","GP5","GP6","GP7","GP8","GP9","GP10","GP11","GP12","GP13","GP14"];
const KEY_LABELS = ["Q","W","E","R","T","A","S","D","F","G","Z","X","C","V","B"];
const FREE = ["GP15","GP16","GP17","GP18","GP19","GP20","GP21","GP22","GP26","GP27","GP28"];

function buildPin(name, label){
  return `<div class="pin" id="pin-${name}"><div class="name">${name}</div>${label?`<div class="key">${label}</div>`:''}<div class="meta"><span>×<span id="count-${name}">0</span></span><span id="time-${name}">--</span></div></div>`;
}
document.getElementById('key-grid').innerHTML = KEYS.map((n,i)=>buildPin(n, KEY_LABELS[i])).join('');
document.getElementById('free-grid').innerHTML = FREE.map(n=>buildPin(n,'')).join('');

const log = document.getElementById('log');
const conn = document.getElementById('conn');

function addLog(t, name, kind){
  const row = document.createElement('div');
  row.className = 'row';
  const cls = kind==='PRESS'?'press':'release';
  row.innerHTML = `<span class="t">${t}</span><span class="${cls}">${kind}</span> ${name}`;
  log.insertBefore(row, log.firstChild);
  while(log.children.length>200) log.removeChild(log.lastChild);
}

const es = new EventSource('/events');
es.onopen = ()=>{conn.textContent='connected';conn.className='status ok';};
es.onerror = ()=>{conn.textContent='disconnected';conn.className='status bad';};
es.addEventListener('snapshot', (e)=>{
  const d = JSON.parse(e.data);
  for(const [n,info] of Object.entries(d)){
    const el = document.getElementById('pin-'+n);
    if(!el) continue;
    el.classList.toggle('pressed', info.pressed);
    document.getElementById('count-'+n).textContent = info.count;
    if(info.last) document.getElementById('time-'+n).textContent = info.last;
  }
});
es.addEventListener('event', (e)=>{
  const d = JSON.parse(e.data);
  const el = document.getElementById('pin-'+d.pin);
  if(el) el.classList.toggle('pressed', d.kind==='PRESS');
  document.getElementById('count-'+d.pin).textContent = d.count;
  document.getElementById('time-'+d.pin).textContent = d.time;
  addLog(d.time, d.pin, d.kind);
});
</script>
</body></html>"""


def serial_reader():
    while True:
        port = find_pico_port()
        if not port:
            print("[serial] no Pico found, retrying in 2s")
            time.sleep(2)
            continue
        try:
            ser = serial.Serial(port, BAUD, timeout=1)
            print(f"[serial] opened {port}")
            broadcast({'type': 'log', 'msg': f'serial connected ({port})'})
            while True:
                line = ser.readline().decode(errors='replace').strip()
                if not line:
                    continue
                parts = line.split()
                if len(parts) != 2 or parts[0] not in ('PRESS', 'RELEASE'):
                    continue
                kind, pin = parts
                if pin not in state:
                    continue
                ts = time.strftime('%H:%M:%S')
                with state_lock:
                    state[pin] = (kind == 'PRESS')
                    if kind == 'PRESS':
                        press_count[pin] += 1
                    last_event_time[pin] = ts
                    cnt = press_count[pin]
                broadcast({
                    'type': 'event',
                    'pin': pin, 'kind': kind, 'count': cnt, 'time': ts,
                })
        except serial.SerialException as e:
            print(f"[serial] error: {e}; retrying in 2s")
            time.sleep(2)


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


def snapshot():
    with state_lock:
        return {
            p: {'pressed': state[p], 'count': press_count[p], 'last': last_event_time[p]}
            for p in PINS
        }


class Handler(BaseHTTPRequestHandler):
    def log_message(self, *a):
        pass

    def do_GET(self):
        if self.path == '/' or self.path == '/index.html':
            body = INDEX.encode()
            self.send_response(200)
            self.send_header('Content-Type', 'text/html; charset=utf-8')
            self.send_header('Content-Length', str(len(body)))
            self.end_headers()
            self.wfile.write(body)
            return
        if self.path == '/events':
            self.send_response(200)
            self.send_header('Content-Type', 'text/event-stream')
            self.send_header('Cache-Control', 'no-cache')
            self.send_header('Connection', 'keep-alive')
            self.end_headers()
            q = queue.Queue(maxsize=200)
            with clients_lock:
                clients.append(q)
            try:
                snap = json.dumps(snapshot())
                self.wfile.write(f"event: snapshot\ndata: {snap}\n\n".encode())
                self.wfile.flush()
                while True:
                    try:
                        msg = q.get(timeout=15)
                        data = json.loads(msg)
                        ev = data.get('type', 'message')
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
        self.send_error(404)


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
