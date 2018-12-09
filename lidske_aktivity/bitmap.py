import math
from functools import partial
from hashlib import sha1
from typing import Callable, Iterator, List, Tuple

from PIL import Image

TColor = str
TSliceFrac = Tuple[int, TColor]
TSliceRad = Tuple[float, float, TColor]


def frac_to_rad(frac: int) -> float:
    return frac * 2 * math.pi


def hash_to_fraction(s: str) -> float:
    """Hash a string into a floating point number between 0 and 1."""
    hash_obj = sha1(s.encode())
    hash_hex_len = hash_obj.digest_size * 2
    hash_int = int(hash_obj.hexdigest(), 16)
    max_hash_int = 16**hash_hex_len - 1
    fraction: float = hash_int / max_hash_int
    return fraction


def rgb_int_to_tuple(rgb_int: int) -> TColor:
    return rgb_int & 255, (rgb_int >> 8) & 255, (rgb_int >> 16) & 255


def str_to_color(s: str) -> TColor:
    fraction = hash_to_fraction(s)
    rgb_int = round(0xffffff * fraction)
    return rgb_int_to_tuple(rgb_int)


def pie_chart_shader(x: int,
                     y: int,
                     w: int,
                     h: int,
                     slices_rad: List[TSliceRad],
                     default_color: str = (255, 255, 255)) -> TColor:
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
    return default_color


def draw_image(w: int,
               h: int,
               shader: Callable,
               background_color: TColor = '#000000') -> Image:
    image = Image.new('RGB', (w, h), background_color)
    pixels = image.load()
    for x in range(w):
        for y in range(h):
            pixels[x, y] = shader(x, y, w - 1, h - 1)
    return image


def _slices_frac_to_rad(slices_frac: List[TSliceFrac]) -> Iterator[TSliceRad]:
    cumulative_frac = 0
    for frac, color in slices_frac:
        yield (
            frac_to_rad(cumulative_frac),
            frac_to_rad(cumulative_frac + frac),
            color
        )
        cumulative_frac += frac


def draw_pie_chart(size: int, slices_frac: List[TSliceFrac]) -> Image:
    slices_rad = list(_slices_frac_to_rad(slices_frac))
    return draw_image(
        w=size,
        h=size,
        shader=partial(pie_chart_shader, slices_rad=slices_rad)
    )


if __name__ == '__main__':
    image = draw_pie_chart(
        size=100,
        slices_frac=[
            (0.5, (255, 0, 0)),
            (0.3, (0, 255, 0)),
            (0.1, (0, 0, 255)),
            (0.05, (255, 255, 0)),
        ]
    )
    image.save('tmp.png')
