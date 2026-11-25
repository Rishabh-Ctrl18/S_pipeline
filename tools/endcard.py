#!/usr/bin/env python3
"""Usage: endcard.py in.mp4 outdir basename
Writes outdir/basename-yt.mp4, -ig.mp4, -fb.mp4: the video with a 'Follow for more' pill in the last
N seconds plus a pulsing heart just below each app's like button (positions in endcard.json)."""
import sys, json, math, os, subprocess
from PIL import Image, ImageDraw, ImageFont, ImageFilter
src, outdir, base = sys.argv[1:4]
cfg = json.load(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'endcard.json')))
W, H = 1080, 1920
dur = float(subprocess.check_output(['ffprobe','-v','error','-show_entries','format=duration','-of','csv=p=0',src]).decode().strip())
secs = cfg['seconds']; t0 = max(0.5, dur - secs)
fonts = ['/usr/share/fonts/truetype/google-fonts/Poppins-Bold.ttf','/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf']
font_path = next(f for f in fonts if os.path.exists(f))

def heart(d, cx, cy, s, fill):
    pts = []
    for i in range(0, 360, 4):
        t = math.radians(i)
        x = 16*math.sin(t)**3
        y = 13*math.cos(t)-5*math.cos(2*t)-2*math.cos(3*t)-math.cos(4*t)
        pts.append((cx + x*s, cy - y*s))
    d.polygon(pts, fill=fill)

def card(platform):
    hx, hy = cfg[platform]['heart']; py = cfg[platform]['pill_y']
    im = Image.new('RGBA', (W, H), (0,0,0,0))
    # pill
    f = ImageFont.truetype(font_path, 78)
    text = 'Follow for more'
    tw = f.getlength(text); pw, ph = int(tw+230), 150
    x0 = (W-pw)//2
    sh = Image.new('RGBA', (W, H), (0,0,0,0)); sd = ImageDraw.Draw(sh)
    sd.rounded_rectangle([x0, py+10, x0+pw, py+ph+10], radius=75, fill=(0,0,0,110))
    im.alpha_composite(sh.filter(ImageFilter.GaussianBlur(10)))
    d = ImageDraw.Draw(im)
    d.rounded_rectangle([x0, py, x0+pw, py+ph], radius=75, fill=(255,210,63,255))
    d.text((x0+70, py+ph//2), text, font=f, fill=(22,24,74,255), anchor='lm')
    heart(d, x0+pw-75, py+ph//2+2, 2.3, (230,57,70,255))
    # little heart under the like button
    sh2 = Image.new('RGBA', (W, H), (0,0,0,0)); heart(ImageDraw.Draw(sh2), hx, hy+4, 3.0, (0,0,0,120))
    im.alpha_composite(sh2.filter(ImageFilter.GaussianBlur(4)))
    heart(d, hx, hy, 3.0, (255,255,255,255)); heart(d, hx, hy, 2.3, (230,57,70,255))
    return im

tags = {'youtube':'yt','instagram':'ig','facebook':'fb'}
os.makedirs(outdir, exist_ok=True)
for p, tag in tags.items():
    png = os.path.join('/tmp', f'endcard_{tag}.png'); card(p).save(png)
    out = os.path.join(outdir, f'{base}-{tag}.mp4')
    # fade the card in over 0.35 s starting at t0; heart pulses by fading the whole card alpha gently is unnecessary
    fc = f"[1:v]format=rgba,fade=t=in:st={t0:.2f}:d=0.35:alpha=1[c];[0:v][c]overlay=0:0:enable='gte(t,{t0:.2f})'[v]"
    subprocess.check_call(['ffmpeg','-loglevel','error','-y','-i',src,'-loop','1','-i',png,'-filter_complex',fc,
        '-map','[v]','-map','0:a','-c:v','libx264','-preset','veryfast','-crf','24','-pix_fmt','yuv420p','-c:a','copy',
        '-movflags','+faststart','-shortest',out])
    print(out, os.path.getsize(out))
