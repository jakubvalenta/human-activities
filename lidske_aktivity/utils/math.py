from typing import Optional, Union


def safe_div(
    a: Optional[Union[int, float]], b: Optional[Union[int, float]]
) -> float:
    if a and b:
        return a / b
    return 0.0
