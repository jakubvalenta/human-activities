import logging
import math
import random
import sys
from functools import lru_cache, partial
from hashlib import sha1
from typing import Callable, Iterator, List, NamedTuple, Tuple

from PIL import Image

logger = logging.getLogger(__name__)

MAX_COLORS = 64
ICON_CACHE_SIZE = 128


class Color(NamedTuple):
    r: int
    g: int
    b: int
    a: int = 255


class Slice(NamedTuple):
    start: float
    end: float
    color: Color


COLOR_TRANSPARENT = Color(0, 0, 0, 0)
COLOR_WHITE = Color(255, 255, 255)
COLOR_GRAY = Color(147, 161, 161)
COLOR_BLACK = Color(0, 0, 0)


def _frac_to_rad(frac: float) -> float:
    return min(frac, 1) * 2 * math.pi


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


def _hsl_to_rgb(h: float, s: float, l: float) -> Tuple[int, int, int]:
    """https://stackoverflow.com/a/9493060"""
    if s == 0:
        r = g = b = l  # achromatic
    else:
        q = l * (1 + s) if l < 0.5 else l + s - l * s
        p = 2 * l - q
        r = _hue_to_rgb(p, q, h + 1/3)
        g = _hue_to_rgb(p, q, h)
        b = _hue_to_rgb(p, q, h - 1/3)
    return round(r * 255), round(g * 255), round(b * 255)


def hue_from_index(i: int, steps: int = 6) -> float:
    mod = i % steps
    frac = 1 / steps
    div = i // steps + 1
    shift = frac / div
    return mod * frac + shift


@lru_cache(MAX_COLORS + 1)
def color_from_index(i: int,
                     s: float = 0.8,
                     l: float = 0.5,
                     default_color: Color = COLOR_GRAY,
                     **kwargs) -> Color:
    if i == -1:
        return default_color
    rgb = _hsl_to_rgb(hue_from_index(i, **kwargs), s, l)
    return Color(*rgb)


def _pie_chart_shader(x: int,
                      y: int,
                      w: int,
                      h: int,
                      slices: List[Slice],
                      background_color: Color = COLOR_TRANSPARENT) -> Color:
    center = w / 2, h / 2
    radius = min(center)
    coord = x - center[0], y - center[1]
    distance = math.sqrt(abs(coord[0]**2) + abs(coord[1]**2))
    angle = math.atan2(coord[1], coord[0]) + math.pi / 2
    if angle < 0:
        angle = 2*math.pi + angle
    if distance <= radius:
        for slice in slices:
            if slice.start <= angle < slice.end:
                return slice.color
    return background_color


def _draw_image(w: int,
                h: int,
                shader: Callable,
                background_color: Color = COLOR_TRANSPARENT) -> Image.Image:
    image = Image.new('RGBA', (w, h), background_color)
    pixels = image.load()
    for x in range(w):
        for y in range(h):
            pixels[x, y] = shader(x, y, w - 1, h - 1)
    return image


def _create_slices(fractions: Tuple[float, ...],
                   colors: Tuple[Color, ...] = (),
                   default_color: Color = COLOR_WHITE) -> Iterator[Slice]:
    if not fractions or sum(fractions) == 0:
        yield Slice(
            start=0,
            end=_frac_to_rad(1),
            color=default_color
        )
        return
    cumulative_frac = 0.0
    if not colors:
        colors = tuple(color_from_index(i) for i in range(len(fractions)))
    for frac, color in zip(fractions, colors):
        frac = round(frac, 2)
        if frac == 0:
            continue
        yield Slice(
            start=_frac_to_rad(cumulative_frac),
            end=_frac_to_rad(cumulative_frac + frac),
            color=color
        )
        cumulative_frac += frac


@lru_cache(ICON_CACHE_SIZE)
def draw_pie_chart_png(size: int,
                       fractions: Tuple[float, ...],
                       colors: Tuple[Color, ...] = ()) -> Image.Image:
    logger.info('Drawing PNG icon %s', [f'{fract:.2f}' for fract in fractions])
    slices = list(_create_slices(fractions, colors))
    return _draw_image(
        w=size,
        h=size,
        shader=partial(_pie_chart_shader, slices=slices)
    )


@lru_cache(ICON_CACHE_SIZE)
def draw_pie_chart_svg(fractions: Tuple[float, ...],
                       colors: Tuple[Color, ...] = ()) -> Iterator[str]:
    logger.info('Drawing SVG icon %s', [f'{fract:.2f}' for fract in fractions])
    slices = _create_slices(fractions, colors)
    yield '''<?xml version="1.0" encoding="UTF-8" ?>
<svg xmlns="http://www.w3.org/2000/svg" version="1.1" viewBox="-1 -1 2 2">\n'''
    yield '<g transform="rotate(-90)">\n'
    for slice in slices:
        color = slice.color
        if slice.start == 0 and slice.end == 2*math.pi:
            yield (f'<circle cx="0" cy="0" r="1" '
                   f'fill="rgb({color.r}, {color.g}, {color.b})" />\n')
            continue
        start_x, start_y = math.cos(slice.start), math.sin(slice.start)
        end_x, end_y = math.cos(slice.end), math.sin(slice.end)
        large_arc_flag = int(slice.end - slice.start > math.pi)
        yield (f'<path d="M {start_x:.5f} {start_y:.5f} '
               f'A 1 1 0 {large_arc_flag} 1 {end_x:.5f} {end_y:.5f} L 0 0" '
               f'fill="rgb({color.r}, {color.g}, {color.b})" />\n')
    yield '</g>\n'
    yield '</svg>\n'


def gen_random_slices(n_min: int = 3, n_max: int = 8) -> Iterator[float]:
    total = 0.0
    while total <= 1:
        frac = 1 / random.randint(n_min, n_max)
        total += frac
        yield frac


@lru_cache(ICON_CACHE_SIZE)
def calc_icon_hash(fractions: Tuple[float, ...]) -> str:
    if not fractions or sum(fractions) == 0:
        return '0'
    return '_'.join(f'{frac*100:.0f}' for frac in fractions)


def print_default_svg_icon():
    fractions = (0.35, 0.25, 0.20, 0.15, 0.05)
    svg = draw_pie_chart_svg(fractions)
    sys.stdout.writelines(svg)
