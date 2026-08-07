"""Apache-style access logging + log parsing.

The live API appends a combined-log line for every request so the standalone
monitor (backend/monitor.py) has a realistic feed to tail -- exactly the setup
described in the thesis (Apache access.log + ``tail -f``). The ``extract_query``
regex is faithful to the thesis server-side code (Appendix B).
"""
from __future__ import annotations

import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import unquote

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from config import ACCESS_LOG_PATH  # noqa: E402

_IP_RE = re.compile(r"^(\d{1,3}(?:\.\d{1,3}){3})")
# Thesis-faithful: capture the request target between method and HTTP version.
_REQ_RE = re.compile(r'"(GET|POST|PUT|DELETE|HEAD)\s(\S+)\sHTTP')


def write_access_log(ip: str, method: str, path: str, status: int = 200,
                     size: int = 512, user_agent: str = "-", referer: str = "-") -> str:
    ts = datetime.now(timezone.utc).strftime("%d/%b/%Y:%H:%M:%S +0000")
    line = f'{ip} - - [{ts}] "{method} {path} HTTP/1.1" {status} {size} "{referer}" "{user_agent}"\n'
    try:
        ACCESS_LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
        with open(ACCESS_LOG_PATH, "a", encoding="utf-8") as f:
            f.write(line)
    except OSError as e:
        print(f"[accesslog] could not write log: {e}")
    return line


def extract_ip(log_line: str) -> str | None:
    m = _IP_RE.search(log_line)
    return m.group(1) if m else None


def extract_query(log_line: str) -> str:
    """Extract the query string value from an access-log line.

    Returns the decoded value after the first '=' of the query string, e.g.
    `GET /search?q=<payload> HTTP/1.1` -> `<payload>`. Faithful to the thesis.
    """
    m = _REQ_RE.search(log_line)
    if not m:
        return ""
    target = m.group(2)
    if "?" not in target:
        return ""
    qs = target.split("?", 1)[1]
    # Take the value of the first parameter (e.g. q=...).
    first = qs.split("&", 1)[0]
    value = first.split("=", 1)[1] if "=" in first else first
    return unquote(value.replace("+", " "))


def extract_user_agent(log_line: str) -> str | None:
    parts = log_line.split('"')
    return parts[-2] if len(parts) >= 6 else None
