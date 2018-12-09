import math
import sys
from typing import Iterator, List, Tuple


def percent_to_coord(percent: float) -> Tuple[float, float]:
    x = math.cos(2 * math.pi * percent)
    y = math.sin(2 * math.pi * percent)
    return x, y


def draw_pie_chart(slices: List[Tuple[float, str]]) -> Iterator[str]:
    yield '<?xml version="1.0" encoding="UTF-8" ?>'
    yield ('<svg xmlns="http://www.w3.org/2000/svg" version="1.1" '
           'viewBox="-1 -1 2 2">')
    cumulative_percent: float = 0
    for percent, color in slices:
        start_x, start_y = percent_to_coord(cumulative_percent)
        cumulative_percent += percent
        end_x, end_y = percent_to_coord(cumulative_percent)
        large_arc_flag = int(percent > 0.5)
        d = ' '.join([
            f'M {start_x} {start_y}',
            f'A 1 1 0 {large_arc_flag} 1 {end_x} {end_y}',
            f'L 0 0',
        ])
        yield f'<path d="{d}" fill="{color}" />'
    yield '</svg>'


if __name__ == '__main__':
    slices = [
        (0.1, 'Coral'),
        (0.65, 'CornflowerBlue'),
        (0.2, '#00ab6b'),
    ]
    for line in draw_pie_chart(slices):
        print(line, file=sys.stdout)
