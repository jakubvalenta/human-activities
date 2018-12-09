import math
from functools import partial
from typing import Callable, Iterator, List, Tuple

from PIL import Image

TColor = Tuple[int, int, int]
TSlicePerc = Tuple[int, TColor]
TSliceRad = Tuple[float, float, TColor]


def perc_to_rad(perc: int) -> float:
    return perc / 100 * 2 * math.pi


def pie_chart_shader(x: int,
                     y: int,
                     w: int,
                     h: int,
                     slices_rad: List[TSliceRad]) -> TColor:
    center = w / 2, h / 2
    radius = min(center)
    coord = x - center[0], y - center[1]
    distance = math.sqrt(abs(coord[0]**2) + abs(coord[1]**2))
    angle = math.atan2(coord[1], coord[0]) + math.pi / 2
    if angle < 0:
        angle = 2*math.pi + angle
    if distance > radius:
        return 0, 0, 0
    for slice_begin, slice_end, color in slices_rad:
        if slice_begin <= angle < slice_end:
            return color
    return 255, 255, 255


def draw_image(w: int, h: int, shader: Callable):
    image = Image.new('RGB', (w, h), 'black')
    pixels = image.load()
    for x in range(w):
        for y in range(h):
            pixels[x, y] = shader(x, y, w - 1, h - 1)
    image.save('tmp.png')


def slices_perc_to_rad(slices_perc: List[TSlicePerc]) -> Iterator[TSliceRad]:
    cumulative_perc = 0
    for perc, color in slices_perc:
        yield (
            perc_to_rad(cumulative_perc),
            perc_to_rad(cumulative_perc + perc),
            color
        )
        cumulative_perc += perc


def draw_pie_chart(size: int, slices_perc: List[TSlicePerc]):
    slices_rad = list(slices_perc_to_rad(slices_perc))
    draw_image(
        w=size,
        h=size,
        shader=partial(pie_chart_shader, slices_rad=slices_rad)
    )


if __name__ == '__main__':
    draw_pie_chart(
        size=100,
        slices_perc=[
            (50, (255, 0, 0)),
            (30, (0, 255, 0)),
            (10, (0, 0, 255)),
            (5, (255, 255, 0)),
        ]
    )
