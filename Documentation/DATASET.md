# SQLInsight — Datasets

SQLInsight uses two labelled SQL-query datasets, both in the same simple
`{Query, Label}` CSV format. They drive the two experiments described in
[MODEL.md](MODEL.md):

| Role | File | Rows (loaded) | Used for |
|------|------|--------------:|----------|
| **Training / Experiment 1** | `data/Modified_SQL_Dataset.csv` | 30,918 | Fit the model; 80/20 within-distribution evaluation |
| **Generalisation / Experiment 2** | `data/clean_sql_dataset.csv` | 148,324 | Cross-dataset evaluation (full + unseen-only) |

Row counts are the values recorded in
[`ml/artifacts/metrics.json`](../ml/artifacts/metrics.json) *after* cleaning
(`ml/preprocess.py:load_dataset()` drops empty/un-parseable rows). The thesis cites
the raw clean dataset as **148,326** samples (70,576 benign / 77,750 malicious); the
two-row difference is dropped during loading.

---

## 1. Schema

Both files have exactly two columns:

| Column | Type | Meaning |
|--------|------|---------|
| `Query` | text | The SQL query string or raw user input. |
| `Label` | integer | **`1` = malicious** (SQL-injection payload), **`0` = benign** (normal user input). |

`ml/preprocess.py:load_dataset()` is tolerant of column-name casing and ordering: it
matches `query` / `label` case-insensitively and falls back to the first/last
columns. It then casts `Query` to string, drops NA/empty queries, coerces `Label` to
a clean integer, and drops rows whose label cannot be parsed.

---

## 2. Label balance

Counts from `metrics.json` (post-cleaning) and the thesis's reported totals:

### `Modified_SQL_Dataset.csv` (training / Experiment 1)

| Class | Label | Count (≈) | Share |
|-------|------:|----------:|------:|
| Benign | 0 | 19,537 | ~63% |
| Malicious | 1 | 11,382 | ~37% |
| **Total** | | **30,918** | |

The class imbalance is the reason the classifier is trained with
`class_weight="balanced"` (see [MODEL.md](MODEL.md)).

### `clean_sql_dataset.csv` (generalisation / Experiment 2)

| Class | Label | Count (≈) | Share |
|-------|------:|----------:|------:|
| Benign | 0 | 70,576 | ~48% |
| Malicious | 1 | 77,750 | ~52% |
| **Total (thesis raw)** | | **148,326** | |
| **Total (loaded)** | | **148,324** | |

This dataset is close to balanced and is the thesis's Table 3 dataset (Kaggle).

---

## 3. The overlap finding (why we report "unseen-only")

**The training set is ~entirely contained within the evaluation set.** Roughly
**20.8%** of `clean_sql_dataset.csv` rows are exact duplicates of training queries
from `Modified_SQL_Dataset.csv`. This is directly observable: the first data rows of
both files are byte-for-byte identical, e.g.

```
""" or pg_sleep  (  __TIME__  )  --",1
create user name identified by pass123 temporary tablespace temp default tablespace users;,1
```

Consequence: evaluating the deployed model on the **full** clean dataset re-scores
queries the model already memorised during training, which inflates the apparent
generalisation. SQLInsight therefore reports Experiment 2 **two ways**:

- **Full** (thesis style): all 148,324 rows → 92.36% accuracy.
- **Unseen-only** (honest): only the 117,346 rows whose `Query` never appears in the
  training set (~79% of the clean dataset) → **90.35% accuracy**.

The unseen-only number is the one to cite for real-world generalisation. The
exclusion is computed in `ml/train_model.py`:

```python
train_queries = set(train_df["Query"].str.strip())
unseen_mask = ~eval_df["Query"].str.strip().isin(train_queries)
```

`metrics.json` records this explicitly via `datasets.overlap_note`:
*"train is ~entirely contained in eval; unseen-only excludes it."*

---

## 4. Sample rows

### Benign (`Label = 0`)
Benign rows are short, ordinary user inputs — usernames, identifiers, numbers, and
addresses — not full SQL statements. Real examples from the datasets:

```
99745017c,0
ejerci78,0
47209,0
"calle valencia de don juan 161, 7?d",0
b3r3al,0
```

(The demo generator mirrors this with inputs like `john_doe_2024`,
`iphone 15 pro max`, `4-bedroom house muscat`.)

### Malicious (`Label = 1`)
Malicious rows are SQL-injection payloads spanning the attack families SQLInsight
categorises. Real examples from the datasets:

```
""" or pg_sleep  (  __TIME__  )  --",1
" select * from users where id  =  '1' or @ @1  =  1 union select 1,version  (    )   -- 1'",1
" AND 1  =  utl_inaddr.get_host_address ( ... SELECT DISTINCT(table_name) FROM sys.all_tables ... ) AND 'i' = 'i",1
create user name identified by pass123 temporary tablespace temp default tablespace users;,1
```

These illustrate tautologies (`or '1'='1'`), `UNION SELECT`, time-based blind
(`pg_sleep`), error-based / out-of-band (`utl_inaddr.get_host_address`), and schema
enumeration (`sys.all_tables`). The demo generator (`backend/simulate_traffic.py`)
adds canonical payloads such as `' OR 1=1--`, `'; DROP TABLE users; --`,
`1' AND SLEEP(5)--`, and `'; EXEC xp_cmdshell('whoami')--`.

---

## 5. Data sources

The datasets are assembled from open-source corpora cited by the thesis:

- **Kaggle — "Biggest SQL Injection Dataset"** (Gambler Yu, 2024):
  <https://www.kaggle.com/datasets/gambleryu/biggest-sql-injection-dataset>
- **GitHub — SQL-Injection-Detection** (Saptajit Banerjee), file
  `demo_good_and_bad_requests.csv`:
  <https://github.com/saptajitbanerjee/SQL-Injection-Detection/blob/main/demo_good_and_bad_requests.csv>
- **Kaggle — "EDA - SQL injection dataset"** (M. Iniesta, 2024), used by the thesis
  for its second experiment:
  <https://www.kaggle.com/code/iniestamoh/eda-sql-injection-dataset/input>

The thesis (Section 5.3, Table 3) reports the combined corpus as 148,326 samples —
matching `clean_sql_dataset.csv` here.

---

## 6. Encoding caveat

Both CSV files contain **non-UTF-8 bytes** (raw, real-world payloads include odd
encodings and binary fragments). A naive `pd.read_csv(path)` can raise a
`UnicodeDecodeError`. The loader handles this defensively:

```python
# ml/preprocess.py
df = pd.read_csv(path, encoding="utf-8", encoding_errors="replace")
```

`encoding_errors="replace"` substitutes undecodable bytes with the Unicode
replacement character (U+FFFD) instead of crashing. The same robust loader is used
by both `ml/train_model.py` and any direct dataset inspection, so training is
reproducible regardless of stray bytes. (The standalone log monitor reads access
logs with the same `errors="replace"` strategy in `backend/monitor.py`.)

---

## 7. File locations

```
data/
├── Modified_SQL_Dataset.csv    # training / Experiment 1  (~2.3 MB, 30,918 rows)
└── clean_sql_dataset.csv       # generalisation / Experiment 2  (~55 MB, 148,324 rows)
```

Both are committed to the repository so training is reproducible out of the box
(`python ml/train_model.py`). Paths are defined in `config.py` as `TRAIN_DATASET`
and `EVAL_DATASET`.
