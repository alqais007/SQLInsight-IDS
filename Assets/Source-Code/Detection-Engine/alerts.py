"""Email alerting for SQLInsight (Gmail SMTP).

Sends an HTML security alert when a malicious query is detected, including the
timestamp, source IP, geolocation, verdict and raw log line -- the same fields
described in the thesis alert system. A per-IP cooldown prevents alert storms.
"""
from __future__ import annotations

import smtplib
import sys
import time
from email.message import EmailMessage
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from config import (  # noqa: E402
    ALERT_COOLDOWN_SECONDS,
    ALERT_FROM,
    ALERT_TO,
    ALERTS_ENABLED,
    SMTP_HOST,
    SMTP_PASSWORD,
    SMTP_PORT,
    SMTP_USER,
)

_last_sent: dict[str, float] = {}


def _cooling_down(ip: str | None) -> bool:
    key = ip or "_"
    now = time.time()
    if now - _last_sent.get(key, 0) < ALERT_COOLDOWN_SECONDS:
        return True
    _last_sent[key] = now
    return False


def _html_body(event: dict) -> str:
    geo = ", ".join(
        x for x in [event.get("city"), event.get("region"), event.get("country")] if x
    ) or "Unknown"
    return f"""\
<div style="font-family:Arial,sans-serif;max-width:600px;border:1px solid #eee;border-radius:10px;overflow:hidden">
  <div style="background:#7c3aed;color:#fff;padding:16px 20px">
    <h2 style="margin:0">&#9888; SQLInsight Security Alert</h2>
    <p style="margin:4px 0 0;opacity:.9">SQL Injection attempt detected</p>
  </div>
  <table style="width:100%;border-collapse:collapse;font-size:14px">
    <tr><td style="padding:10px 20px;color:#666">Date / Time (UTC)</td><td style="padding:10px 20px"><b>{event.get('ts','')}</b></td></tr>
    <tr style="background:#fafafa"><td style="padding:10px 20px;color:#666">Source IP</td><td style="padding:10px 20px"><b>{event.get('source_ip','?')}</b></td></tr>
    <tr><td style="padding:10px 20px;color:#666">Location</td><td style="padding:10px 20px">{geo}</td></tr>
    <tr style="background:#fafafa"><td style="padding:10px 20px;color:#666">Attack Type</td><td style="padding:10px 20px">{event.get('attack_type') or 'Unknown'}</td></tr>
    <tr><td style="padding:10px 20px;color:#666">Confidence</td><td style="padding:10px 20px">{round(float(event.get('confidence',0))*100,1)}%</td></tr>
    <tr style="background:#fafafa"><td style="padding:10px 20px;color:#666">Status</td><td style="padding:10px 20px"><b style="color:#dc2626">SUSPICIOUS</b></td></tr>
    <tr><td style="padding:10px 20px;color:#666;vertical-align:top">Payload / Log</td>
        <td style="padding:10px 20px"><code style="word-break:break-all">{(event.get('log_line') or event.get('query',''))[:500]}</code></td></tr>
  </table>
  <div style="padding:12px 20px;background:#f3f4f6;color:#888;font-size:12px">Sent automatically by SQLInsight IDS.</div>
</div>"""


def send_alert(event: dict) -> bool:
    """Send an alert email. Returns True if a message was actually sent."""
    if not ALERTS_ENABLED:
        return False
    if not (SMTP_USER and SMTP_PASSWORD and ALERT_TO):
        print("[alerts] SMTP not configured; skipping email.")
        return False
    if _cooling_down(event.get("source_ip")):
        return False

    message = EmailMessage()
    message["From"] = ALERT_FROM
    message["To"] = ALERT_TO
    message["Subject"] = "Security Alert: SQL Injection Attempt Detected"
    message.set_content(
        f"SQL Injection detected from {event.get('source_ip','?')} at {event.get('ts','')}.\n"
        f"Attack type: {event.get('attack_type') or 'Unknown'}\n"
        f"Payload: {(event.get('query') or '')[:500]}"
    )
    message.add_alternative(_html_body(event), subtype="html")

    try:
        with smtplib.SMTP(SMTP_HOST, SMTP_PORT, timeout=15) as server:
            server.starttls()
            server.login(SMTP_USER, SMTP_PASSWORD)
            server.send_message(message)
        print(f"[alerts] Alert email sent to {ALERT_TO}.")
        return True
    except Exception as e:  # noqa: BLE001 - alerting must never crash detection
        print(f"[alerts] Error sending email: {e}")
        return False
