import math
import random
from functools import partial
from hashlib import sha1
from typing import Callable, Iterator, List, Tuple

from PIL import Image

TColor = Tuple[int, int, int, int]
TSliceFrac = float
TSliceRad = Tuple[float, float, TColor]


def _frac_to_rad(frac: float) -> float:
    return frac * 2 * math.pi


def _hash_to_fraction(s: str) -> float:
    """Hash a string into a floating point number between 0 and 1."""
    hash_obj = sha1(s.encode())
    hash_hex_len = hash_obj.digest_size * 2
    hash_int = int(hash_obj.hexdigest(), 16)
    max_hash_int = 16**hash_hex_len - 1
    fraction: float = hash_int / max_hash_int
    return fraction


def _hue_to_rgb(p: float, q: float, t: float) -> float:
    if t < 0:
        t += 1
    if t > 1:
        t -= 1
    if t < 1/6:
        return p + (q - p) * 6 * t
    if t < 1/2:
        return q
    if t < 2/3:
        return p + (q - p) * (2/3 - t) * 6
    return p


def _hsl_to_rgb(h: float, s: float, l: float) -> TColor:
    """https://stackoverflow.com/a/9493060"""
    if s == 0:
        r = g = b = l  # achromatic
    else:
        q = l * (1 + s) if l < 0.5 else l + s - l * s
        p = 2 * l - q
        r = _hue_to_rgb(p, q, h + 1/3)
        g = _hue_to_rgb(p, q, h)
        b = _hue_to_rgb(p, q, h - 1/3)
    return round(r * 255), round(g * 255), round(b * 255), 255


def hue_from_index(i: int, steps: int = 6) -> float:
    mod = i % steps
    frac = 1 / steps
    div = i // steps + 1
    shift = frac / div
    return mod * frac + shift


def color_from_index(i: int,
                     s: float = 0.8,
                     l: float = 0.5,
                     **kwargs) -> TColor:
    return _hsl_to_rgb(hue_from_index(i, **kwargs), s, l)


def _pie_chart_shader(x: int,
                      y: int,
                      w: int,
                      h: int,
                      slices_rad: List[TSliceRad],
                      default_color: TColor = (255, 255, 255, 255),
                      background_color: TColor = (0, 0, 0, 0)) -> TColor:
    center = w / 2, h / 2
    radius = min(center)
    coord = x - center[0], y - center[1]
    distance = math.sqrt(abs(coord[0]**2) + abs(coord[1]**2))
    angle = math.atan2(coord[1], coord[0]) + math.pi / 2
    if angle < 0:
        angle = 2*math.pi + angle
    if distance > radius:
        return background_color
    for slice_begin, slice_end, color in slices_rad:
        if slice_begin <= angle < slice_end:
            return color
    return default_color


def _draw_image(w: int,
                h: int,
                shader: Callable,
                background_color: TColor = (0, 0, 0, 0)) -> Image:
    image = Image.new('RGBA', (w, h), background_color)
    pixels = image.load()
    for x in range(w):
        for y in range(h):
            pixels[x, y] = shader(x, y, w - 1, h - 1)
    return image


def _slices_frac_to_rad(slices_frac: List[TSliceFrac]) -> Iterator[TSliceRad]:
    cumulative_frac = 0.0
    for i, frac in enumerate(slices_frac):
        yield (
            _frac_to_rad(cumulative_frac),
            _frac_to_rad(cumulative_frac + frac),
            color_from_index(i)
        )
        cumulative_frac += frac


def draw_pie_chart(size: int, slices_frac: List[TSliceFrac]) -> Image:
    slices_rad = list(_slices_frac_to_rad(slices_frac))
    return _draw_image(
        w=size,
        h=size,
        shader=partial(_pie_chart_shader, slices_rad=slices_rad)
    )


def gen_random_slices(n_min: int, n_max: int) -> Iterator[TSliceFrac]:
    total = 0.0
    while total <= 1:
        frac = 1 / random.randint(n_min, n_max)
        total += frac
        yield frac