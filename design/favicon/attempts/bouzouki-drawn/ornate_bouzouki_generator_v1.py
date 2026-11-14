import sys

BODY = "M50 166C62 166 66 190 80 212C94 232 100 252 91 273C83 291 65 300 50 300C35 300 17 291 9 273C0 252 6 232 20 212C34 190 38 166 50 166Z"

def defs():
    return '''<defs>
  <linearGradient id="amber" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#f6ad45"/><stop offset="1" stop-color="#c56c14"/></linearGradient>
  <linearGradient id="neck" x1="0" y1="0" x2="1" y2="0"><stop offset="0" stop-color="#241a13"/><stop offset=".5" stop-color="#3a2a1d"/><stop offset="1" stop-color="#241a13"/></linearGradient>
  <pattern id="grain" width="2.6" height="10" patternUnits="userSpaceOnUse"><path d="M1.3 0V10" stroke="#a9560f" stroke-width=".5" opacity=".55"/></pattern>
  <clipPath id="face"><path d="{b}" transform="translate(50 233) scale(.94) translate(-50 -233)"/></clipPath>
</defs>'''.format(b=BODY)

def half():
    # ornamental pearl scrolls, left side; mirrored for the right
    return '''<g fill="none" stroke="#efe6cf" stroke-linecap="round" stroke-width="2.4">
      <path d="M36 246c-9-9-24-3-22 9 2 10 14 10 15 2 1-6-6-8-8-4"/>
      <path d="M38 222c-8-5-15-3-17 3"/>
    </g>
    <g fill="#efe6cf"><path d="M24 232c6-2 10 1 11 5-6 1-10-1-11-5z"/><circle cx="31" cy="212" r="1.8"/></g>'''

def instrument():
    frets = "".join(f'<path d="M44 {y}h12"/>' for y in range(54, 170, 9))
    dots = "".join(f'<circle cx="50" cy="{y}" r="1.7"/>' for y in (84, 111, 147))
    pegs = "".join(f'<ellipse cx="{x}" cy="{y}" rx="4" ry="2.8" fill="#e9b24a" stroke="#f7efd8" stroke-width="1.2"/>' for x in (33, 67) for y in (10, 20, 30, 39))
    strings = "".join(f'<path d="M{a} 44L{b} 286"/>' for a, b in ((45.2, 38.5), (47, 40), (48.8, 42.5), (50.5, 45.5), (49.5, 54.5), (51.2, 57.5), (53, 60), (54.8, 61.5)))
    return f'''{defs()}
  <path d="M40 40V12C40 4 44 1 50 1C56 1 60 4 60 12V40Z" fill="#17110c" stroke="#e9b24a" stroke-width="1.2"/>
  <path d="M46 14c2-5 6-5 8 0M47 24c2-4 4-4 6 0" fill="none" stroke="#efe6cf" stroke-width="1.4" stroke-linecap="round"/>
  {pegs}
  <rect x="43.5" y="41" width="13" height="130" fill="url(#neck)"/>
  <path d="M43.5 42h13" stroke="#efe6cf" stroke-width="2"/>
  <g stroke="#d9ccb0" stroke-width=".9">{frets}</g>
  <g fill="#efe6cf">{dots}</g>
  <path d="{BODY}" fill="#f4eedd"/>
  <path d="{BODY}" transform="translate(50 233) scale(.965) translate(-50 -233)" fill="#12100e"/>
  <g clip-path="url(#face)">
    <rect x="0" y="252" width="100" height="51" fill="url(#amber)"/>
    <rect x="0" y="252" width="100" height="51" fill="url(#grain)"/>
    <path d="M0 252H100" stroke="#efe6cf" stroke-width="2.4"/>
    {half()}
    <g transform="translate(100 0) scale(-1 1)">{half()}</g>
    <ellipse cx="50" cy="228" rx="15" ry="21" fill="#0b0908" stroke="#efe6cf" stroke-width="3"/>
    <ellipse cx="50" cy="228" rx="9.5" ry="15" fill="none" stroke="#e9b24a" stroke-width="1.6"/>
  </g>
  <path d="{BODY}" transform="translate(50 233) scale(.94) translate(-50 -233)" fill="none" stroke="#e9b24a" stroke-width=".9"/>
  <rect x="35" y="283" width="30" height="7" rx="3.5" fill="#c9c1ae" stroke="#7d7566" stroke-width=".8"/>
  <g stroke="#f3ead2" stroke-width=".55" opacity=".85">{strings}</g>'''

def alone():
    return f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="-2 -2 104 304">\n{instrument()}\n</svg>\n'

def tile(rx):
    return f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 64 64">
  <defs><linearGradient id="bg" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="#3b6cf0"/><stop offset="1" stop-color="#1a3aa8"/></linearGradient></defs>
  <rect width="64" height="64" rx="{rx}" fill="url(#bg)"/>
  <g transform="translate(32 32) rotate(32) scale(.27) translate(-50 -196)">
{instrument()}
  </g>
</svg>
'''
kind, out = sys.argv[1], sys.argv[2]
open(out, 'w').write(alone() if kind == 'alone' else tile(int(sys.argv[3]) if len(sys.argv) > 3 else 14))
