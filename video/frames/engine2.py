#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
engine2.py — 「普博奇点」风格渲染引擎（米白纸感 / 学术排版）

还原要点：
  · 背景 #F7F5F1 米白纸感
  · 左上角细体小字：视频标题 + 分隔符
  · 右上角：PART NN / 21 · 章节名
  · 大标题：黑体粗，下方一道红色短下划线
  · 正文：深灰，行距宽松
  · 数据脚注：左下角，小字 + 橙色圆点
  · 关键词/结论：红色加粗
"""
import sys

from PIL import Image, ImageDraw, ImageFont

sys.stdout.reconfigure(encoding='utf-8', errors='replace')

W, H = 1920, 1080
FPS = 30

FB = "C:/Windows/Fonts/msyhbd.ttc"
FR = "C:/Windows/Fonts/msyh.ttc"
FL = "C:/Windows/Fonts/msyh.ttc"

PAPER   = (247, 245, 241)
INK     = (26, 26, 26)
INK2    = (60, 60, 60)
GRAY    = (128, 126, 121)
LGRAY   = (190, 186, 179)
RED     = (214, 40, 40)
ORANGE  = (230, 126, 34)
BLUE    = (52, 101, 164)
GREEN   = (56, 142, 60)
DARK    = (33, 33, 33)

_f = {}


def font(size, bold=True, light=False):
    key = (size, bold, light)
    if key not in _f:
        _f[key] = ImageFont.truetype(FB if bold else FR, size)
    return _f[key]


def ease_out(p):
    p = max(0.0, min(1.0, p))
    return 1 - (1 - p) ** 3


def ease_in_out(p):
    p = max(0.0, min(1.0, p))
    return 3 * p * p - 2 * p * p * p


def mix(c1, c2, a):
    a = max(0.0, min(1.0, a))
    return tuple(int(c1[i] + (c2[i] - c1[i]) * a) for i in range(3))


def seg(t, t0, t1):
    if t <= t0:
        return 0.0
    if t >= t1:
        return 1.0
    return (t - t0) / (t1 - t0)


def fade(t, t0, t1, fi=0.45, fo=0.45):
    if t < t0 or t > t1:
        return 0.0
    a = 1.0
    if t < t0 + fi:
        a = (t - t0) / fi
    if t > t1 - fo:
        a = min(a, (t1 - t) / fo)
    return max(0.0, min(1.0, a))


def tx(d, xy, s, size, color, anchor="la", bold=True, alpha=1.0, spacing=0):
    if alpha <= 0.01 or not s:
        return
    c = mix(PAPER, color, alpha)
    if spacing == 0:
        d.text(xy, s, font=font(size, bold), fill=c, anchor=anchor)
    else:
        # 手动字距
        x, y = xy
        for ch in s:
            d.text((x, y), ch, font=font(size, bold), fill=c, anchor=anchor)
            bb = font(size, bold).getbbox(ch)
            x += (bb[2] - bb[0]) + spacing


def tw(s, size, bold=True):
    f = font(size, bold)
    bb = f.getbbox(s)
    return bb[2] - bb[0]


def line_height(size):
    return int(size * 1.42)


def wrap(d, s, size, max_w, bold=True):
    """按像素宽度折行（中文逐字）"""
    lines, cur = [], ""
    for ch in s:
        if ch == "\n":
            lines.append(cur); cur = ""
            continue
        test = cur + ch
        if tw(test, size, bold) > max_w and cur:
            lines.append(cur); cur = ch
        else:
            cur = test
    if cur:
        lines.append(cur)
    return lines


def num(t, t0, t1, target, fmt="{:,.0f}"):
    return fmt.format(target * ease_out(seg(t, t0, t1)))


# ---------------- 版式部件 ----------------
def paper(d, alpha=1.0):
    d.rectangle([0, 0, W, H], fill=mix(PAPER, PAPER, 1))


def header(d, title, part, chapter, alpha=1.0):
    """左上标题 / 右上部编号"""
    tx(d, (120, 52), title, 24, GRAY, bold=False, alpha=alpha)
    tx(d, (W - 120, 52), f"PART {part:02d} / 11 · {chapter}", 24, LGRAY,
       anchor="ra", bold=False, alpha=alpha)


def footer(d, left, right, alpha=1.0):
    """底部脚注 + 大红底线"""
    tx(d, (120, H - 62), left, 22, GRAY, bold=False, alpha=alpha)
    tx(d, (W - 120, H - 62), right, 22, GRAY, anchor="ra", bold=False, alpha=alpha)
    # 橙色圆点
    d.ellipse([120 - 0, H - 62 + 6, 120 - 0 + 0, H - 62 + 6], fill=ORANGE)
    p = seg(alpha, 0, 1)


def folio(d, alpha=1.0, prog=1.0):
    """底部红色进度线"""
    y = H - 26
    d.rectangle([120, y, W - 120, y + 2], fill=mix(PAPER, LGRAY, 0.45 * alpha))
    d.rectangle([120, y, 120 + int((W - 240) * prog), y + 2],
                fill=mix(PAPER, RED, 0.85 * alpha))


def h1(d, s, y=196, alpha=1.0, size=76):
    tx(d, (120, y), s, size, INK, alpha=alpha)
    # 红色短下划线
    d.rectangle([120, y + size + 22, 120 + 78, y + size + 30],
                fill=mix(PAPER, RED, alpha))
    return y + size + 60


def bullet(d, x, y, text_s, size=38, color=INK2, alpha=1.0, dot=ORANGE, lh=None):
    d.ellipse([x, y + int(size * 0.32), x + 10, y + int(size * 0.32) + 10],
              fill=mix(PAPER, dot, alpha))
    tx(d, (x + 34, y), text_s, size, color, bold=False, alpha=alpha)
    return y + (lh or line_height(size))


def kv(d, x, y, k, v, ks=34, vs=52, alpha=1.0, vcolor=INK, gap=150):
    tx(d, (x, y), k, ks, GRAY, bold=False, alpha=alpha)
    tx(d, (x + gap, y - 6), v, vs, vcolor, bold=True, alpha=alpha)
    return y + vs + 34


def bignum(d, x, y, s, size=150, color=INK, alpha=1.0):
    tx(d, (x, y), s, size, color, alpha=alpha)
    return y + size


def hbar(d, x, y, wmax, h, p, color, alpha=1.0, bg=True):
    if bg:
        d.rectangle([x, y, x + wmax, y + h], fill=mix(PAPER, (238, 234, 228), alpha))
    w = max(0, int(wmax * ease_out(p)))
    if w > 1:
        d.rectangle([x, y, x + w, y + h], fill=mix(PAPER, color, alpha))


def vbar(d, x, base_y, w, hmax, p, color, alpha=1.0):
    h = max(0, int(hmax * ease_out(p)))
    if h > 1:
        d.rectangle([x, base_y - h, x + w, base_y], fill=mix(PAPER, color, alpha))


def rule(d, y, alpha=1.0, color=None):
    d.rectangle([120, y, W - 120, y + 1], fill=mix(PAPER, color or LGRAY, alpha))
