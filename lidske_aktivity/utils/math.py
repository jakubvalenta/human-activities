from typing import Any, Optional


def safe_div(a: Optional[int], b: Optional[int]) -> float:
    if a and b:
        return a / b
    return 0


def try_int(val: Any) -> Optional[int]:
    try:
        return int(val)
    except (TypeError, ValueError):
        return None
