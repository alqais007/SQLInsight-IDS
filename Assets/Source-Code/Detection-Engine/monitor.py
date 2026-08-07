"""Standalone real-time log monitor (thesis-faithful, Appendix B).

Tails an Apache/Nginx access log with ``tail -f``, extracts the query string
from each request, classifies it with the trained model, and on a malicious
verdict records the event and fires an email alert -- the exact pipeline from
the thesis server-side deployment, generalised to also feed the dashboard DB.

Usage:
    python backend/monitor.py                 # tails ACCESS_LOG_PATH from .env
    python backend/monitor.py /var/log/apache2/access.log
"""
from __future__ import annotations

import subprocess
import sys
import time
from pathlib import Path

_BACKEND_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(_BACKEND_DIR))
sys.path.insert(0, str(_BACKEND_DIR.parent))

import accesslog  # noqa: E402
import alerts  # noqa: E402
import database  # noqa: E402
import detection  # noqa: E402
import geoip  # noqa: E402
from config import ACCESS_LOG_PATH  # noqa: E402


def predict_log_entry(log_line: str) -> str:
    query = accesslog.extract_query(log_line)
    if not query:
        return "Normal"
    result = detection.detect(query)
    if result["prediction"] != 1:
        return "Normal"

    ip = accesslog.extract_ip(log_line)
    geo = geoip.geolocate(ip)
    event = {
        **result,
        "source_ip": ip,
        "method": "GET",
        "path": log_line.split('"')[1].split(" ")[1].split("?")[0] if '"' in log_line else "/",
        "user_agent": accesslog.extract_user_agent(log_line),
        "source": "monitor",
        "log_line": log_line.strip(),
        **geo,
        "alerted": 0,
    }
    if alerts.send_alert(event):
        event["alerted"] = 1
    database.insert_event(event)
    return "Suspicious"


def _follow_with_tail(path: Path):
    proc = subprocess.Popen(
        ["tail", "-f", "-n", "0", str(path)],
        stdout=subprocess.PIPE, text=True, bufsize=1,
    )
    assert proc.stdout is not None
    for line in proc.stdout:
        yield line


def _follow_pure_python(path: Path):
    """Fallback follower when `tail` is unavailable (e.g. Windows)."""
    with open(path, "r", encoding="utf-8", errors="replace") as f:
        f.seek(0, 2)
        while True:
            line = f.readline()
            if not line:
                time.sleep(0.3)
                continue
            yield line


def main() -> None:
    path = Path(sys.argv[1]) if len(sys.argv) > 1 else ACCESS_LOG_PATH
    path.parent.mkdir(parents=True, exist_ok=True)
    path.touch(exist_ok=True)
    database.init_db()

    if not detection.model_loaded():
        print("Model artifacts missing. Run `python ml/train_model.py` first.")
        sys.exit(1)

    print(f"Monitoring started on {path} ...")
    try:
        follower = _follow_with_tail(path)
        try:
            first = next(follower)
        except (FileNotFoundError, OSError):
            follower = _follow_pure_python(path)
            first = None
    except FileNotFoundError:
        follower = _follow_pure_python(path)
        first = None

    try:
        if first is not None:
            _handle(first)
        for line in follower:
            _handle(line)
    except KeyboardInterrupt:
        print("\nMonitoring stopped.")


def _handle(line: str) -> None:
    if not line.strip():
        return
    result = predict_log_entry(line)
    flag = "[ALERT]" if result == "Suspicious" else "       "
    print(f"{flag} {result:10s} | {line.strip()[:120]}")


if __name__ == "__main__":
    main()
