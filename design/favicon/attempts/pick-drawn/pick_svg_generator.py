import math, sys

def rounded_polygon(pts, r):
    """SVG path of a polygon with every corner rounded by radius r."""
    n = len(pts); segs = []
    for i in range(n):
        p0, p1, p2 = pts[i - 1], pts[i], pts[(i + 1) % n]
        v1 = (p0[0] - p1[0], p0[1] - p1[1]); v2 = (p2[0] - p1[0], p2[1] - p1[1])
        l1 = math.hypot(*v1); l2 = math.hypot(*v2)
        u1 = (v1[0] / l1, v1[1] / l1); u2 = (v2[0] / l2, v2[1] / l2)
        ang = math.acos(u1[0] * u2[0] + u1[1] * u2[1])
        d = r / math.tan(ang / 2)
        a = (p1[0] + u1[0] * d, p1[1] + u1[1] * d); b = (p1[0] + u2[0] * d, p1[1] + u2[1] * d)
        cross = u1[0] * u2[1] - u1[1] * u2[0]
        segs.append((a, b, 0 if cross > 0 else 1))
    out = "M{:.2f} {:.2f}".format(*segs[0][0])
    for i, (a, b, sweep) in enumerate(segs):
        if i: out += "L{:.2f} {:.2f}".format(*a)
        out += "A{r} {r} 0 0 {s} {:.2f} {:.2f}".format(*b, r=r, s=sweep)
    return out + "Z"

# Rounded triangle like a Greek "pena": wide top, rounded point at the bottom.
SHAPE = rounded_polygon([(4, 10), (60, 10), (32, 58.5)], 12.5)
INNER = rounded_polygon([(11, 15.500), (53, 15.500), (32, 52)], 8)

B_PATH = "M23 17h10.500a7 7 0 0 1 4.100 12.700A7.800 7.800 0 0 1 34.500 44H23zM28.500 22v6.200h4a3.100 3.100 0 0 0 0-6.200zM28.500 33v6.200h5a3.100 3.100 0 0 0 0-6.200z"

def svg(body, defs=""):
    return f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 64 64"><defs>{defs}<clipPath id="c"><path d="{SHAPE}"/></clipPath></defs>{body}</svg>\n'

def tortoise():
    defs = '<linearGradient id="g" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="#ffbd3a"/><stop offset="1" stop-color="#d9731a"/></linearGradient>'
    swirls = '''<g clip-path="url(#c)">
  <rect width="64" height="64" fill="url(#g)"/>
  <g fill="#3b1405" opacity=".9">
    <ellipse cx="14" cy="14" rx="9" ry="5" transform="rotate(35 14 14)"/><ellipse cx="49" cy="30" rx="8" ry="4.500" transform="rotate(-50 49 30)"/>
    <ellipse cx="26" cy="46" rx="7" ry="3.600" transform="rotate(60 26 46)"/><ellipse cx="45" cy="13" rx="6" ry="3" transform="rotate(10 45 13)"/>
  </g>
  <g fill="#a8480d" opacity=".75"><ellipse cx="33" cy="28" rx="11" ry="5.500" transform="rotate(-30 33 28)"/><ellipse cx="18" cy="31" rx="6" ry="3" transform="rotate(75 18 31)"/></g>
  <g fill="#ffe08a" opacity=".85"><ellipse cx="38" cy="40" rx="5" ry="2.200" transform="rotate(-60 38 40)"/><ellipse cx="22" cy="22" rx="4.500" ry="2" transform="rotate(20 22 22)"/></g>
</g>
<path d="%s" fill="none" stroke="#5a2308" stroke-width="1.200"/>
<path d="%s" transform="translate(0 4)" fill="#fbe7a6" stroke="#6a3a05" stroke-width=".8" opacity="0"/>
<path d="%s" fill="#f9dc8a" stroke="#6a3a05" stroke-width="1" transform="translate(32 28) scale(.78) translate(-31.5 -30.5)"/>''' % (SHAPE, B_PATH, B_PATH)
    return svg(swirls, defs)

def blue():
    defs = '<linearGradient id="g" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="#4a7bff"/><stop offset="1" stop-color="#1a3aa8"/></linearGradient><linearGradient id="a" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#ffc25a"/><stop offset="1" stop-color="#e58a1f"/></linearGradient>'
    return svg(f'''<path d="{SHAPE}" fill="url(#g)"/>
<path d="{INNER}" fill="none" stroke="url(#a)" stroke-width="1.800" stroke-linejoin="round"/>
<path d="{B_PATH}" fill="#fff" transform="translate(32 28) scale(.78) translate(-31.5 -30.5)"/>''', defs)

def black():
    defs = '<linearGradient id="a" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#ffc25a"/><stop offset="1" stop-color="#e58a1f"/></linearGradient>'
    return svg(f'''<path d="{SHAPE}" fill="#14110f"/>
<path d="{SHAPE}" fill="none" stroke="#f1e8d2" stroke-width="2.200"/>
<path d="{INNER}" fill="none" stroke="#f1e8d2" stroke-width="1.100" stroke-dasharray="2.600 1.800" stroke-linecap="round"/>
<path d="{B_PATH}" fill="url(#a)" transform="translate(32 28) scale(.78) translate(-31.5 -30.5)"/>''', defs)

if __name__ == "__main__":
    for name, fn in (("tortoise", tortoise), ("blue", blue), ("black", black)):
        open(f"{sys.argv[1]}/pick_{name}.svg", "w").write(fn())
