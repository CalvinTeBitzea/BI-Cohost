import json
from pathlib import Path
import jsonschema

_SCHEMA_DIR = Path(__file__).parent.parent / "schemas"
_cache: dict = {}


def _load(schema_name: str) -> dict:
    if schema_name not in _cache:
        path = _SCHEMA_DIR / f"{schema_name}.json"
        _cache[schema_name] = json.loads(path.read_text())
    return _cache[schema_name]


def validate(schema_name: str, data: dict) -> None:
    """Raises jsonschema.ValidationError if data fails the schema."""
    jsonschema.validate(instance=data, schema=_load(schema_name))


def is_valid(schema_name: str, data: dict) -> bool:
    try:
        validate(schema_name, data)
        return True
    except jsonschema.ValidationError:
        return False
