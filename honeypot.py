import json
import os
import threading
from datetime import datetime
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import parse_qs, urlparse
from flask import Flask, jsonify, render_template_string

app = Flask(__name__)
ALERT_LOG = "honeypot_alerts.json"
HONEYPOT_PORT = 8080

FAKE_LOGIN_PAGE = """<!DOCTYPE html>
<html><head><meta charset="UTF-8"><title>Admin Portal — SecureCorp</title>
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600&display=swap" rel="stylesheet">
<style>
*{margin:0;padding:0;box-sizing:border-box;}
body{font-family:'Inter',sans-serif;background:#0f1117;display:flex;justify-content:center;align-items:center;min-height:100vh;}
.wrap{background:#1a1d27;border:1px solid #2a2d3d;border-radius:12px;padding:40px 36px;width:360px;box-shadow:0 24px 64px rgba(0,0,0,0.5);}
.logo{text-align:center;margin-bottom:28px;}
.logo h1{color:#fff;font-size:20px;font-weight:600;}
.logo p{color:#6b7280;font-size:12px;margin-top:4px;}
.lock{font-size:36px;margin-bottom:10px;}
label{display:block;color:#9ca3af;font-size:12px;font-weight:500;margin-bottom:6px;}
input{width:100%;padding:10px 14px;background:#0f1117;border:1px solid #2a2d3d;border-radius:8px;color:#fff;font-size:14px;outline:none;margin-bottom:14px;}
input:focus{border-color:#4f46e5;}
button{width:100%;padding:11px;background:#4f46e5;color:#fff;border:none;border-radius:8px;font-size:14px;font-weight:600;cursor:pointer;}
button:hover{background:#4338ca;}
.footer{text-align:center;color:#374151;font-size:11px;margin-top:20px;}
</style></head>
<body><div class="wrap">
  <div class="logo"><div class="lock">🔐</div><h1>SecureCorp Admin</h1><p>Internal Portal — Authorized Access Only</p></div>
  <form method="POST" action="/login">
    <label>Username</label><input type="text" name="username" placeholder="Enter username" required/>
    <label>Password</label><input type="password" name="password" placeholder="Enter password" required/>
    <button type="submit">Sign In</button>
  </form>
  <div class="footer">SecureCorp v2.4.1 · Enterprise Edition</div>
</div></body></html>"""

FAKE_ADMIN_PAGE = """<!DOCTYPE html>
<html><head><meta charset="UTF-8"><title>Admin Panel — CorpNet</title>
<link href="https://fonts.googleapis.com/css2?family=Roboto+Mono:wght@400;500&family=Roboto:wght@400;500;700&display=swap" rel="stylesheet">
<style>
*{margin:0;padding:0;box-sizing:border-box;}
body{font-family:'Roboto',sans-serif;background:#111827;display:flex;justify-content:center;align-items:center;min-height:100vh;}
.panel{background:#1f2937;border:1px solid #374151;border-radius:8px;padding:36px;width:400px;}
.header{display:flex;align-items:center;gap:12px;margin-bottom:28px;padding-bottom:20px;border-bottom:1px solid #374151;}
.icon{width:44px;height:44px;background:linear-gradient(135deg,#059669,#10b981);border-radius:10px;display:flex;align-items:center;justify-content:center;font-size:22px;}
.title h2{color:#f9fafb;font-size:18px;font-weight:700;}
.title p{color:#6b7280;font-size:12px;margin-top:2px;}
.field{margin-bottom:16px;}
.field label{display:block;color:#9ca3af;font-size:11px;font-weight:500;text-transform:uppercase;letter-spacing:0.5px;margin-bottom:6px;}
.field input{width:100%;padding:10px 14px;background:#111827;border:1px solid #374151;border-radius:6px;color:#f9fafb;font-size:14px;font-family:'Roboto Mono';outline:none;}
.field input:focus{border-color:#059669;}
.btn{width:100%;padding:11px;background:#059669;color:#fff;border:none;border-radius:6px;font-size:14px;font-weight:600;cursor:pointer;margin-top:4px;}
.btn:hover{background:#047857;}
.notice{text-align:center;color:#4b5563;font-size:11px;margin-top:16px;}
.tag{display:inline-block;background:#064e3b;color:#6ee7b7;padding:2px 8px;border-radius:4px;font-size:10px;font-family:'Roboto Mono';}
</style></head>
<body><div class="panel">
  <div class="header">
    <div class="icon">🛡</div>
    <div class="title"><h2>CorpNet Admin Panel</h2><p>Infrastructure Management System <span class="tag">v3.1</span></p></div>
  </div>
  <form method="POST" action="/admin">
    <div class="field"><label>Administrator ID</label><input type="text" name="username" placeholder="admin@corpnet.internal" required/></div>
    <div class="field"><label>Security Token</label><input type="password" name="password" placeholder="••••••••••••" required/></div>
    <button class="btn" type="submit">Authenticate →</button>
  </form>
  <div class="notice">⚠ Unauthorized access is monitored and prosecuted · CorpNet Security Policy v7</div>
</div></body></html>"""

FAKE_DASHBOARD_PAGE = """<!DOCTYPE html>
<html><head><meta charset="UTF-8"><title>Employee Dashboard — IntraConnect</title>
<link href="https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700&display=swap" rel="stylesheet">
<style>
*{margin:0;padding:0;box-sizing:border-box;}
body{font-family:'Plus Jakarta Sans',sans-serif;background:linear-gradient(135deg,#1e1b4b,#0f172a);display:flex;justify-content:center;align-items:center;min-height:100vh;}
.card{background:rgba(255,255,255,0.05);backdrop-filter:blur(20px);border:1px solid rgba(255,255,255,0.1);border-radius:16px;padding:40px;width:420px;box-shadow:0 32px 80px rgba(0,0,0,0.4);}
.top{text-align:center;margin-bottom:32px;}
.logo-ring{width:64px;height:64px;border-radius:50%;background:linear-gradient(135deg,#818cf8,#6366f1);display:flex;align-items:center;justify-content:center;font-size:30px;margin:0 auto 14px;}
h2{color:#e2e8f0;font-size:22px;font-weight:700;}
p{color:#94a3b8;font-size:13px;margin-top:4px;}
.tabs{display:flex;gap:8px;margin-bottom:24px;}
.tab{flex:1;padding:8px;border-radius:8px;font-size:12px;font-weight:600;text-align:center;cursor:pointer;border:1px solid transparent;}
.tab.active{background:rgba(99,102,241,0.2);border-color:rgba(99,102,241,0.4);color:#818cf8;}
.tab.inactive{color:#64748b;border-color:rgba(255,255,255,0.05);}
label{display:block;color:#94a3b8;font-size:12px;font-weight:500;margin-bottom:6px;}
input{width:100%;padding:12px 16px;background:rgba(255,255,255,0.05);border:1px solid rgba(255,255,255,0.1);border-radius:10px;color:#e2e8f0;font-size:14px;outline:none;margin-bottom:16px;}
input:focus{border-color:#6366f1;background:rgba(99,102,241,0.08);}
.btn{width:100%;padding:13px;background:linear-gradient(135deg,#6366f1,#818cf8);color:#fff;border:none;border-radius:10px;font-size:14px;font-weight:700;cursor:pointer;letter-spacing:0.3px;}
.btn:hover{opacity:0.9;}
.links{display:flex;justify-content:space-between;margin-top:16px;}
.links a{color:#6366f1;font-size:12px;text-decoration:none;}
.divider{height:1px;background:rgba(255,255,255,0.07);margin:20px 0;}
.sso{width:100%;padding:11px;background:rgba(255,255,255,0.05);border:1px solid rgba(255,255,255,0.1);border-radius:10px;color:#e2e8f0;font-size:13px;font-weight:600;cursor:pointer;display:flex;align-items:center;justify-content:center;gap:8px;}
</style></head>
<body><div class="card">
  <div class="top">
    <div class="logo-ring">🏢</div>
    <h2>IntraConnect Portal</h2>
    <p>Employee Dashboard · Single Sign-On</p>
  </div>
  <div class="tabs">
    <div class="tab active">Employee Login</div>
    <div class="tab inactive">Guest Access</div>
  </div>
  <form method="POST" action="/dashboard">
    <label>Work Email</label><input type="text" name="username" placeholder="you@company.com" required/>
    <label>Password</label><input type="password" name="password" placeholder="Enter your password" required/>
    <button class="btn" type="submit">Continue to Dashboard</button>
  </form>
  <div class="links"><a href="#">Forgot password?</a><a href="#">IT Support</a></div>
  <div class="divider"></div>
  <button class="sso">🔑 Sign in with Microsoft SSO</button>
</div></body></html>"""

FAKE_DENIED = """<!DOCTYPE html>
<html><head><meta charset="UTF-8"><title>Access Denied</title>
<meta http-equiv="refresh" content="3;url=/login">
<style>*{margin:0;padding:0;}body{font-family:sans-serif;background:#0f1117;display:flex;justify-content:center;align-items:center;min-height:100vh;color:#fff;text-align:center;}</style>
</head><body><div><div style="font-size:48px;margin-bottom:16px">⚠️</div>
<h2 style="color:#ef4444">Session Expired</h2>
<p style="color:#6b7280;margin-top:8px">Redirecting to login...</p></div></body></html>"""

# ─────────────────────────────────────────────────────────────
#  ALERT STORAGE
# ─────────────────────────────────────────────────────────────
def load_alerts():
    if not os.path.exists(ALERT_LOG):
        return []
    with open(ALERT_LOG, "r") as f:
        return json.load(f)

def save_alert(alert):
    alerts = load_alerts()
    alert["id"] = len(alerts) + 1
    alerts.append(alert)
    with open(ALERT_LOG, "w") as f:
        json.dump(alerts, f, indent=4)
    print(f"  ALERT #{alert['id']} — {alert['ip']} [{alert['method']} {alert['path']}]")

# ─────────────────────────────────────────────────────────────
#  HONEYPOT HTTP SERVER
# ─────────────────────────────────────────────────────────────
def get_page_for_path(path):
    p = path.split("?")[0].rstrip("/")
    if p in ("/admin",):
        return FAKE_ADMIN_PAGE, "Admin Panel"
    elif p in ("/dashboard",):
        return FAKE_DASHBOARD_PAGE, "Employee Dashboard"
    else:
        return FAKE_LOGIN_PAGE, "Login Portal"

class HoneypotHandler(BaseHTTPRequestHandler):
    def log_message(self, *args): pass

    def do_GET(self):
        page, trap_name = get_page_for_path(self.path)
        save_alert({
            "timestamp": datetime.now().isoformat(),
            "ip": self.client_address[0],
            "method": "GET",
            "path": self.path,
            "user_agent": self.headers.get("User-Agent", "Unknown"),
            "credentials": None,
            "severity": "MEDIUM",
            "trap": trap_name
        })
        self.send_response(200)
        self.send_header("Content-type", "text/html")
        self.end_headers()
        self.wfile.write(page.encode())

    def do_POST(self):
        length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(length).decode()
        params = parse_qs(body)
        username = params.get("username", [""])[0]
        password = params.get("password", [""])[0]
        _, trap_name = get_page_for_path(self.path)
        save_alert({
            "timestamp": datetime.now().isoformat(),
            "ip": self.client_address[0],
            "method": "POST",
            "path": self.path,
            "user_agent": self.headers.get("User-Agent", "Unknown"),
            "credentials": {"username": username, "password": password},
            "severity": "HIGH",
            "trap": trap_name
        })
        self.send_response(200)
        self.send_header("Content-type", "text/html")
        self.end_headers()
        self.wfile.write(FAKE_DENIED.encode())

honeypot_running = False
honeypot_server  = None

def start_honeypot():
    global honeypot_server, honeypot_running
    honeypot_server = HTTPServer(("0.0.0.0", HONEYPOT_PORT), HoneypotHandler)
    honeypot_running = True
    honeypot_server.serve_forever()

def stop_honeypot():
    global honeypot_server, honeypot_running
    if honeypot_server:
        honeypot_server.shutdown()
        honeypot_running = False

# ─────────────────────────────────────────────────────────────
#  DASHBOARD HTML
# ─────────────────────────────────────────────────────────────
DASHBOARD = r"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>HoneyOps — Threat Intelligence</title>
<link href="https://fonts.googleapis.com/css2?family=DM+Mono:wght@400;500&family=Syne:wght@700;800&family=Cabinet+Grotesk:wght@400;500;700;800&display=swap" rel="stylesheet">
<style>
:root{
  --bg:#08090d;--bg2:#0d0f15;--bg3:#11141e;--card:#0f1219;
  --border:#1c2030;--red:#ff4060;--orange:#ff8c42;--yellow:#ffd166;
  --green:#06d6a0;--blue:#118ab2;--purple:#9b5de5;
  --text:#dde2f0;--muted:#4a5268;
}
*{margin:0;padding:0;box-sizing:border-box;}
body{background:var(--bg);color:var(--text);font-family:'Cabinet Grotesk',sans-serif;min-height:100vh;}

.topbar{display:flex;align-items:center;justify-content:space-between;padding:16px 32px;background:var(--bg2);border-bottom:1px solid var(--border);}
.brand{display:flex;align-items:center;gap:14px;}
.brand-icon{width:40px;height:40px;background:linear-gradient(135deg,#ff4060,#ff8c42);border-radius:10px;display:flex;align-items:center;justify-content:center;font-size:20px;}
.brand-name{font-family:'Syne';font-size:20px;font-weight:800;background:linear-gradient(135deg,#ff4060,#ff8c42);-webkit-background-clip:text;-webkit-text-fill-color:transparent;background-clip:text;}
.brand-sub{font-family:'DM Mono';font-size:10px;color:var(--muted);letter-spacing:2px;text-transform:uppercase;}
.topbar-right{display:flex;align-items:center;gap:16px;}
#clock{font-family:'DM Mono';font-size:12px;color:var(--muted);}
.hp-btn{display:flex;align-items:center;gap:10px;padding:10px 20px;border-radius:8px;font-family:'Syne';font-size:13px;font-weight:700;cursor:pointer;border:none;letter-spacing:0.5px;transition:all 0.2s;}
.hp-btn.on{background:rgba(6,214,160,0.1);border:1px solid rgba(6,214,160,0.4);color:var(--green);}
.hp-btn.off{background:rgba(255,64,96,0.1);border:1px solid rgba(255,64,96,0.4);color:var(--red);}
.dot{width:8px;height:8px;border-radius:50%;}
.dot.on{background:var(--green);box-shadow:0 0 8px var(--green);animation:blink 1.5s infinite;}
.dot.off{background:var(--muted);}
@keyframes blink{0%,100%{opacity:1}50%{opacity:0.3}}

.content{padding:28px 32px;}

.metrics{display:grid;grid-template-columns:repeat(5,1fr);gap:12px;margin-bottom:24px;}
.metric{background:var(--card);border:1px solid var(--border);border-radius:10px;padding:20px;position:relative;overflow:hidden;transition:all 0.2s;cursor:default;}
.metric.clickable{cursor:pointer;}
.metric.clickable:hover{transform:translateY(-3px);box-shadow:0 10px 28px rgba(0,0,0,0.4);border-color:var(--muted);}
.metric.active-filter{outline:2px solid var(--muted);outline-offset:2px;}
.metric::before{content:'';position:absolute;top:0;left:0;right:0;height:3px;}
.m-red::before{background:var(--red);}
.m-orange::before{background:var(--orange);}
.m-yellow::before{background:var(--yellow);}
.m-green::before{background:var(--green);}
.m-purple::before{background:var(--purple);}
.metric-label{font-family:'DM Mono';font-size:10px;color:var(--muted);letter-spacing:2px;text-transform:uppercase;margin-bottom:10px;}
.metric-value{font-family:'Syne';font-size:32px;font-weight:800;}
.mv-red{color:var(--red);}
.mv-orange{color:var(--orange);}
.mv-yellow{color:var(--yellow);}
.mv-green{color:var(--green);}
.mv-purple{color:var(--purple);}
.metric-hint{font-family:'DM Mono';font-size:9px;color:var(--muted);opacity:0.5;margin-top:6px;}

.filter-bar{display:none;align-items:center;gap:10px;margin-bottom:16px;padding:10px 16px;background:var(--bg2);border:1px solid var(--border);border-radius:8px;font-family:'DM Mono';font-size:12px;color:var(--orange);}
.filter-bar.visible{display:flex;}
.filter-bar span{flex:1;}
.filter-clear{background:transparent;border:1px solid var(--border);color:var(--muted);padding:4px 12px;border-radius:5px;font-family:'DM Mono';font-size:11px;cursor:pointer;transition:all 0.2s;}
.filter-clear:hover{border-color:var(--red);color:var(--red);}

.grid2{display:grid;grid-template-columns:1fr 340px;gap:16px;}
.card{background:var(--card);border:1px solid var(--border);border-radius:10px;overflow:hidden;}
.card-header{padding:16px 20px;border-bottom:1px solid var(--border);display:flex;align-items:center;justify-content:space-between;background:var(--bg2);}
.card-title{font-family:'Syne';font-size:14px;font-weight:700;}

.alert-list{max-height:580px;overflow-y:auto;}
.alert-list::-webkit-scrollbar{width:4px;}
.alert-list::-webkit-scrollbar-thumb{background:var(--border);border-radius:2px;}

.alert-item{
  padding:14px 20px;border-bottom:1px solid var(--border);
  display:grid;grid-template-columns:auto 1fr auto;gap:14px;align-items:start;
  cursor:pointer;transition:all 0.18s;
  animation:ain 0.35s ease;
}
@keyframes ain{from{opacity:0;transform:translateY(-4px)}to{opacity:1;transform:translateY(0)}}
.alert-item:hover{background:var(--bg3);box-shadow:inset 3px 0 0 var(--red);}
.alert-item:last-child{border-bottom:none;}

.sev{padding:4px 10px;border-radius:20px;font-family:'DM Mono';font-size:10px;letter-spacing:1px;white-space:nowrap;}
.sev-HIGH{background:rgba(255,64,96,0.15);color:var(--red);border:1px solid rgba(255,64,96,0.3);}
.sev-MEDIUM{background:rgba(255,140,66,0.12);color:var(--orange);border:1px solid rgba(255,140,66,0.25);}
.sev-LOW{background:rgba(255,209,102,0.10);color:var(--yellow);border:1px solid rgba(255,209,102,0.2);}

.meth{font-family:'DM Mono';font-size:10px;padding:2px 7px;border-radius:4px;margin-right:6px;}
.meth-GET{background:rgba(6,214,160,0.1);color:var(--green);border:1px solid rgba(6,214,160,0.2);}
.meth-POST{background:rgba(255,64,96,0.1);color:var(--red);border:1px solid rgba(255,64,96,0.2);}

.ai-ip{font-family:'DM Mono';font-size:13px;color:var(--text);}
.ai-path{font-family:'DM Mono';font-size:11px;color:var(--muted);margin-top:2px;}
.ai-cred{font-family:'DM Mono';font-size:11px;color:var(--red);margin-top:4px;}
.ai-agent{font-family:'DM Mono';font-size:10px;color:var(--muted);margin-top:2px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;max-width:340px;}
.ai-time{font-family:'DM Mono';font-size:10px;color:var(--muted);white-space:nowrap;}
.ai-hint{font-family:'DM Mono';font-size:9px;color:var(--muted);opacity:0.45;margin-top:4px;}

.empty{padding:60px 20px;text-align:center;color:var(--muted);font-family:'DM Mono';font-size:12px;}
.empty-icon{font-size:40px;margin-bottom:12px;opacity:0.3;}

.trap-url{font-family:'DM Mono';font-size:12px;color:var(--orange);text-decoration:none;padding:12px 20px;display:flex;align-items:center;justify-content:space-between;border-bottom:1px solid var(--border);transition:background 0.2s;cursor:pointer;}
.trap-url:hover{background:var(--bg3);}
.trap-url:last-child{border-bottom:none;}
.trap-badge{font-size:10px;padding:2px 8px;border-radius:4px;background:rgba(255,140,66,0.1);border:1px solid rgba(255,140,66,0.2);color:var(--orange);}

.ip-row{display:flex;align-items:center;padding:12px 20px;border-bottom:1px solid var(--border);font-family:'DM Mono';font-size:12px;cursor:pointer;transition:background 0.2s;}
.ip-row:hover{background:var(--bg3);}
.ip-row:last-child{border-bottom:none;}
.ip-bar-wrap{flex:1;margin:0 12px;height:4px;background:var(--border);border-radius:2px;}
.ip-bar{height:4px;background:var(--red);border-radius:2px;transition:width 0.5s;}

.btn-clear{padding:6px 14px;background:transparent;border:1px solid var(--border);color:var(--muted);border-radius:6px;font-family:'DM Mono';font-size:11px;cursor:pointer;transition:all 0.2s;}
.btn-clear:hover{border-color:var(--red);color:var(--red);}

.overlay{position:fixed;inset:0;background:rgba(0,0,0,0.8);backdrop-filter:blur(8px);z-index:1000;display:flex;align-items:center;justify-content:center;opacity:0;pointer-events:none;transition:opacity 0.25s;}
.overlay.open{opacity:1;pointer-events:all;}
.modal{background:var(--bg2);border:1px solid var(--border);border-radius:14px;width:680px;max-width:95vw;max-height:90vh;overflow-y:auto;transform:translateY(20px) scale(0.97);transition:transform 0.25s;box-shadow:0 40px 100px rgba(0,0,0,0.7);}
.overlay.open .modal{transform:none;}
.modal::-webkit-scrollbar{width:4px;}
.modal::-webkit-scrollbar-thumb{background:var(--border);border-radius:2px;}

.mh{padding:20px 24px;border-bottom:1px solid var(--border);display:flex;align-items:center;justify-content:space-between;position:sticky;top:0;background:var(--bg2);z-index:1;border-radius:14px 14px 0 0;}
.mh-title{font-family:'Syne';font-size:16px;font-weight:800;display:flex;align-items:center;gap:10px;}
.mclose{width:32px;height:32px;border-radius:8px;background:var(--bg3);border:1px solid var(--border);color:var(--muted);font-size:18px;cursor:pointer;display:flex;align-items:center;justify-content:center;transition:all 0.2s;}
.mclose:hover{border-color:var(--red);color:var(--red);}
.mbody{padding:24px;}

.msec{margin-bottom:22px;}
.msec-title{font-family:'DM Mono';font-size:10px;color:var(--muted);letter-spacing:3px;text-transform:uppercase;margin-bottom:12px;padding-bottom:8px;border-bottom:1px solid var(--border);}

.dgrid{display:grid;grid-template-columns:1fr 1fr;gap:10px;}
.ditem{background:var(--bg3);border:1px solid var(--border);border-radius:8px;padding:12px 14px;}
.ditem.full{grid-column:1/-1;}
.dlabel{font-family:'DM Mono';font-size:10px;color:var(--muted);letter-spacing:1px;text-transform:uppercase;margin-bottom:4px;}
.dval{font-family:'DM Mono';font-size:13px;color:var(--text);word-break:break-all;}
.dval.red{color:var(--red);}
.dval.green{color:var(--green);}
.dval.orange{color:var(--orange);}

.cred-box{background:rgba(255,64,96,0.07);border:1px solid rgba(255,64,96,0.25);border-radius:8px;padding:16px;display:grid;grid-template-columns:1fr 1fr;gap:12px;}
.cred-label{font-family:'DM Mono';font-size:10px;color:var(--red);opacity:0.7;letter-spacing:1px;text-transform:uppercase;margin-bottom:4px;}
.cred-val{font-family:'DM Mono';font-size:16px;color:var(--red);font-weight:500;}

.tl-bar{background:var(--bg3);border:1px solid var(--border);border-radius:8px;padding:14px 16px;display:flex;align-items:center;gap:12px;font-family:'DM Mono';font-size:12px;}
.tl-dot{width:10px;height:10px;border-radius:50%;background:var(--red);box-shadow:0 0 8px var(--red);flex-shrink:0;}

.geo-grid{display:grid;grid-template-columns:1fr 1fr;gap:10px;}
.geo-loading{font-family:'DM Mono';font-size:12px;color:var(--muted);text-align:center;padding:24px;grid-column:1/-1;}
.map-box{border-radius:8px;border:1px solid var(--border);overflow:hidden;grid-column:1/-1;height:200px;background:var(--bg3);display:flex;align-items:center;justify-content:center;font-family:'DM Mono';font-size:12px;color:var(--muted);}
</style>
</head>
<body>
<div class="topbar">
  <div class="brand">
    <div class="brand-icon">🪤</div>
    <div>
      <div class="brand-name">HoneyOps</div>
      <div class="brand-sub">Deception Security Platform</div>
    </div>
  </div>
  <div class="topbar-right">
    <span id="clock"></span>
    <button class="hp-btn off" id="hp-btn" onclick="toggleHP()">
      <span class="dot off" id="hp-dot"></span>
      <span id="hp-label">START HONEYPOT</span>
    </button>
  </div>
</div>

<div class="content">
  <div class="metrics">
    <div class="metric m-red">
      <div class="metric-label">Total Alerts</div>
      <div class="metric-value mv-red" id="m-total">0</div>
    </div>
    <div class="metric m-orange clickable" id="btn-high" onclick="filterAlerts('high')" title="Click to filter HIGH severity alerts">
      <div class="metric-label">High Severity</div>
      <div class="metric-value mv-orange" id="m-high">0</div>
      <div class="metric-hint">↑ click to filter</div>
    </div>
    <div class="metric m-yellow clickable" id="btn-creds" onclick="filterAlerts('creds')" title="Click to filter credential attempts">
      <div class="metric-label">Cred Attempts</div>
      <div class="metric-value mv-yellow" id="m-creds">0</div>
      <div class="metric-hint">↑ click to filter</div>
    </div>
    <div class="metric m-green clickable" id="btn-ips" onclick="filterAlerts('ips')" title="Click to view unique IPs">
      <div class="metric-label">Unique IPs</div>
      <div class="metric-value mv-green" id="m-ips">0</div>
      <div class="metric-hint">↑ click to filter</div>
    </div>
    <div class="metric m-purple">
      <div class="metric-label">Honeypot Port</div>
      <div class="metric-value mv-purple" style="font-size:22px;padding-top:6px">:8080</div>
    </div>
  </div>

  <div class="filter-bar" id="filter-bar">
    <span id="filter-label">🔍 Filtering alerts...</span>
    <button class="filter-clear" onclick="clearFilter()">✕ Clear Filter</button>
  </div>

  <div class="grid2">
    <div class="card">
      <div class="card-header">
        <span class="card-title">🚨 Live Alert Feed</span>
        <button class="btn-clear" onclick="clearAlerts()">Clear All</button>
      </div>
      <div class="alert-list" id="alert-list">
        <div class="empty"><div class="empty-icon">🪤</div>No alerts yet.<br>Start the honeypot and visit a trap URL.</div>
      </div>
    </div>

    <div style="display:flex;flex-direction:column;gap:16px;">
      <div class="card">
        <div class="card-header"><span class="card-title">🎯 Trap URLs — Click to visit</span></div>
        <a class="trap-url" href="http://localhost:8080/login" target="_blank">
          <span>→ /login — Admin Portal</span><span class="trap-badge">SecureCorp</span>
        </a>
        <a class="trap-url" href="http://localhost:8080/admin" target="_blank">
          <span>→ /admin — Infrastructure Panel</span><span class="trap-badge">CorpNet</span>
        </a>
        <a class="trap-url" href="http://localhost:8080/dashboard" target="_blank">
          <span>→ /dashboard — Employee SSO</span><span class="trap-badge">IntraConnect</span>
        </a>
      </div>
      <div class="card" style="flex:1;">
        <div class="card-header"><span class="card-title">📡 Top Offending IPs</span></div>
        <div id="ip-list">
          <div class="empty" style="padding:30px 20px;"><div style="font-size:24px;margin-bottom:8px;opacity:0.3">📡</div>No IPs yet.</div>
        </div>
      </div>
    </div>
  </div>
</div>

<!-- MODAL -->
<div class="overlay" id="overlay" onclick="overlayClick(event)">
  <div class="modal">
    <div class="mh">
      <div class="mh-title"><span id="m-sev-badge"></span>🔍 Alert Detail</div>
      <button class="mclose" onclick="closeModal()">✕</button>
    </div>
    <div class="mbody" id="mbody"></div>
  </div>
</div>

<script>
let hpOn = false, pollTimer = null, allAlerts = [], activeFilter = null;

// clock
setInterval(()=>{document.getElementById('clock').textContent=new Date().toISOString().replace('T',' ').slice(0,19)+' UTC';},1000);
document.getElementById('clock').textContent=new Date().toISOString().replace('T',' ').slice(0,19)+' UTC';

// honeypot toggle
async function toggleHP(){
  const btn=document.getElementById('hp-btn'),dot=document.getElementById('hp-dot'),lbl=document.getElementById('hp-label');
  if(!hpOn){
    await fetch('/api/honeypot/start',{method:'POST'});
    hpOn=true; btn.className='hp-btn on'; dot.className='dot on'; lbl.textContent='STOP HONEYPOT';
    pollTimer=setInterval(loadAlerts,2000);
  } else {
    await fetch('/api/honeypot/stop',{method:'POST'});
    hpOn=false; btn.className='hp-btn off'; dot.className='dot off'; lbl.textContent='START HONEYPOT';
    clearInterval(pollTimer);
  }
  loadAlerts();
}

// load alerts
async function loadAlerts(){
  const r=await fetch('/api/alerts'); const d=await r.json(); allAlerts=d.alerts;
  document.getElementById('m-total').textContent=allAlerts.length;
  document.getElementById('m-high').textContent=allAlerts.filter(a=>a.severity==='HIGH').length;
  document.getElementById('m-creds').textContent=allAlerts.filter(a=>a.credentials).length;
  document.getElementById('m-ips').textContent=[...new Set(allAlerts.map(a=>a.ip))].length;
  renderAlerts(); renderIPs();
}

// ── FILTER LOGIC ──
function filterAlerts(type){
  if(activeFilter===type){
    clearFilter();
    return;
  }
  activeFilter=type;
  // highlight active card
  ['btn-high','btn-creds','btn-ips'].forEach(id=>document.getElementById(id).classList.remove('active-filter'));
  const map={high:'btn-high',creds:'btn-creds',ips:'btn-ips'};
  document.getElementById(map[type]).classList.add('active-filter');
  // show filter bar
  const bar=document.getElementById('filter-bar');
  bar.classList.add('visible');
  const labels={high:'Showing HIGH severity alerts only',creds:'Showing credential capture attempts only',ips:'Showing unique IP address breakdown'};
  document.getElementById('filter-label').textContent='🔍 '+labels[type];
  renderAlerts();
}

function clearFilter(){
  activeFilter=null;
  ['btn-high','btn-creds','btn-ips'].forEach(id=>document.getElementById(id).classList.remove('active-filter'));
  document.getElementById('filter-bar').classList.remove('visible');
  renderAlerts();
}

function renderAlerts(){
  const el=document.getElementById('alert-list');

  // Special IP view
  if(activeFilter==='ips'){
    const counts={};
    allAlerts.forEach(a=>{counts[a.ip]=(counts[a.ip]||0)+1;});
    const sorted=Object.entries(counts).sort((a,b)=>b[1]-a[1]);
    const max=sorted[0]?.[1]||1;
    if(!sorted.length){
      el.innerHTML='<div class="empty"><div class="empty-icon">📡</div>No IPs captured yet.</div>';
      return;
    }
    el.innerHTML=sorted.map(([ip,c])=>`
      <div class="alert-item" onclick="filterByIP('${ip}')" style="grid-template-columns:1fr auto auto;">
        <div class="ai-ip" style="font-size:14px">${esc(ip)}</div>
        <div class="ip-bar-wrap" style="width:120px;margin:0 12px;align-self:center"><div class="ip-bar" style="width:${(c/max*100).toFixed(0)}%"></div></div>
        <div style="color:var(--red);font-family:'DM Mono';font-size:13px;white-space:nowrap">${c} alert${c>1?'s':''}</div>
      </div>`).join('');
    return;
  }

  // Standard filtered/unfiltered view
  let filtered=allAlerts;
  if(activeFilter==='high') filtered=allAlerts.filter(a=>a.severity==='HIGH');
  else if(activeFilter==='creds') filtered=allAlerts.filter(a=>a.credentials);

  if(!filtered.length){
    const msg=activeFilter?'No matching alerts for this filter.':'No alerts yet.<br>Start the honeypot and visit a trap URL.';
    el.innerHTML=`<div class="empty"><div class="empty-icon">🪤</div>${msg}</div>`;
    return;
  }
  el.innerHTML=[...filtered].reverse().map((a)=>{
    const idx=allAlerts.indexOf(a);
    const cred=a.credentials?`<div class="ai-cred">⚠ user: ${esc(a.credentials.username)} | pass: ${esc(a.credentials.password)}</div>`:'';
    const trap=a.trap?`<span style="font-family:'DM Mono';font-size:9px;color:var(--purple);margin-left:6px">[${esc(a.trap)}]</span>`:'';
    return `<div class="alert-item" onclick="openModal(${idx})">
      <div><span class="sev sev-${a.severity}">${a.severity}</span></div>
      <div>
        <div class="ai-ip"><span class="meth meth-${a.method}">${a.method}</span>${esc(a.ip)}${trap}</div>
        <div class="ai-path">${esc(a.path)}</div>
        ${cred}
        <div class="ai-agent">${esc(a.user_agent)}</div>
      </div>
      <div style="display:flex;flex-direction:column;align-items:flex-end;gap:4px">
        <div class="ai-time">${a.timestamp.slice(11,19)}</div>
        <div class="ai-hint">click for details →</div>
      </div>
    </div>`;
  }).join('');
}

function renderIPs(){
  const counts={};
  allAlerts.forEach(a=>{counts[a.ip]=(counts[a.ip]||0)+1;});
  const sorted=Object.entries(counts).sort((a,b)=>b[1]-a[1]).slice(0,8);
  const max=sorted[0]?.[1]||1;
  const el=document.getElementById('ip-list');
  if(!sorted.length){
    el.innerHTML='<div class="empty" style="padding:30px 20px;"><div style="font-size:24px;margin-bottom:8px;opacity:0.3">📡</div>No IPs yet.</div>';
    return;
  }
  el.innerHTML=sorted.map(([ip,c])=>`
    <div class="ip-row" onclick="filterByIP('${ip}')" title="Highlight alerts from ${ip}">
      <span style="color:var(--text);font-family:'DM Mono';font-size:12px">${ip}</span>
      <div class="ip-bar-wrap"><div class="ip-bar" style="width:${(c/max*100).toFixed(0)}%"></div></div>
      <span style="color:var(--red);font-family:'DM Mono';font-size:12px">${c}</span>
    </div>`).join('');
}

function esc(s){return String(s||'').replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;');}

async function openModal(idx){
  const a=allAlerts[idx]; if(!a) return;
  document.getElementById('m-sev-badge').innerHTML=`<span class="sev sev-${a.severity}">${a.severity}</span>`;
  const ts=new Date(a.timestamp);
  const credHTML=a.credentials?`
    <div class="msec">
      <div class="msec-title">⚠ Captured Credentials</div>
      <div class="cred-box">
        <div><div class="cred-label">Username Entered</div><div class="cred-val">${esc(a.credentials.username)||'(empty)'}</div></div>
        <div><div class="cred-label">Password Entered</div><div class="cred-val">${esc(a.credentials.password)||'(empty)'}</div></div>
      </div>
    </div>`:'';

  document.getElementById('mbody').innerHTML=`
    <div class="msec">
      <div class="msec-title">📋 Event Overview</div>
      <div class="tl-bar">
        <div class="tl-dot"></div>
        <span><span class="meth meth-${a.method}">${a.method}</span>Intrusion on <b style="color:var(--orange)">${esc(a.path)}</b></span>
        <span style="margin-left:auto;font-family:'DM Mono';font-size:10px;color:var(--muted)">${a.timestamp.slice(0,19).replace('T',' ')}</span>
      </div>
    </div>
    ${credHTML}
    <div class="msec">
      <div class="msec-title">🌐 Connection Details</div>
      <div class="dgrid">
        <div class="ditem"><div class="dlabel">Source IP</div><div class="dval red">${esc(a.ip)}</div></div>
        <div class="ditem"><div class="dlabel">HTTP Method</div><div class="dval orange">${a.method}</div></div>
        <div class="ditem"><div class="dlabel">Target Path</div><div class="dval">${esc(a.path)}</div></div>
        <div class="ditem"><div class="dlabel">Trap Triggered</div><div class="dval orange">${esc(a.trap||'Unknown')}</div></div>
        <div class="ditem"><div class="dlabel">UTC Timestamp</div><div class="dval">${ts.toISOString().replace('T',' ').slice(0,19)} UTC</div></div>
        <div class="ditem"><div class="dlabel">Local Time</div><div class="dval">${ts.toLocaleString()}</div></div>
        <div class="ditem full"><div class="dlabel">User-Agent</div><div class="dval">${esc(a.user_agent)}</div></div>
      </div>
    </div>
    <div class="msec">
      <div class="msec-title">📍 IP Geolocation</div>
      <div class="geo-grid" id="geo-grid"><div class="geo-loading">⏳ Looking up ${esc(a.ip)}...</div></div>
    </div>
    <div class="msec">
      <div class="msec-title">🗺 Location Map</div>
      <div class="map-box" id="map-box">Loading map...</div>
    </div>
    <div class="msec">
      <div class="msec-title">🛡 Threat Analysis</div>
      <div class="dgrid">
        <div class="ditem"><div class="dlabel">Honeypot Sprung</div><div class="dval green">✓ YES</div></div>
        <div class="ditem"><div class="dlabel">Credentials Captured</div><div class="dval ${a.credentials?'red':'green'}">${a.credentials?'✓ YES — Logged':'✗ No attempt'}</div></div>
        <div class="ditem"><div class="dlabel">Access Granted</div><div class="dval green">✗ Denied</div></div>
        <div class="ditem"><div class="dlabel">Alert ID</div><div class="dval">#${String(a.id||idx+1).padStart(4,'0')}</div></div>
      </div>
    </div>`;

  document.getElementById('overlay').classList.add('open');
  document.body.style.overflow='hidden';

  try{
    const isLocal=['127.0.0.1','::1','::ffff:127.0.0.1'].includes(a.ip);
    const gr=await fetch(`http://ip-api.com/json/${isLocal?'':a.ip}?fields=status,country,regionName,city,zip,lat,lon,timezone,isp,org,query`);
    const geo=await gr.json();
    if(isLocal||geo.status==='success'){
      const C=isLocal?'Localhost':geo.country;
      const R=isLocal?'Local Machine':geo.regionName;
      const Ci=isLocal?'Your Computer':geo.city;
      const ISP=isLocal?'Loopback':geo.isp;
      const ORG=isLocal?'—':(geo.org||'—');
      const TZ=isLocal?'—':geo.timezone;
      const lat=isLocal?null:geo.lat, lon=isLocal?null:geo.lon;
      document.getElementById('geo-grid').innerHTML=`
        <div class="ditem"><div class="dlabel">Country</div><div class="dval orange">${C}</div></div>
        <div class="ditem"><div class="dlabel">Region</div><div class="dval">${R}</div></div>
        <div class="ditem"><div class="dlabel">City</div><div class="dval">${Ci}</div></div>
        <div class="ditem"><div class="dlabel">Timezone</div><div class="dval">${TZ}</div></div>
        <div class="ditem"><div class="dlabel">ISP</div><div class="dval">${ISP}</div></div>
        <div class="ditem"><div class="dlabel">Organization</div><div class="dval">${ORG}</div></div>
        ${lat!==null?`<div class="ditem"><div class="dlabel">Latitude</div><div class="dval">${lat}</div></div>
        <div class="ditem"><div class="dlabel">Longitude</div><div class="dval">${lon}</div></div>`:''}`;
      if(lat!==null){
        document.getElementById('map-box').innerHTML=
          `<iframe src="https://www.openstreetmap.org/export/embed.html?bbox=${lon-3},${lat-3},${lon+3},${lat+3}&layer=mapnik&marker=${lat},${lon}"
            style="width:100%;height:100%;border:none;"></iframe>`;
      } else {
        document.getElementById('map-box').textContent='🖥 Localhost — no map for local connections';
      }
    } else {
      document.getElementById('geo-grid').innerHTML='<div class="geo-loading">Could not resolve location.</div>';
      document.getElementById('map-box').textContent='Map unavailable';
    }
  }catch(e){
    document.getElementById('geo-grid').innerHTML='<div class="geo-loading">Geo lookup failed.</div>';
    document.getElementById('map-box').textContent='Map unavailable';
  }
}

function closeModal(){document.getElementById('overlay').classList.remove('open');document.body.style.overflow='';}
function overlayClick(e){if(e.target===document.getElementById('overlay'))closeModal();}
document.addEventListener('keydown',e=>{if(e.key==='Escape')closeModal();});

function filterByIP(ip){
  if(activeFilter==='ips') clearFilter();
  document.querySelectorAll('.alert-item').forEach(el=>{
    el.style.opacity=el.textContent.includes(ip)?'1':'0.2';
  });
  setTimeout(()=>document.querySelectorAll('.alert-item').forEach(el=>el.style.opacity='1'),3000);
}

async function clearAlerts(){
  if(!confirm('Clear all alerts?'))return;
  await fetch('/api/alerts/clear',{method:'POST'});
  clearFilter();
  loadAlerts();
}

loadAlerts();
setInterval(loadAlerts,4000);
</script>
</body>
</html>"""

# ─────────────────────────────────────────────────────────────
#  FLASK ROUTES
# ─────────────────────────────────────────────────────────────
@app.route("/")
def dashboard():
    return render_template_string(DASHBOARD)

@app.route("/api/alerts")
def api_alerts():
    return jsonify({"alerts": load_alerts()})

@app.route("/api/alerts/clear", methods=["POST"])
def api_clear():
    with open(ALERT_LOG, "w") as f:
        json.dump([], f)
    return jsonify({"ok": True})

@app.route("/api/honeypot/start", methods=["POST"])
def api_start():
    global honeypot_running
    if not honeypot_running:
        t = threading.Thread(target=start_honeypot, daemon=True)
        t.start()
    return jsonify({"ok": True})

@app.route("/api/honeypot/stop", methods=["POST"])
def api_stop():
    stop_honeypot()
    return jsonify({"ok": True})

if __name__ == "__main__":
    print("\n  HoneyOps Dashboard")
    print("  Open http://localhost:5002\n")
    app.run(debug=False, port=5002)