import logging
import math
import random
import sys
from functools import lru_cache, partial
from hashlib import sha1
from typing import Callable, Iterator, List, NamedTuple, Optional, Tuple

from PIL import Image

logger = logging.getLogger(__name__)


class Color(NamedTuple):
    r: int
    g: int
    b: int
    a: int = 255


# https://sashat.me/2017/01/11/list-of-20-simple-distinct-colors/
COLORS = (
    Color(230, 25, 75),
    Color(60, 180, 75),
    Color(255, 225, 25),
    Color(0, 130, 200),
    Color(245, 130, 48),
    Color(145, 30, 180),
    Color(70, 240, 240),
    Color(240, 50, 230),
    Color(210, 245, 60),
    Color(250, 190, 190),
    Color(0, 128, 128),
    Color(230, 190, 255),
    Color(170, 110, 40),
    Color(255, 250, 200),
    Color(128, 0, 0),
    Color(170, 255, 195),
    Color(128, 128, 0),
    Color(255, 215, 180),
    Color(0, 0, 128),
    Color(128, 128, 128),
    Color(255, 255, 255),
    Color(0, 0, 0),
)
COLOR_TRANSPARENT = Color(0, 0, 0, 0)
COLOR_DEFAULT = Color(147, 161, 161)


class Slice(NamedTuple):
    start: float
    end: float
    color: Color = COLOR_DEFAULT


ICON_CACHE_SIZE = 128
DEFAULT_FRACTIONS = (0.35, 0.25, 0.20, 0.15, 0.05)


def _frac_to_rad(frac: float) -> float:
    return min(frac, 1) * 2 * math.pi


def _hash_to_fraction(s: str) -> float:
    """Hash a string into a floating point number between 0 and 1."""
    hash_obj = sha1(s.encode())
    hash_hex_len = hash_obj.digest_size * 2
    hash_int = int(hash_obj.hexdigest(), 16)
    max_hash_int = 16 ** hash_hex_len - 1
    fraction: float = hash_int / max_hash_int
    return fraction


def _color_from_index(i: int) -> Color:
    if -1 < i < len(COLORS):
        return COLORS[i]
    return COLOR_DEFAULT


def _gen_colors(
    num: int, highlighted: Optional[int] = None
) -> Tuple[Color, ...]:
    if highlighted is not None:
        colors = [COLOR_DEFAULT for i in range(num)]
        colors[highlighted] = _color_from_index(highlighted)
        return tuple(colors)
    return tuple(_color_from_index(i) for i in range(num))


def _pie_chart_shader(
    x: int,
    y: int,
    w: int,
    h: int,
    slices: List[Slice],
    background_color: Color = COLOR_TRANSPARENT,
) -> Color:
    center = w / 2, h / 2
    radius = min(center)
    coord = x - center[0], y - center[1]
    distance = math.sqrt(abs(coord[0] ** 2) + abs(coord[1] ** 2))
    angle = math.atan2(coord[1], coord[0]) + math.pi / 2
    if angle < 0:
        angle = 2 * math.pi + angle
    if distance <= radius:
        for slice in slices:
            if slice.start <= angle < slice.end:
                return slice.color
    return background_color


def _draw_image(
    w: int,
    h: int,
    shader: Callable,
    background_color: Color = COLOR_TRANSPARENT,
) -> Image.Image:
    image = Image.new('RGBA', (w, h), background_color)
    pixels = image.load()
    for x in range(w):
        for y in range(h):
            pixels[x, y] = shader(x, y, w - 1, h - 1)
    return image


def _create_slices(
    fractions: Tuple[float, ...], highlighted: Optional[int] = None
) -> Iterator[Slice]:
    if not fractions or sum(fractions) == 0:
        yield Slice(start=0, end=_frac_to_rad(1))
        return
    cumulative_frac = 0.0
    colors = _gen_colors(len(fractions), highlighted)
    for frac, color in zip(fractions, colors):
        frac = round(frac, 2)
        if frac == 0:
            continue
        yield Slice(
            start=_frac_to_rad(cumulative_frac),
            end=_frac_to_rad(cumulative_frac + frac),
            color=color,
        )
        cumulative_frac += frac


@lru_cache(ICON_CACHE_SIZE)
def draw_pie_chart_png(
    size: int, fractions: Tuple[float, ...], highlighted: Optional[int] = None
) -> Image.Image:
    logger.info('Drawing PNG icon %s', [f'{fract:.2f}' for fract in fractions])
    slices = list(_create_slices(fractions, highlighted))
    return _draw_image(
        w=size, h=size, shader=partial(_pie_chart_shader, slices=slices)
    )


@lru_cache(ICON_CACHE_SIZE)
def draw_pie_chart_svg(
    fractions: Tuple[float, ...], highlighted: Optional[int] = None
) -> str:
    logger.info('Drawing SVG icon %s', [f'{fract:.2f}' for fract in fractions])
    slices = _create_slices(fractions, highlighted)
    lines = []
    lines.append('<?xml version="1.0" encoding="UTF-8" ?>')
    lines.append(
        '<svg xmlns="http://www.w3.org/2000/svg" '
        'version="1.1" viewBox="-1 -1 2 2">'
    )
    lines.append('<g transform="rotate(-90)">')
    for slice in slices:
        color = slice.color
        if slice.start == 0 and slice.end == 2 * math.pi:
            lines.append(
                f'<circle cx="0" cy="0" r="1" '
                f'fill="rgb({color.r}, {color.g}, {color.b})" />'
            )
            continue
        start_x, start_y = math.cos(slice.start), math.sin(slice.start)
        end_x, end_y = math.cos(slice.end), math.sin(slice.end)
        large_arc_flag = int(slice.end - slice.start > math.pi)
        lines.append(
            f'<path d="M {start_x:.5f} {start_y:.5f} '
            f'A 1 1 0 {large_arc_flag} 1 {end_x:.5f} {end_y:.5f} L 0 0" '
            f'fill="rgb({color.r}, {color.g}, {color.b})" />'
        )
    lines.append('</g>')
    lines.append('</svg>')
    lines.append('')
    return '\n'.join(lines)


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
    svg = draw_pie_chart_svg(DEFAULT_FRACTIONS)
    sys.stdout.write(svg)
