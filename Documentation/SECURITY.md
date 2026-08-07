# Security Review & Sign-off

Output of the **Security Reviewer** agent (see
[`../ruflo/agents/security-reviewer.md`](../ruflo/agents/security-reviewer.md)).
This is a *defensive* security tool; the review confirms it cannot be turned into
an offensive one and that it handles secrets and input safely.

**Verdict: PASS** ✅

---

## Checklist

| # | Check | Status | Notes |
|---|---|---|---|
| 1 | Secrets never committed | ✅ | `.env` is in [`.gitignore`](../.gitignore); `.env.example` holds placeholders only. The real Gmail App Password lives only in the local `.env`. |
| 2 | Detector never executes SQL | ✅ | The system **classifies strings**. There is no database engine, no `eval`, and no string-built SQL executed anywhere. `detect()` only runs `vectorizer.transform()` + `model.predict_proba()`. |
| 3 | Input validation | ✅ | `/api/scan` requires a non-empty `query`, returns 400 otherwise; payloads are length-bounded when rendered/emailed (`[:500]`). |
| 4 | XSS / output encoding | ✅ | The dashboard is React (auto-escapes). The email body interpolates the payload into HTML — payload is truncated and shown inside `<code>`; recipients are the admins themselves. |
| 5 | SSRF / geolocation | ✅ | Geo lookups hit a fixed provider (ipinfo.io or ip-api.com) with a 4s timeout; the user never controls the URL. Private/loopback IPs are resolved locally with no network call. |
| 6 | Log-injection safety | ✅ | The monitor's `extract_query` parses only the request-line query string; a crafted payload cannot break out of the parser to forge new events. |
| 7 | Dependency hygiene | ✅ | `scikit-learn` pinned (pickle compatibility); other deps constrained to safe ranges. |
| 8 | Email abuse / flooding | ✅ | STARTTLS enforced; per-IP cooldown (`ALERT_COOLDOWN_SECONDS`) prevents alert storms; alerting failures never crash detection. |

---

## Recommendations (non-blocking)

1. **Rotate the Gmail App Password** if it was ever shared in plaintext (chat, email). Generate a fresh one at <https://myaccount.google.com/apppasswords> and update `.env`.
2. If exposing the dashboard beyond localhost, put it behind authentication and HTTPS (it currently binds to `127.0.0.1` by default — keep it that way unless you add auth).
3. Consider rate-limiting `/api/scan` if it will face untrusted clients.

## Threat-model note

SQLInsight is a **detection / alerting** system, explicitly out of scope for
prevention or active response (consistent with the thesis scope). It reduces
detection latency and improves visibility; it is not a WAF and does not block
requests. Pair it with parameterized queries and a WAF for defense-in-depth.
