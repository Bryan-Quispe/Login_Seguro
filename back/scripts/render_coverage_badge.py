from PIL import Image, ImageDraw, ImageFont
import sys

def render_coverage_badge(percent, out_path, width=900, height=200, bg=(255,255,255)):
    try:
        font_large = ImageFont.truetype('DejaVuSans.ttf', 36)
        font_small = ImageFont.truetype('DejaVuSans.ttf', 18)
    except Exception:
        font_large = ImageFont.load_default()
        font_small = ImageFont.load_default()

    img = Image.new('RGB', (width, height), color=bg)
    draw = ImageDraw.Draw(img)

    text = f'Cobertura: {percent:.2f}%'
    tw, th = draw.textsize(text, font=font_large)
    draw.text(((width-tw)/2, 20), text, font=font_large, fill=(0,0,0))

    # draw bar background
    bar_x0 = 100
    bar_x1 = width - 100
    bar_y0 = 100
    bar_y1 = 140
    draw.rectangle([bar_x0, bar_y0, bar_x1, bar_y1], fill=(230,230,230))

    # fill according to percent
    fill_x = bar_x0 + int((bar_x1-bar_x0) * (percent/100.0))
    draw.rectangle([bar_x0, bar_y0, fill_x, bar_y1], fill=(76,175,80))

    # percent text on bar
    pct_text = f'{percent:.2f}%'
    pw, ph = draw.textsize(pct_text, font=font_small)
    draw.text((bar_x1 - pw, bar_y0 - ph - 4), pct_text, font=font_small, fill=(0,0,0))

    img.save(out_path)
    print('Saved', out_path)

if __name__ == '__main__':
    if len(sys.argv) < 3:
        print('Usage: render_coverage_badge.py <percent> <out.png>')
        sys.exit(2)
    percent = float(sys.argv[1])
    render_coverage_badge(percent, sys.argv[2])
