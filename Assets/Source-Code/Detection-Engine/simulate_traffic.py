"""Demo traffic generator.

Sends a realistic mix of benign and malicious requests to the running API so the
dashboard populates with live detections, attack types and geographic spread.

Usage:
    python backend/simulate_traffic.py            # ~40 mixed requests
    python backend/simulate_traffic.py 200 0.35   # 200 requests, 35% malicious
    python backend/simulate_traffic.py loop        # continuous stream
"""
from __future__ import annotations

import random
import sys
import time

import requests

API = "http://127.0.0.1:5000/api/scan"

BENIGN = [
    "john_doe_2024", "iphone 15 pro max", "best pizza near me", "blue running shoes",
    "how to learn python", "weather tomorrow", "[email protected]", "order status 48213",
    "wireless headphones", "gardening tips for spring", "annual report 2025", "reset my password",
    "4-bedroom house muscat", "flight to dubai", "samsung galaxy s24", "coffee machine reviews",
]
MALICIOUS = [
    "admin' OR '1'='1", "admin' OR '1'='1' --", "' OR 1=1--", "1' UNION SELECT NULL,NULL--",
    "UNION SELECT username,password FROM users--", "'; DROP TABLE users; --",
    "1' AND SLEEP(5)--", "'; EXEC xp_cmdshell('whoami')--", "1' ORDER BY 10--",
    "' OR pg_sleep(10)--", "1 AND extractvalue(1,concat(0x7e,version()))",
    "' UNION SELECT table_name FROM information_schema.tables--", "1); DROP TABLE members;--",
    "' OR 'x'='x", "1 AND 1=utl_inaddr.get_host_address((SELECT user FROM dual))",
]
# Public IPs from varied regions for geographic spread on the dashboard.
IPS = [
    "45.83.91.10", "103.21.244.2", "185.220.101.5", "200.55.12.7", "5.39.10.20",
    "41.86.42.9", "1.32.244.1", "212.95.50.8", "190.2.130.4", "77.88.55.66",
    "8.8.8.8", "203.0.113.45", "151.101.1.69", "92.63.197.10", "176.65.4.22",
]
UAS = ["sqlmap/1.7", "Mozilla/5.0 (Windows NT 10.0)", "curl/8.4.0",
       "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15)", "python-requests/2.31"]


def send(query: str, malicious_hint: bool) -> None:
    try:
        r = requests.post(API, json={
            "query": query,
            "source_ip": random.choice(IPS),
            "user_agent": random.choice(UAS),
            "source": "demo",
        }, timeout=5)
        d = r.json()
        flag = "ATTACK " if d.get("prediction") == 1 else "ok     "
        print(f"  {flag} {d.get('confidence',0):5.1%} {d.get('attack_type') or '':22s} | {query[:48]}")
    except requests.RequestException as e:
        print(f"  ! request failed (is the server running?): {e}")
        sys.exit(1)


def one_round(p_malicious: float) -> None:
    if random.random() < p_malicious:
        send(random.choice(MALICIOUS), True)
    else:
        send(random.choice(BENIGN), False)


def main() -> None:
    args = sys.argv[1:]
    if args and args[0] == "loop":
        print("Streaming demo traffic (Ctrl+C to stop)...")
        try:
            while True:
                one_round(0.3)
                time.sleep(random.uniform(0.4, 1.6))
        except KeyboardInterrupt:
            print("\nStopped.")
        return
    n = int(args[0]) if args else 40
    p = float(args[1]) if len(args) > 1 else 0.3
    print(f"Sending {n} requests (~{p:.0%} malicious) to {API} ...")
    for _ in range(n):
        one_round(p)
        time.sleep(0.05)
    print("Done.")


if __name__ == "__main__":
    main()
