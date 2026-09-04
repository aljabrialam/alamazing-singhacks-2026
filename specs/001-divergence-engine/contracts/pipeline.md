# Pipeline Contracts

Module boundaries. Each stage is independently testable.

## load.py
```python
def load_all(path: str = "data/") -> Book
```
All files, typed and joined, indexed by `client_id`. Never silently drops
rows — imperfections are logged to `Book.imperfections` and surfaced on
the uncertainty screen.

## diff.py
```python
def diff(book: Book, client_id: str, date_a: str, date_b: str) -> DataFrame
def attribution(book: Book, client_id: str, date_a: str, date_b: str) -> DataFrame
```
Aggregates across all the client's portfolios. Pure — no I/O, no model.

## events.py
```python
def events_between(book: Book, date_a: str, date_b: str) -> DataFrame
def events_touching(book: Book, client_id: str, date_a: str, date_b: str) -> DataFrame
```
Reads `event_log.csv` only. Returns event ids usable in `Finding.events`.

## divergence/*.py
```python
def detect(book: Book, client_id: str) -> list[Finding]
```
Same signature for all four detectors. Pure and deterministic. A detector
that cannot produce evidence returns nothing rather than a bare assertion.

## brief.py
```python
def write_brief(client: Client, findings: list[Finding]) -> str
```
One model call per client, at build time. Receives derived findings — never
raw client records. Output committed to `findings.json`.

## build.py
```python
def build(path: str = "data/") -> None   # writes web/public/findings.json
```

## Invariant
`build(x) == build(x)` for all x. Enforced by the determinism test.
