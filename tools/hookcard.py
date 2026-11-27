#!/usr/bin/env python3
"""Usage: hookcard.py in.mp4 out.mp4 "WHY DOES LIGHTNING HAVE A DELAY?"
Puts a big question on screen from 0.1 s to 2.5 s (fade out), and uses the same frame (frame at 1.0 s + question) as the
cover for t<0.1 s, so Instagram/Facebook covers and the first frame carry the question. Audio untouched."""
import sys, os, subprocess, textwrap
from PIL import Image, ImageDraw, ImageFont, ImageFilter
src, out, q = sys.argv[1], sys.argv[2], sys.argv[3].upper().strip()
W, H = 1080, 1920
font_path = next(f for f in ['/usr/share/fonts/truetype/google-fonts/Poppins-ExtraBold.ttf','/usr/share/fonts/truetype/google-fonts/Poppins-Bold.ttf','/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf'] if os.path.exists(f))
size = 112
while True:
    f = ImageFont.truetype(font_path, size)
    lines = []; cur = ''
    for w in q.split():
        t = (cur+' '+w).strip()
        if f.getlength(t) <= 900: cur = t
        else: lines.append(cur); cur = w
    lines.append(cur)
    if len(lines) <= 4 or size < 70: break
    size -= 6
lh = int(size*1.18); th = lh*len(lines); top = 200
im = Image.new('RGBA', (W, H), (0,0,0,0)); d = ImageDraw.Draw(im)
pad = 40; bw = int(max(f.getlength(l) for l in lines)) + 2*pad
x0 = (W-bw)//2
sh = Image.new('RGBA', (W, H), (0,0,0,0)); ImageDraw.Draw(sh).rounded_rectangle([x0, top-pad+12, x0+bw, top+th+pad+12], 48, fill=(0,0,0,120))
im.alpha_composite(sh.filter(ImageFilter.GaussianBlur(12)))
d.rounded_rectangle([x0, top-pad, x0+bw, top+th+pad], 48, fill=(22,24,74,235))
for i, l in enumerate(lines):
    y = top + i*lh + lh//2
    col = (255,210,63,255) if i == len(lines)-1 else (255,255,255,255)
    d.text((W//2, y), l, font=f, fill=col, anchor='mm')
png = '/tmp/hook_overlay.png'; im.save(png)
subprocess.check_call(['ffmpeg','-loglevel','error','-y','-ss','1.0','-i',src,'-frames:v','1','/tmp/hook_base.png'])
cov = Image.open('/tmp/hook_base.png').convert('RGBA').resize((W,H)); cov.alpha_composite(im); cov.convert('RGB').save('/tmp/hook_cover.png')
fc = ("[1:v]format=rgba,fade=t=out:st=2.1:d=0.4:alpha=1[o];[0:v][o]overlay=0:0:enable='between(t,0.1,2.5)'[a];"
      "[a][2:v]overlay=0:0:enable='lt(t,0.1)'[v]")
subprocess.check_call(['ffmpeg','-loglevel','error','-y','-i',src,'-loop','1','-i',png,'-loop','1','-i','/tmp/hook_cover.png','-filter_complex',fc,
  '-map','[v]','-map','0:a','-c:v','libx264','-preset','veryfast','-crf','22','-pix_fmt','yuv420p','-c:a','copy','-movflags','+faststart','-shortest',out])
print(out)
