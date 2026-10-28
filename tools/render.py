"""Render paulthery/aiostreams-badges as self-contained PNGs for Nuvio.

Nuvio draws only image badges, in a slot 16dp high (34-92dp wide), scaled
with ContentScale.Fit and clipped to a 6dp radius. There is no custom CSS,
so the frame, fill and corner radius are baked into each image.
"""
import json, re, sys
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

SRC = Path(sys.argv[1])          # aiostreams-badges checkout
OUT = Path(sys.argv[2])          # output folder
OUT.mkdir(parents=True, exist_ok=True)

H = 128                          # final height in px (8 px per dp)
SS = 4                           # supersampling
R = H * 6 / 16                   # Nuvio clips the slot at 6dp of 16dp
MIN_W = H * 34 / 16              # Nuvio's slot is never narrower than 34dp
BORDER = 6                       # ~0.75dp frame
FONT_DIR = Path('/usr/share/fonts/opentype/inter')

def font(weight, size):
    return ImageFont.truetype(str(FONT_DIR / f'Inter-{weight}.otf'), round(size))

def rgba(hex_, alpha=1.0):
    h = hex_.lstrip('#')
    return tuple(int(h[i:i+2], 16) for i in (0, 2, 4)) + (round(255 * alpha),)

def tracked_width(text, f, track):
    if not track:
        return f.getlength(text)
    return sum(f.getlength(c) for c in text) + track * (len(text) - 1)

def draw_text(draw, cx, baseline, text, f, fill, track=0.0):
    """Centre text on cx (ink of the glyph run, without trailing tracking)."""
    w = tracked_width(text, f, track)
    x = cx - w / 2
    if not track:
        draw.text((x, baseline), text, font=f, fill=fill, anchor='ls')
        return
    for c in text:
        draw.text((x, baseline), c, font=f, fill=fill, anchor='ls')
        x += f.getlength(c) + track

def rounded_mask(w, h, r):
    m = Image.new('L', (w, h), 0)
    ImageDraw.Draw(m).rounded_rectangle((0, 0, w - 1, h - 1), radius=r, fill=255)
    return m

def frame(img, colour, r, b):
    """Stroke drawn inside the rounded rect, like a CSS border."""
    w, h = img.size
    layer = Image.new('RGBA', (w, h), (0, 0, 0, 0))
    ImageDraw.Draw(layer).rounded_rectangle(
        (0, 0, w - 1, h - 1), radius=r, outline=rgba(colour), width=b)
    return Image.alpha_composite(img, layer)

def finish(big, path):
    w, h = big.size
    big.putalpha(Image.composite(big.getchannel('A'), Image.new('L', big.size, 0),
                                 rounded_mask(w, h, round(R * SS))))
    small = big.resize((round(w / SS), H), Image.LANCZOS)
    small.save(path, optimize=True)
    return small

# ---------------------------------------------------------------- text badge
TEXT_SIZE = 0.50 * H             # Inter SemiBold, about 8dp in the slot
TEXT_TRACK = 0.02                # em
PAD = 0.30 * H
CAP = 0.727                      # Inter cap height / em

def text_badge(label, color, border, background, path):
    f = font('SemiBold', TEXT_SIZE * SS)
    track = TEXT_TRACK * TEXT_SIZE * SS
    tw = tracked_width(label, f, track)
    w = max(round(tw + 2 * PAD * SS), round(MIN_W * SS))  # fill the slot, even gaps
    h = H * SS
    img = Image.new('RGBA', (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    if background:
        d.rounded_rectangle((0, 0, w - 1, h - 1), radius=R * SS, fill=rgba(background))
    baseline = h / 2 + CAP * TEXT_SIZE * SS / 2
    draw_text(d, w / 2, baseline, label, f, rgba(color), track)
    img = frame(img, border, R * SS, BORDER * SS)
    return finish(img, path)

# ------------------------------------------------------------ two-line badge
def svg_parts(svg_path):
    s = svg_path.read_text()
    texts = re.findall(r'>([^<]+)</text>', s)
    colour = re.search(r'<rect x="0" y="0"[^>]*fill="(#[0-9A-Fa-f]{6})"', s).group(1)
    return texts[0], texts[1], colour

def two_line_badge(svg_path, path):
    name, detail, colour = svg_parts(svg_path)
    u = H * SS / 41                       # one SVG unit, design is 81 x 41
    w, h = max(round(81 * u), round(MIN_W * SS)), H * SS
    img = Image.new('RGBA', (w, h), (0, 0, 0, 0))
    # top block, name knocked out
    block = Image.new('RGBA', (w, h), (0, 0, 0, 0))
    ImageDraw.Draw(block).rectangle((0, 0, w, round(25.375 * u)), fill=rgba(colour))
    knock = Image.new('L', (w, h), 255)
    draw_text(ImageDraw.Draw(knock), w / 2, 17.71 * u, name,
              font('Bold', 15 * u), 0, 0.2 * u)
    block.putalpha(Image.composite(block.getchannel('A'), Image.new('L', (w, h), 0), knock))
    img = Image.alpha_composite(img, block)
    # detail line
    d = ImageDraw.Draw(img)
    draw_text(d, w / 2, 36.16 * u, detail, font('Medium', 8 * u), rgba(colour, 0.85), 1.8 * u)
    img = frame(img, colour, R * SS, BORDER * SS)
    return finish(img, path)

if __name__ == '__main__':
    badges = json.loads((SRC / 'badges.json').read_text())['badges']
    made = []
    for b in badges:
        slug = re.sub(r'[^a-z0-9]+', '-', b['label'].lower().replace('+', 'plus')
                      .replace('&', 'and')).strip('-')
        if 'image' in b:
            m = re.search(r'/(codec|hdr)/([a-z0-9]+)\.png', b['image'])
            folder, stem = m.groups()
            svg = SRC / folder / f'{stem}.svg'
            slug = stem
            img = two_line_badge(svg, OUT / f'{slug}.png')
        else:
            img = text_badge(b['label'], b['color'], b['border'], b.get('background'),
                             OUT / f'{slug}.png')
        made.append({'label': b['label'], 'file': f'{slug}.png', 'size': img.size})
    (OUT.parent / 'manifest.json').write_text(json.dumps(made, indent=1))
    print(len(made), 'badges')
    dupes = {m['file'] for m in made if [x['file'] for x in made].count(m['file']) > 1}
    print('duplicate files:', dupes or 'none')
    print('aspect range:', min(m['size'][0] / H for m in made), max(m['size'][0] / H for m in made))
