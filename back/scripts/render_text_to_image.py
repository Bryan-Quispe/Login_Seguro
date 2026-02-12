from PIL import Image, ImageDraw, ImageFont
import sys

def render_text_file_to_png(txt_path, out_path, width=1200, padding=20, bg=(255,255,255), fg=(0,0,0)):
    with open(txt_path, 'r', encoding='utf-8', errors='ignore') as f:
        lines = f.read().splitlines()

    try:
        font = ImageFont.truetype('DejaVuSansMono.ttf', 14)
    except Exception:
        font = ImageFont.load_default()

    # compute height
    max_line_width = 0
    line_heights = []
    draw = ImageDraw.Draw(Image.new('RGB', (10,10)))
    for line in lines:
        w,h = draw.textsize(line, font=font)
        max_line_width = max(max_line_width, w)
        line_heights.append(h)

    img_w = min(width, max_line_width + 2*padding)
    img_h = padding*2 + sum(line_heights) + len(lines)*2
    img = Image.new('RGB', (img_w, img_h), color=bg)
    draw = ImageDraw.Draw(img)

    y = padding
    for line in lines:
        draw.text((padding, y), line, font=font, fill=fg)
        y += font.getsize(line)[1] + 2

    img.save(out_path)

if __name__ == '__main__':
    if len(sys.argv) < 3:
        print('Usage: render_text_to_image.py <input.txt> <output.png>')
        sys.exit(2)
    render_text_file_to_png(sys.argv[1], sys.argv[2])
    print('Saved', sys.argv[2])
