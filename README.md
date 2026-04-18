🔴 HoneyOps — a real-time honeypot deception platform

The system deploys three fully designed fake enterprise login portals — each styled as a different fictional company — on a dedicated HTTP server. They look exactly like real admin interfaces. But they're completely fake.
The rule is simple: no legitimate user should ever visit these pages. So anyone who does? Immediately flagged.


🛠 What the system does:
→ Serves 3 convincing fake portals (/login, /admin, /dashboard)
→ Captures every GET request as a MEDIUM severity alert (reconnaissance)
→ Captures every credential submission as a HIGH severity alert (active attack)
→ Logs source IP, user-agent, timestamp, trap triggered, and any submitted passwords
→ Streams all alerts to a live operator dashboard in real time
→ Runs IP geolocation + map on every attacker IP
→ Classifies, filters, and visualises threats by severity

💡 The key insight behind honeypots:
Traditional IDS systems fight false positives. A honeypot has a theoretical false positive rate of ZERO — because nothing legitimate should ever touch it. Every alert is real. Every interaction is suspicious. No tuning required.


🧱 Built with:
• Python + Flask (dashboard API)
• Python http.server (honeypot listener, port 8080)
• Threading — two servers, one process
• Vanilla JS single-page dashboard (no frameworks)
• JSON persistent alert store
• ip-api.com geolocation + OpenStreetMap

📊 The dashboard includes:

✅ Live alert feed with real-time polling

✅ Severity classification (MEDIUM / HIGH

✅ Credential capture display

✅ One-click IP geolocation modal + interactive map

✅ Clickable metric cards for instant alert filtering

✅ Top offending IPs ranked by activity

This project taught me that the best security traps don't look like traps at all.
