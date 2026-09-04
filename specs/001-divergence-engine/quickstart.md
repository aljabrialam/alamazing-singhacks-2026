# Quickstart

## Data
```bash
unzip singhacks-jb-wealth-intelligence.zip
cd singhacks-jb-wealth-intelligence
pip install -r requirements.txt
python starter/quickstart.py
```
`starter/quickstart.py` prints the book, event timeline, market table and
one worked client. It computes nothing clever — it shows the shape of the
data in 30 seconds.

## Read before coding
Open these three by hand. Twenty clients fits in your head.
- `clients.csv`
- `rm_notes.json`  ← the differentiator lives here
- `event_log.csv`  ← authoritative for 2026
- `docs/DATA_DICTIONARY.md` for field definitions

Pick one client, follow them across the five snapshots, work out from
`event_log.csv` which events touched them. That loop — position, change,
cause — is the core of the challenge.

## Pipeline
```bash
python pipeline/build.py        # → web/public/findings.json
pytest tests/test_determinism.py
```

## Web
```bash
cd web && npm install && npm run dev
```

## Snapshots
| Date | Marks |
|---|---|
| 2025-12-31 | Baseline |
| 2026-02-27 | Day before Middle East conflict |
| 2026-03-31 | After Strait of Hormuz closure |
| 2026-06-30 | After June technology drawdown |
| 2026-08-26 | Today |
