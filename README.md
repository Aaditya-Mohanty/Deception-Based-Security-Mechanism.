# HoneyOps — Real-Time Honeypot Deception Platform  

## Overview  
HoneyOps is a real-time honeypot system designed to detect and analyze malicious activity by deploying highly realistic fake enterprise login portals.  

The platform follows a deception-first security approach. Instead of blocking attackers, it traps, monitors, and analyzes them in real time. Any interaction with the system is treated as suspicious, resulting in highly reliable detection with near-zero false positives. 

-----

## Features  
- Deployment of three realistic fake enterprise portals (`/login`, `/admin`, `/dashboard`)  
- Real-time attack detection and alert generation  
- Credential capture for threat analysis  
- IP tracking with geolocation mapping  
- Live monitoring dashboard with alert streaming  
- Severity-based classification (MEDIUM / HIGH)  
- Persistent JSON-based alert storage  
- Interactive filtering and visualization of threats  

-----

## How It Works  

### Core Concept  
The system hosts fake login and administrative portals that mimic real enterprise systems.  

Since no legitimate user should access these portals:  
- Any visit is treated as suspicious activity  
- Any credential submission is considered a confirmed attack attempt  

-----

### Detection Logic  

#### 1. Reconnaissance Detection (MEDIUM Severity)  
- Every GET request to fake endpoints is logged  
- Indicates scanning or probing activity  

#### 2. Attack Detection (HIGH Severity)  
- Any credential submission is captured  
- Logged as an active intrusion attempt  

-----

### Logged Data  
Each interaction records:  
- Timestamp  
- Source IP address  
- User-Agent  
- Endpoint accessed (trap triggered)  
- Submitted credentials (if any)  
- Severity level  

------

### Real-Time Monitoring  
- Alerts are streamed live to the dashboard  
- Operators can monitor attacker activity instantly  
- No delay between detection and visibility  

---

## Dashboard Features  
- Live alert feed with real-time updates  
- Severity-based filtering (MEDIUM / HIGH)  
- Credential capture display  
- IP geolocation with interactive map  
- Top attacking IPs ranked by activity  
- Clickable metrics for quick filtering  

---

## Key Insight  
Traditional security systems often struggle with false positives.  

A honeypot eliminates this issue:  
- No legitimate traffic is expected  
- Every interaction is suspicious  
- No tuning is required  

This results in high-confidence threat detection with minimal noise.  

---

## Tech Stack  
- Python + Flask — Dashboard API  
- Python `http.server` — Honeypot listener (Port 8080)  
- Threading — Dual server execution  
- Vanilla JavaScript — Frontend dashboard  
- JSON — Persistent alert storage  
- ip-api.com + OpenStreetMap — IP geolocation and mapping  

---

## Notes  
- The system automatically starts logging interactions once deployed  
- No manual setup is required for log generation  
- Alerts are created dynamically whenever an attacker interacts with the honeypot  

---

## Conclusion  
HoneyOps demonstrates how deception can be used as an effective cybersecurity strategy. By actively exposing attacker behavior rather than only defending systems, it provides valuable insights into real-world threats and attack patterns.  
