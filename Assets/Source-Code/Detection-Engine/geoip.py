"""IP geolocation for alert enrichment + the dashboard attack map.

Uses ipinfo.io when IPINFO_TOKEN is set (matching the thesis server code),
otherwise falls back to the free, token-less ip-api.com. Results are cached in
memory. Private/loopback addresses are resolved locally without a network call.
"""
from __future__ import annotations

import ipaddress
import sys
from functools import lru_cache
from pathlib import Path

import requests

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from config import IPINFO_TOKEN  # noqa: E402

_EMPTY = {"country": None, "region": None, "city": None, "lat": None, "lon": None}


def _is_private(ip: str) -> bool:
    try:
        return ipaddress.ip_address(ip).is_private or ipaddress.ip_address(ip).is_loopback
    except ValueError:
        return True


@lru_cache(maxsize=4096)
def geolocate(ip: str | None) -> dict:
    if not ip:
        return dict(_EMPTY)
    if _is_private(ip):
        return {"country": "Local", "region": "Private", "city": "localhost", "lat": None, "lon": None}
    try:
        if IPINFO_TOKEN:
            r = requests.get(f"https://ipinfo.io/{ip}/json", params={"token": IPINFO_TOKEN}, timeout=4)
            if r.status_code == 200:
                d = r.json()
                loc = (d.get("loc") or ",").split(",")
                return {
                    "country": d.get("country"),
                    "region": d.get("region"),
                    "city": d.get("city"),
                    "lat": float(loc[0]) if loc[0] else None,
                    "lon": float(loc[1]) if len(loc) > 1 and loc[1] else None,
                }
        # Token-less fallback.
        r = requests.get(
            f"http://ip-api.com/json/{ip}",
            params={"fields": "status,country,countryCode,regionName,city,lat,lon"},
            timeout=4,
        )
        if r.status_code == 200 and r.json().get("status") == "success":
            d = r.json()
            return {
                "country": d.get("countryCode") or d.get("country"),
                "region": d.get("regionName"),
                "city": d.get("city"),
                "lat": d.get("lat"),
                "lon": d.get("lon"),
            }
    except requests.RequestException:
        pass
    return dict(_EMPTY)
