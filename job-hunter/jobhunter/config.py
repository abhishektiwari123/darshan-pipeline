from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"


def load(path: str | None = None) -> dict:
    cfg_path = Path(path) if path else ROOT / "config.yaml"
    if not cfg_path.exists():
        raise SystemExit(
            f"{cfg_path} not found. Copy config.example.yaml to config.yaml and fill it in."
        )
    cfg = yaml.safe_load(cfg_path.read_text()) or {}
    base = cfg_path.parent
    for key in ("pdf", "text"):
        value = cfg.get("resume", {}).get(key)
        if value:
            cfg["resume"][key] = str((base / value).resolve())
    DATA.mkdir(exist_ok=True)
    return cfg
