# Model code

Copied from the private repository that holds the full transfer valuation pipeline. The full pipeline (data ingest, warehouse, fee model, revenue and NPV layers, every validation gate) lives there, because it is built on data that cannot be redistributed.

| File | What it does | Runs here? |
|---|---|---|
| `usage_model/usage.py` | Usage share and efficiency, the definitions this repo tests | Yes |
| `usage_model/wowy.py` | On/off team xG difference per 90, shrunk for thin samples | Yes (self-check) |
| `usage_model/understat.py` | Downloads and tidies the Understat shot archive | Yes |
| `usage_model/talent.py` | The price-blind talent model, as a reference copy | Self-check only (needs scikit-learn; skips without it) |

Each file has an offline self-check: `PYTHONPATH=src python -m usage_model.usage`.
