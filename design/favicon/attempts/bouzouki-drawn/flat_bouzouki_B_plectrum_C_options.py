import sys
TILE = lambda rx, bg1="#3b6cf0", bg2="#1a3aa8": f'<defs><linearGradient id="bg" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="{bg1}"/><stop offset="1" stop-color="{bg2}"/></linearGradient><linearGradient id="am" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#ffc25a"/><stop offset="1" stop-color="#e58a1f"/></linearGradient></defs><rect width="64" height="64" rx="{rx}" fill="url(#bg)"/>'

def A(rx=14):  # flat white bouzouki, tilted, on the brand-blue tile
    return f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 64 64">{TILE(rx)}
<g transform="translate(32 32) rotate(40) scale(1.04) translate(-32 -29.5)">
<rect x="29.5" y="2.5" width="5" height="33" rx="1.2" fill="#fff"/>
<rect x="27" y="0" width="10" height="8.5" rx="2.6" fill="#fff"/>
<path d="M32 22.5c5.2 0 6.7 7.6 11.4 13.8 3.9 5.1 4.3 9.8 2.2 13-2.5 3.8-7.3 5.9-13.6 5.9s-11.1-2.1-13.6-5.9c-2.100-3.200-1.700-7.900 2.200-13C25.300 30.100 26.800 22.500 32 22.500z" fill="#fff"/>
<circle cx="32" cy="45" r="4.2" fill="#2a52d6"/>
<g fill="url(#am)"><circle cx="24.6" cy="3.4" r="1.5"/><circle cx="24.6" cy="7" r="1.5"/><circle cx="39.4" cy="3.4" r="1.5"/><circle cx="39.4" cy="7" r="1.5"/></g>
<rect x="26.5" y="54" width="11" height="2.2" rx="1.1" fill="#2a52d6"/>
</g></svg>
'''

def B(rx=14):  # monogram
    return f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 64 64">{TILE(rx)}
<path fill="#fff" fill-rule="evenodd" d="M21 13h13.500a9.500 9.500 0 0 1 5.600 17.200A10.500 10.500 0 0 1 36.500 51H21zM29 20v8.500h5.200a4.250 4.250 0 0 0 0-8.500zM29 35v9h6.500a4.500 4.500 0 0 0 0-9z"/>
<circle cx="47.500" cy="16.500" r="4" fill="url(#am)"/>
</svg>
'''

def C(rx=14):  # amber plectrum / bouzouki face on navy
    return f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 64 64">{TILE(rx, "#1d2a52", "#0b1226")}
<path d="M32 8c10.500 0 18.500 5.200 18.500 14.500 0 12.500-12 29.500-18.500 33.500-6.500-4-18.500-21-18.500-33.500C13.500 13.200 21.500 8 32 8z" fill="url(#am)"/>
<path d="M32 8c10.500 0 18.500 5.200 18.500 14.500 0 5-1.800 10.500-4.400 15.500H17.900c-2.600-5-4.400-10.500-4.400-15.500C13.500 13.200 21.500 8 32 8z" fill="#10172e"/>
<circle cx="32" cy="27" r="6.500" fill="none" stroke="#f6efdc" stroke-width="2.600"/>
<path d="M17.900 38h28.200" stroke="#f6efdc" stroke-width="2"/>
</svg>
'''
if __name__ == "__main__":
    for name, fn in (("A", A), ("B", B), ("C", C)):
        open(f"{sys.argv[1]}/opt{name}.svg", "w").write(fn())
