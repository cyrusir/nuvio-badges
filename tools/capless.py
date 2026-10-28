import sys, re
from pathlib import Path
sys.argv=['x','/home/claude/aiostreams-badges','/tmp/unused']
import importlib.util
spec=importlib.util.spec_from_file_location('r','render.py'); r=importlib.util.module_from_spec(spec); spec.loader.exec_module(r)
from PIL import Image, ImageDraw
SRC=Path('/home/claude/aiostreams-badges'); OUT=Path('capless'); OUT.mkdir(exist_ok=True)
def capless(svg, path):
    name, detail, colour = r.svg_parts(svg)
    SS,H=r.SS,r.H
    f=r.font('Bold', r.TEXT_SIZE*SS); tr=r.TEXT_TRACK*r.TEXT_SIZE*SS
    w=max(round(r.tracked_width(name,f,tr)+2*r.PAD*SS), round(r.MIN_W*SS)); h=H*SS
    block=Image.new('RGBA',(w,h),r.rgba(colour))
    knock=Image.new('L',(w,h),255)
    r.draw_text(ImageDraw.Draw(knock), w/2, h/2+r.CAP*r.TEXT_SIZE*SS/2, name, f, 0, tr)
    block.putalpha(knock)
    return r.finish(block, path)
for svg in sorted(list((SRC/'codec').glob('*.svg'))+list((SRC/'hdr').glob('*.svg'))):
    capless(svg, OUT/f'{svg.stem}.png')
