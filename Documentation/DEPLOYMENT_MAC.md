# SQLInsight — Deployment on macOS

SQLInsight is designed to **clone and run** on macOS: the React dashboard is
pre-built into `frontend/dist/` and the ML model is pre-trained into
`ml/artifacts/`, both committed to the repository. The only setup step is installing
the Python dependencies — **no Node build, no model training**. This matches the
thesis's target environment (macOS 64-bit, Python 3.12).

---

## 1. Prerequisites

| Requirement | Version | Notes |
|-------------|---------|-------|
| macOS | 64-bit | Thesis target platform. |
| Python | **3.12+** | `python3 --version`. Ships with modern macOS or via [python.org](https://www.python.org/) / Homebrew. |
| git | any recent | To clone the repository. |

No Node.js / npm is needed to *run* SQLInsight (only to *rebuild* the frontend, which
is optional — see [§8](#8-optional-rebuilding-the-frontend)).

---

## 2. Clone

```bash
git clone <your-repo-url> SQLInsight
cd SQLInsight
```

---

## 3. Create a virtual environment

```bash
python3 -m venv .venv
source .venv/bin/activate
```

Your shell prompt should now show `(.venv)`. (`.venv/` is gitignored.)

---

## 4. Install dependencies

```bash
pip install -r requirements.txt
```

This installs scikit-learn (pinned to `1.8.0`), NumPy, SciPy, pandas, joblib,
Flask, `requests`, and `python-dotenv`.

> The scikit-learn pin is deliberate: the committed model artifacts were trained
> with `1.8.0`, and loading a pickle with a different scikit-learn version can fail
> or warn. Keep the pin.

---

## 5. Run

The model and frontend are already built, so just start the Flask app:

```bash
python backend/app.py
```

You should see:

```
SQLInsight v1.0.0  |  model_loaded=True  alerts=False
Dashboard: http://127.0.0.1:5000
```

Open the dashboard at **<http://127.0.0.1:5000>**.

Quick API check:

```bash
curl http://127.0.0.1:5000/api/health
# {"status":"ok","version":"1.0.0","model_loaded":true,"alerts_enabled":false}
```

> If the repository ships a convenience launcher (`./run.sh`), it simply activates
> the venv and runs `python backend/app.py`; either approach is equivalent. The
> canonical command is `python backend/app.py`.

Host and port come from `.env` (`HOST`, `PORT`; defaults `127.0.0.1:5000`). To expose
the dashboard on your LAN, set `HOST=0.0.0.0` (understand the security implications
first).

---

## 6. Generate demo traffic

With the server running, populate the dashboard with a realistic mix of benign and
malicious detections (`backend/simulate_traffic.py` posts to `POST /api/scan`):

```bash
# In a second terminal (venv activated):
python backend/simulate_traffic.py 60 0.35     # 60 requests, ~35% malicious
```

Arguments: `python backend/simulate_traffic.py [count] [malicious_ratio]` (defaults
`40` and `0.3`). Continuous stream:

```bash
python backend/simulate_traffic.py loop        # Ctrl+C to stop
```

Each request is geolocated (the generator rotates through public IPs from varied
regions) so the dashboard's attack map and country breakdown populate.

---

## 7. Run the standalone log monitor (thesis-faithful `tail -f`)

For production-style detection, run `backend/monitor.py` against a **real** web
server access log. It tails the file, extracts each request's query string,
classifies it with the same model, and on a malicious verdict records the event and
fires an email alert — the exact server-side pipeline from the thesis (Appendix B).

```bash
# Apache (typical macOS / Linux path):
python backend/monitor.py /var/log/apache2/access.log

# Nginx:
python backend/monitor.py /var/log/nginx/access.log
```

With **no argument**, it tails `ACCESS_LOG_PATH` from `.env` (default
`logs/access.log` — the demo log the API itself writes), which is handy for a
self-contained demo: run the app, run the monitor with no args, then run the demo
generator and watch detections stream in both.

```bash
python backend/monitor.py
```

### How `ACCESS_LOG_PATH` works
Defined in `config.py`:

```python
ACCESS_LOG_PATH = Path(os.getenv("ACCESS_LOG_PATH", str(LOGS_DIR / "access.log")))
```

- Set it in `.env` to point at any Apache/Nginx **combined log format** file.
- Relative paths are resolved against the project root; absolute paths are used as-is.
- The same path is where the inline API appends its log lines, so the API and the
  monitor can share one feed.

The monitor uses `tail -f` via a subprocess when available and transparently falls
back to a pure-Python tail if `tail` is missing. The monitoring process needs read
permission on the log file (Apache/Nginx logs under `/var/log/` are often
root-owned — run with appropriate permissions, or point at a copy you can read).

---

## 8. Email alerts setup (Gmail)

Alerts are **off by default**. To enable them:

### 8.1 Create the config file
```bash
cp .env.example .env
```

### 8.2 Get a Gmail App Password
Email is sent over Gmail SMTP, which requires a **16-character App Password** (not
your normal Google password; this requires 2-Step Verification to be enabled on the
account):

1. Go to **<https://myaccount.google.com/apppasswords>**.
2. Create an app password (e.g. named "SQLInsight").
3. Copy the 16-character value.

### 8.3 Edit `.env`
```ini
ALERTS_ENABLED=true
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=you@gmail.com
SMTP_PASSWORD=your_16_char_app_password
ALERT_FROM=you@gmail.com
ALERT_TO=admin@example.com
ALERT_COOLDOWN_SECONDS=60
```

Notes:
- App passwords are displayed with spaces for readability; `config.py` strips spaces
  automatically, so either form works.
- `ALERT_COOLDOWN_SECONDS` is the minimum gap between alert emails for the **same
  source IP** (anti-spam); default 60s.
- If `ALERTS_ENABLED=false` or SMTP credentials are blank, detection still works and
  events are still recorded — only the email send is skipped.

When a malicious query is detected (via either detection mode), the administrator
receives an HTML alert with the timestamp, source IP, geolocation, attack type,
confidence, status, and the raw log line.

### Optional — IP geolocation token
Geolocation works without any key (falls back to the free, token-less ip-api.com).
For higher limits / the thesis's provider, set an [ipinfo.io](https://ipinfo.io)
token in `.env`:

```ini
IPINFO_TOKEN=your_ipinfo_token
```

### Security
- **Never commit `.env`.** It is already in `.gitignore` (alongside `*.local`), so
  your credentials are not pushed to GitHub.
- If a password or App Password is ever shared in plaintext (chat, screenshot, a
  committed file), **rotate it immediately** at
  <https://myaccount.google.com/apppasswords>.
- The repository commits `.env.example` (placeholders only) as the template.

---

## 9. What gets created at runtime

These are regenerated as needed and are gitignored:

| Path | Purpose |
|------|---------|
| `runtime/sqlinsight.db` | SQLite event store (the `events` table). |
| `logs/access.log` | Apache-style log the API appends to / the monitor tails. |

To reset all recorded events, stop the app and delete `runtime/sqlinsight.db`; it is
re-created empty on next start (`database.init_db()`).

---

## 10. Troubleshooting

| Symptom | Cause | Fix |
|---------|-------|-----|
| `model_loaded=False` on startup / `/api/health` | Model artifacts missing from `ml/artifacts/`. | Run `python ml/train_model.py` to regenerate `ML_model.pkl` + `vectorizer.joblib` (see [MODEL.md](MODEL.md)). |
| `Model artifacts not found. Run python ml/train_model.py first.` | Same as above (raised by `backend/detection.py`). | Same as above. |
| `Address already in use` / port 5000 busy | Another process (often macOS AirPlay Receiver) holds port 5000. | Set `PORT=5050` in `.env`, **or** disable *System Settings → General → AirDrop & Handoff → AirPlay Receiver*. |
| Pickle load error / scikit-learn version warning | Installed scikit-learn differs from the artifacts' `1.8.0`. | Reinstall with the pin (`pip install -r requirements.txt`), or retrain with `python ml/train_model.py`. |
| `UnicodeDecodeError` reading a dataset | A dataset file has non-UTF-8 bytes. | Already handled by the loader (`encoding_errors="replace"`); ensure you use `ml/preprocess.py:load_dataset()` / `python ml/train_model.py`. |
| Dashboard shows "Frontend not built yet" page | `frontend/dist/` is absent. | It is meant to be committed. If missing, rebuild it (see below) or use the API directly. |
| Demo generator prints "is the server running?" | The Flask app is not running. | Start `python backend/app.py` first, then run `backend/simulate_traffic.py`. |
| Monitor sees no events on a real log | Wrong path, no read permission, or no query strings in requests. | Verify `ACCESS_LOG_PATH`, check file permissions, and confirm requests include `?param=...` query strings. |
| No alert emails | `ALERTS_ENABLED` false, SMTP not set, within per-IP cooldown, or using a normal password. | Set `ALERTS_ENABLED=true`, fill SMTP creds, use a Gmail **App Password**, and wait past `ALERT_COOLDOWN_SECONDS`. |

### (Optional) Rebuilding the frontend
Only needed if you change the React source. Requires Node.js + npm:

```bash
cd frontend
npm install
npm run build      # outputs to frontend/dist/
```

The build is committed so Mac users never need this to run SQLInsight.

---

## 11. Quick reference

```bash
# One-time setup
git clone <repo-url> SQLInsight && cd SQLInsight
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

# Run the dashboard + API
python backend/app.py                      # http://127.0.0.1:5000

# Demo traffic (second terminal)
python backend/simulate_traffic.py 60 0.35
python backend/simulate_traffic.py loop

# Production log monitor (thesis-faithful)
python backend/monitor.py /var/log/apache2/access.log

# Enable email alerts
cp .env.example .env   # then set ALERTS_ENABLED=true + Gmail App Password

# Retrain the model (optional; artifacts are pre-committed)
python ml/train_model.py
```
