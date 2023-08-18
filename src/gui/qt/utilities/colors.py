import colorsys
import numpy as np

def _bright_color_generator():
    hue = 0
    while True:
        r,g,b = [int(255 * i) for i in colorsys.hsv_to_rgb(hue, 1, 1)]

        yield r,g,b

        hue += 0.1
        # avoid red and blue hues by wrapping to 0.2 when increment reaches 0.6
        if hue >= 0.6:
            hue = 0.2

bright_colors = _bright_color_generator()

def get_next_color():
    return next(bright_colors)

def rgb_color_generator(start_color, end_color, phase_increment=0.01):
    rs, gs, bs = start_color
    re, ge, be = end_color

    rr = re - rs
    gr = ge - gs
    br = be - bs

    rp = 0
    gp = np.pi / 3
    bp = 2 * np.pi / 3

    while True:
        r = int(rs + rr * (np.sin(rp) + 1) / 2)
        g = int(gs + gr * (np.sin(gp) + 1) / 2)
        b = int(bs + br * (np.sin(bp) + 1) / 2)

        yield r, g, b

        rp += phase_increment
        gp += phase_increment
        bp += phase_increment

        if rp > 2 * np.pi:
            rp -= 2 * np.pi
        if gp > 2 * np.pi:
            gp -= 2 * np.pi
        if bp > 2 * np.pi:
            bp -= 2 * np.pi