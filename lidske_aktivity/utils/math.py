from typing import Any, Optional, Union


def safe_div(a: Optional[Union[int, float]],
             b: Optional[Union[int, float]]) -> float:
    if a and b:
        return a / b
    return 0


def try_int(val: Any) -> Optional[int]:
    try:
        return int(val)
    except (TypeError, ValueError):
        return None
