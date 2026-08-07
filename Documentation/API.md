# SQLInsight — API Reference

SQLInsight exposes a small JSON REST API served by Flask (`backend/app.py`). All
endpoints return `application/json`. The default base URL is
`http://127.0.0.1:5000` (configurable via `HOST` / `PORT` in `.env`).

| Method | Path | Purpose |
|--------|------|---------|
| `GET` | [`/api/health`](#get-apihealth) | Service + model status |
| `GET` | [`/api/model`](#get-apimodel) | Model metadata + all metrics |
| `POST` | [`/api/scan`](#post-apiscan) | Classify a query; persist event; maybe alert |
| `GET` | [`/api/events`](#get-apievents) | Recent events |
| `GET` | [`/api/stats`](#get-apistats) | Aggregated dashboard statistics |
| `GET` | [`/` and `/<path>`](#get--and-path) | Serve the React dashboard (SPA) |

Conventions used below: `0` = benign, `1` = malicious; `confidence` is
`P(malicious)` in `[0, 1]`; timestamps are UTC ISO-8601 `YYYY-MM-DDTHH:MM:SSZ`.

---

## GET /api/health

Liveness + readiness probe.

**Request:** no parameters.

```bash
curl http://127.0.0.1:5000/api/health
```

**Response `200`:**

```json
{
  "status": "ok",
  "version": "1.0.0",
  "model_loaded": true,
  "alerts_enabled": false
}
```

| Field | Type | Description |
|-------|------|-------------|
| `status` | string | Always `"ok"` when the service is up. |
| `version` | string | App version (`config.VERSION`). |
| `model_loaded` | boolean | `true` if `ML_model.pkl` + `vectorizer.joblib` loaded. |
| `alerts_enabled` | boolean | Mirrors `ALERTS_ENABLED` from config. |

> If `model_loaded` is `false`, run `python ml/train_model.py` (see [MODEL.md](MODEL.md)).

---

## GET /api/model

Returns the full contents of `ml/artifacts/metrics.json` — model metadata and all
experiment metrics. Used by the dashboard's model panel.

**Request:** no parameters.

```bash
curl http://127.0.0.1:5000/api/model
```

**Response `200`** (abridged — see [`metrics.json`](../ml/artifacts/metrics.json) for
the full document):

```json
{
  "generated_at": "2026-05-25T06:26:08Z",
  "sklearn_version": "1.8.0",
  "model": "LogisticRegression",
  "model_params": { "C": 4.0, "solver": "liblinear", "max_iter": 1000, "class_weight": "balanced" },
  "features": {
    "n_features": 80650,
    "vectorizer": "FeatureUnion(word 1-2 gram + char_wb 3-5 gram) -> VarianceThreshold"
  },
  "datasets": {
    "train": { "file": "Modified_SQL_Dataset.csv", "rows": 30918 },
    "eval":  { "file": "clean_sql_dataset.csv", "rows": 148324 },
    "overlap_note": "train is ~entirely contained in eval; unseen-only excludes it"
  },
  "experiment_1":        { "accuracy": 99.71, "precision": 99.96, "recall": 99.25, "f1": 99.6,
                           "confusion_matrix": { "tn": 3907, "fp": 1, "fn": 17, "tp": 2259 },
                           "samples": 6184, "train_size": 24734, "test_size": 6184 },
  "experiment_2_full":   { "accuracy": 92.36, "precision": 98.74, "recall": 86.52, "f1": 92.23,
                           "confusion_matrix": { "tn": 69716, "fp": 859, "fn": 10480, "tp": 67269 },
                           "samples": 148324 },
  "experiment_2_unseen": { "accuracy": 90.35, "precision": 98.49, "recall": 84.23, "f1": 90.8,
                           "confusion_matrix": { "tn": 50138, "fp": 859, "fn": 10461, "tp": 55888 },
                           "samples": 117346 },
  "headline": { "accuracy": 99.71, "precision": 99.96, "recall": 99.25, "f1": 99.6 }
}
```

**Response `404`** (artifacts not yet generated):

```json
{ "error": "metrics not found; run ml/train_model.py" }
```

---

## POST /api/scan

Classify a single query string. This is the inline detection path (Mode A): it runs
the model, geolocates the source IP, **appends an Apache-style line to the access
log** (so the standalone monitor has a feed), persists an event row, fires an email
alert if the verdict is malicious (and alerts are configured), and returns the full
event.

**Request body** (`application/json`):

| Field | Type | Required | Default | Description |
|-------|------|----------|---------|-------------|
| `query` | string | **yes** | — | The query string / payload to classify. |
| `source_ip` | string | no | request remote addr, else `127.0.0.1` | Client IP (used for geolocation + alerts). |
| `source` | string | no | `"scanner"` | Free-text origin tag stored on the event. |
| `method` | string | no | `"GET"` | HTTP method (upper-cased). |
| `user_agent` | string | no | request `User-Agent`, else `"SQLInsight-Client"` | Client User-Agent. |
| `path` | string | no | `"/search"` | Request path. |

**Example — malicious:**

```bash
curl -X POST http://127.0.0.1:5000/api/scan \
  -H "Content-Type: application/json" \
  -d '{"query": "admin'\'' OR '\''1'\''='\''1'\'' --", "source_ip": "45.83.91.10"}'
```

**Response `200`:**

```json
{
  "id": 42,
  "query": "admin' OR '1'='1' --",
  "prediction": 1,
  "confidence": 0.9987,
  "verdict": "Suspicious",
  "attack_type": "Tautology / Auth Bypass",
  "source_ip": "45.83.91.10",
  "method": "GET",
  "path": "/search",
  "user_agent": "SQLInsight-Client",
  "source": "scanner",
  "log_line": "45.83.91.10 - - [25/May/2026:06:30:00 +0000] \"GET /search?q=admin%27%20OR%20%271%27%3D%271%27%20-- HTTP/1.1\" 200 512 \"-\" \"SQLInsight-Client\"",
  "country": "NL",
  "region": "North Holland",
  "city": "Amsterdam",
  "lat": 52.374,
  "lon": 4.8897,
  "alerted": 1
}
```

**Example — benign:**

```bash
curl -X POST http://127.0.0.1:5000/api/scan \
  -H "Content-Type: application/json" \
  -d '{"query": "blue running shoes"}'
```

```json
{
  "id": 43,
  "query": "blue running shoes",
  "prediction": 0,
  "confidence": 0.0123,
  "verdict": "Normal",
  "attack_type": null,
  "source_ip": "127.0.0.1",
  "method": "GET",
  "path": "/search",
  "user_agent": "curl/8.4.0",
  "source": "scanner",
  "log_line": "127.0.0.1 - - [25/May/2026:06:31:00 +0000] \"GET /search?q=blue%20running%20shoes HTTP/1.1\" 200 512 \"-\" \"curl/8.4.0\"",
  "country": "Local",
  "region": "Private",
  "city": "localhost",
  "lat": null,
  "lon": null,
  "alerted": 0
}
```

**Response fields** (this is also the shape stored in the SQLite `events` table and
returned by `/api/events`):

| Field | Type | Description |
|-------|------|-------------|
| `id` | integer | New event id (SQLite autoincrement). |
| `query` | string | The classified query. |
| `prediction` | `0` \| `1` | `1` = malicious, `0` = benign (from the model). |
| `confidence` | number | `P(malicious)`, rounded to 4 decimals. |
| `verdict` | string | `"Suspicious"` or `"Normal"`. |
| `attack_type` | string \| null | Descriptive category (e.g. `"Union-based"`); `null` when benign. |
| `source_ip` | string | Resolved client IP. |
| `method` | string | HTTP method. |
| `path` | string | Request path. |
| `user_agent` | string | Client User-Agent. |
| `source` | string | Origin tag. |
| `log_line` | string | The Apache combined-log line written for this request. |
| `country`, `region`, `city` | string \| null | Geolocation (loopback/private ⇒ `Local`/`Private`/`localhost`). |
| `lat`, `lon` | number \| null | Coordinates (null for private IPs / lookup failure). |
| `alerted` | `0` \| `1` | `1` if an email alert was actually sent for this event. |

**Error `400`** (missing/empty `query`):

```json
{ "error": "missing 'query'" }
```

> **Attack-type categories** (`backend/detection.py:classify_attack_type`):
> Tautology / Auth Bypass, Union-based, Stacked Queries, Time-based Blind,
> Error-based, Command Execution, Comment Injection, Schema Enumeration, and
> `Generic / Obfuscated` (fallback). These are descriptive only — the
> malicious/benign verdict always comes from the ML model.

---

## GET /api/events

Returns recent events, most-recent first.

**Query parameters:**

| Param | Type | Default | Description |
|-------|------|---------|-------------|
| `limit` | integer | `50` | Max rows to return. Capped server-side at **500**. |
| `verdict` | string | — | Filter by verdict: `Suspicious` or `Normal`. Other values are ignored (no filter). |

```bash
curl "http://127.0.0.1:5000/api/events?limit=5&verdict=Suspicious"
```

**Response `200`:**

```json
{
  "events": [
    {
      "id": 42,
      "ts": "2026-05-25T06:30:00Z",
      "query": "admin' OR '1'='1' --",
      "prediction": 1,
      "confidence": 0.9987,
      "verdict": "Suspicious",
      "attack_type": "Tautology / Auth Bypass",
      "source_ip": "45.83.91.10",
      "method": "GET",
      "path": "/search",
      "user_agent": "sqlmap/1.7",
      "country": "NL",
      "region": "North Holland",
      "city": "Amsterdam",
      "lat": 52.374,
      "lon": 4.8897,
      "source": "demo",
      "alerted": 1
    }
  ]
}
```

Each element is a full `events` row (see the schema in [ARCHITECTURE.md](ARCHITECTURE.md#4-sqlite-events-schema)).
Note that `/api/events` rows include `ts` (the stored timestamp) for every event.

---

## GET /api/stats

Aggregated statistics for the dashboard, computed from the `events` table, with the
model headline metrics folded in.

**Request:** no parameters.

```bash
curl http://127.0.0.1:5000/api/stats
```

**Response `200`:**

```json
{
  "totals": {
    "requests": 120,
    "attacks": 38,
    "normal": 82,
    "alerts": 12,
    "attack_rate": 31.7
  },
  "last_24h": { "attacks": 38 },
  "timeseries": [
    { "bucket": "2026-05-24T07:00Z", "hour": "07:00", "attacks": 0, "normal": 0 },
    { "bucket": "2026-05-25T06:00Z", "hour": "06:00", "attacks": 5, "normal": 11 }
  ],
  "by_type": [
    { "type": "Union-based", "count": 14 },
    { "type": "Tautology / Auth Bypass", "count": 9 }
  ],
  "by_country": [
    { "country": "NL", "count": 12 },
    { "country": "RU", "count": 7 }
  ],
  "top_ips": [
    { "ip": "45.83.91.10", "count": 8, "country": "NL" }
  ],
  "model": {
    "accuracy": 99.71,
    "precision": 99.96,
    "recall": 99.25,
    "f1": 99.6,
    "generalisation": {
      "accuracy": 90.35,
      "precision": 98.49,
      "recall": 84.23,
      "f1": 90.8,
      "confusion_matrix": { "tn": 50138, "fp": 859, "fn": 10461, "tp": 55888 },
      "samples": 117346
    }
  }
}
```

| Field | Type | Description |
|-------|------|-------------|
| `totals.requests` | integer | All events recorded. |
| `totals.attacks` | integer | Events with `prediction = 1`. |
| `totals.normal` | integer | `requests − attacks`. |
| `totals.alerts` | integer | Events with `alerted = 1`. |
| `totals.attack_rate` | number | `attacks / requests × 100`, 1 decimal (0.0 if none). |
| `last_24h.attacks` | integer | Attacks in the last 24h. |
| `timeseries` | array | 24 hourly buckets (oldest→newest): `{bucket, hour, attacks, normal}`. |
| `by_type` | array | Attack counts grouped by `attack_type`, descending. |
| `by_country` | array | Attack counts by country (top 10), descending. |
| `top_ips` | array | Top 8 attacking IPs: `{ip, count, country}`. |
| `model` | object | `headline` metrics (Experiment 1) + `generalisation` (Experiment 2 unseen-only). Present only if `metrics.json` exists. |

---

## GET / and /\<path\>

Serves the pre-built React single-page app from `frontend/dist/`.

- `GET /` → `frontend/dist/index.html`.
- `GET /<path>` → the matching static asset if it exists, otherwise
  `index.html` (client-side routing fallback).
- Any path beginning with `api/` that is not a defined endpoint returns
  `404 {"error": "not found"}`.
- If `frontend/dist/` does not exist, a small HTML page is returned explaining how
  to build the frontend (`cd frontend && npm install && npm run build`) or to use the
  API directly.
