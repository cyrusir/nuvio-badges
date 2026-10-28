"""Build the Nuvio badge JSON and the AIOStreams formatter that feeds it.

Nuvio runs each badge regex (java.util.regex / Kotlin Regex, find()) over
several strings per stream: the file name(s), stream name, description, and
all of them joined. Every matching badge is shown; there is no "first match
per group", so the order of a group is enforced with negative lookaheads.

Badges that need AIOStreams' parsed results (tiers, cached service,
languages) read invisible markers the formatter appends to the description.
"""
import json, sys
from pathlib import Path

BASE = sys.argv[1].rstrip('/') + '/'      # where icons/ will be hosted
OUT = Path(sys.argv[2])
SRC = Path(sys.argv[3])                   # aiostreams-badges checkout
VERSION = 1

# ------------------------------------------------------------------ markers
P, A, B, C = '⁠', '​', '‌', '‍'
MARK = {
    'ANY': P + A + A + A,
    'T1': P + A + A + B, 'T2': P + A + A + C, 'T3': P + A + B + A, 'LQ': P + A + B + B,
    'RD': P + A + B + C, 'TB': P + A + C + A, 'AD': P + A + C + B, 'EN': P + A + C + C,
    'FR': P + B + A + A, 'MULTI': P + B + A + B, 'ENG': P + B + A + C,
}
def rx(name):          # marker as a regex, written with \u escapes
    return ''.join(f'\\u{ord(c):04x}' for c in MARK[name])

FILETOK = r'(?:\b(?:2160p|1440p|1080[pi]|720p|576p|480p)\b|\.(?:mkv|mp4|avi|m2ts|m4v|webm|ts)\b)'
# true only on the joined string: it alone carries both the file name and
# the formatter's markers, so cross-source exclusions can be checked there
JOINED = f'(?=.*{rx("ANY")})(?=.*{FILETOK})'
DV = r'\b(?:dv|dovi|dolby[ ._-]?vision)\b'
NOT_SIZE = r'(?![0-9])(?![ ._]?[kmgt]i?b\b)'   # "7.1 GB" in the description

# ------------------------------------------------- badges, in display order
# body: regex applied from the start of a candidate (DOTALL, case-insensitive)
def core(r):
    return f'.*(?:{r})'

G = []   # (group, label, body)
def group(gid, items, prefix=''):
    """Ordered group: each badge excludes the ones above it."""
    bodies = []
    for label, body in items:
        excl = ''.join(f'(?!{b})' for b in bodies)
        G.append((gid, label, prefix + excl + body))
        bodies.append(body)

group('tier', [('T1', core(rx('T1'))), ('T2', core(rx('T2'))), ('T3', core(rx('T3')))])
group('lq', [('LQ', core(rx('LQ')))])
group('res', [('4K', core(r'\b(?:2160p|4k)\b')),
              ('1080', core(r'\b1080[pi]\b')),
              ('720', core(r'\b720p\b'))])
group('src', [('REMUX', core(r'\bremux\b')),
              ('BLURAY', core(r'\bblu-?ray\b')),
              ('WEB-DL', core(r'\bweb[ ._-]?dl\b|\bweb\b(?![ ._-]?(?:rip|dl)\b)')),
              ('WEBRIP', core(r'\bweb[ ._-]?rip\b'))])
group('hdr', [('HDR+DV', f'(?=.*{DV})(?=.*\\bhdr)'),
              ('HDR10+', core(r'\bhdr10(?:\+|p\b|plus\b)')),
              ('HDR', core(r'\bhdr(?:10)?\b')),
              ('DV', core(DV)),
              ('HLG', core(r'\bhlg\b'))])
G.append(('hdr', 'SDR', f'(?=.*{FILETOK})(?!.*(?:hdr|{DV}|hlg))'))
group('imax', [('IMAX', core(r'\bimax\b'))])
group('audio', [('ATMOS', core(r'\batmos\b')),
                ('DTS:X', core(r'\bdts[ ._:-]?x\b')),
                ('TRUEHD', core(r'\btrue[ ._-]?hd\b')),
                ('DTS-HD MA', core(r'\bdts[ ._-]?hd[ ._-]?ma\b')),
                ('DD+', core(r'\b(?:ddp|dd\+|e-?ac-?3)(?![a-z])'))])
group('ch', [('7.1', core(r'(?<![0-9])7[ ._]1' + NOT_SIZE)),
             ('5.1', core(r'(?<![0-9])5[ ._]1' + NOT_SIZE))])
group('enc', [('HEVC', core(r'\b(?:hevc|[hx][ .]?265)\b')),
              ('AV1', core(r'\bav1\b')),
              ('H.264', core(r'\b(?:avc|[hx][ .]?264)\b')),
              ('VP9', core(r'\bvp9\b'))])
group('bit', [('10BIT', core(r'\b10[ ._-]?bit\b'))])
VFF, VFQ = core(r'\b(?:truefrench|vff|vf2)\b'), core(r'\b(?:vfq|vq)\b')
group('fr', [('VFF', VFF), ('VFQ', VFQ)])
G.append(('fr', 'VF', JOINED + f'(?!{VFF})(?!{VFQ})' + core(rx('FR'))))
G.append(('fr', 'VOSTFR', f'(?!{VFF})(?!{VFQ})' + core(r'\b(?:vost(?:fr)?|subfrench)\b')))
VFVO = core(f'{rx("MULTI")}|\\bmulti\\b|\\bdual[ ._-]?audio\\b')
G.append(('lang', 'VF+VO', VFVO))
G.append(('lang', 'VO', JOINED + f'(?!{VFVO})' + core(rx('ENG'))))
group('ed', [
    ('FINAL CUT', r'(?!(?:the\W+)?final\W+cut\W+(?:19|20)\d\d).*\bfinal[ ._-]?cut\b'),
    ('DIR CUT', core(r"\bdirector'?s?[ ._-]?cut\b")),
    ('REDUX', core(r'\bredux\b')),
    ('ROGUE CUT', core(r'\brogue[ ._-]?cut\b')),
    ('ULTIMATE', core(r'\bultimate[ ._-]?(?:cut|edition)\b')),
    ('EXTENDED', core(r'\bextended\b|\bversion[ ._-]?longue\b')),
    ('ROADSHOW', core(r'\broadshow\b')),
    ('UNRATED', core(r'\bunrated\b')),
    ('UNCUT', core(r'\buncut\b(?![ ._-]*gems)|\bversion[ ._-]?int[eé]grale\b')),
    ('UNCENSORED', core(r'\buncensored\b')),
    ('DEFINITIVE', core(r'\bdefinitive[ ._-]?(?:cut|edition)\b')),
    ('SPECIAL ED', core(r'\bspecial[ ._-]?edition\b')),
    ('INTL CUT', core(r'\binternational[ ._-]?(?:cut|version)\b')),
    ('ALT CUT', core(r'\balternat(?:e|ive)[ ._-]?(?:cut|version)\b')),
    ('ASSEMBLY', core(r'\bassembly[ ._-]?cut\b')),
    ('PRODUCER CUT', core(r"\bproducers?'?[ ._-]?cut\b")),
    ('WORKPRINT', core(r'\bworkprint\b')),
    ('TV CUT', core(r'\b(?:tv|television)[ ._-]?(?:cut|version)\b')),
    ('B&W', core(r'black[ ._-]?(?:and|&)[ ._-]?(?:chrome|white)|\bnoir[ ._-]?(?:edition|version)\b')),
    ('DESPECIALIZED', core(r'\bdespeciali[sz]ed\b')),
    ('ANNIVERSARY', core(r'\banniversary[ ._-]?edition\b')),
    ('COLLECTOR', core(r"\bcollector'?s?[ ._-]?edition\b")),
    ('DIAMOND', core(r'\bdiamond[ ._-]?edition\b')),
    ('PLATINUM', core(r'\bplatinum[ ._-]?edition\b')),
    ('THEATRICAL', core(r'\btheatrical\b')),
])
group('rem', [('REMASTERED', core(r'\bremaster(?:ed)?\b|\brestor(?:ed|ation)\b'))])
group('crit', [('CRITERION', core(r'\bcriterion\b'))])
group('matte', [('OPEN MATTE', core(r'open[ ._-]?matte'))])
group('proper', [('PROPER', core(r'\b(?:repack|proper|rerip)\d?\b'))])
group('pack', [('PACK', core(r'\bS\d{1,2}\b(?![ ._-]?E\d)|\bcomplete\b|\bint[eé]grale?\b'))])
group('svc', [('RD', core(rx('RD'))), ('TB', core(rx('TB'))),
              ('AD', core(rx('AD'))), ('EN', core(rx('EN')))])

GROUP_NAMES = {
    'tier': 'Tier', 'lq': 'Low quality', 'res': 'Resolution', 'src': 'Source',
    'hdr': 'Dynamic range', 'imax': 'IMAX', 'audio': 'Audio', 'ch': 'Channels',
    'enc': 'Codec', 'bit': 'Bit depth', 'fr': 'French', 'lang': 'Language',
    'ed': 'Edition', 'rem': 'Remastered', 'crit': 'Criterion', 'matte': 'Open matte',
    'proper': 'Proper', 'pack': 'Pack', 'svc': 'Cached service',
}

def build():
    manifest = {m['label']: m['file'] for m in json.loads((OUT / 'manifest.json').read_text())}
    labels = [g[1] for g in G]
    assert sorted(labels) == sorted(manifest), set(labels) ^ set(manifest)
    groups, seen = [], []
    for gid, *_ in G:
        if gid not in seen:
            seen.append(gid)
            groups.append({'id': gid, 'name': GROUP_NAMES[gid], 'color': '#FFC6A56B',
                           'isExpanded': True})
    filters = []
    for gid, label, body in G:
        f = manifest[label]
        filters.append({
            'id': 'pt-' + f[:-4], 'groupId': gid, 'type': 'filter', 'name': label,
            'pattern': '(?is)^' + body,
            'imageURL': f'{BASE}icons/{f}?v={VERSION}',
            'isEnabled': True, 'tagColor': '#00000000', 'tagStyle': 'filled',
            'textColor': '#FFFFFFFF', 'borderColor': '#00000000',
        })
    (OUT / 'nuvio-badges.json').write_text(
        json.dumps({'groups': groups, 'filters': filters}, indent=2, ensure_ascii=True) + '\n')
    return filters

# --------------------------------------------------------------- formatter
def formatter():
    m = MARK
    rse = lambda key, mk: f'{{stream.rseMatched::join::~{key}["{m[mk]}"||""]}}'
    lang = lambda key, mk: f'{{stream.languages::~{key}["{m[mk]}"||""]}}'
    svc = ''.join(f'{{service.shortName::={s.lower()}["{m[s]}"||""]}}' for s in ('RD', 'TB', 'AD', 'EN'))
    block = (m['ANY']
             + rse('t1', 'T1') + rse('t2', 'T2') + rse('t3', 'T3')
             + rse('lq', 'LQ') + rse('upscaled', 'LQ') + rse('fr fastsub', 'LQ')
             + f'{{service.cached::istrue["{svc}"||""]}}'
             + lang('french', 'FR') + lang('multi', 'MULTI') + lang('dual audio', 'MULTI')
             + lang('english', 'ENG') + lang('original', 'ENG'))
    desc = (SRC / 'formatter' / 'description.txt').read_text().rstrip('\n')
    (OUT / 'formatter').mkdir(exist_ok=True)
    (OUT / 'formatter' / 'description-nuvio.txt').write_text(desc + block)
    for f in ('name.txt', 'name-alt.txt'):
        (OUT / 'formatter' / f).write_text((SRC / 'formatter' / f).read_text())
    return desc + block

if __name__ == '__main__':
    fl = build()
    formatter()
    print(len(fl), 'filters,', len({f['groupId'] for f in fl}), 'groups')
    print('longest pattern:', max(len(f['pattern']) for f in fl))
