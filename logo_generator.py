"""Generate MCLauncher logo and assets"""
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageOps
import os
import math
from pathlib import Path


def create_logo(size=512):
    img = Image.new('RGBA', (size, size), (0, 0, 0, 0))
    center = size // 2
    draw = ImageDraw.Draw(img)

    # Background glow
    for i in range(60, 0, -1):
        alpha = int(15 * (1 - i / 60))
        r = int(center * 0.85 * (i / 60))
        draw.ellipse([
            center - r, center - r, center + r, center + r
        ], fill=(30, 180, 255, alpha))

    # Outer ring
    ring_colors = [(0, 180, 255), (0, 230, 118), (255, 200, 0)]
    for idx, color in enumerate(ring_colors):
        offset = idx * 15
        for a in range(0, 360, 2):
            rad = math.radians(a + offset)
            r1 = int(center * 0.82)
            r2 = int(center * 0.75)
            x1 = center + int(r1 * math.cos(rad))
            y1 = center + int(r1 * math.sin(rad))
            x2 = center + int(r2 * math.cos(rad))
            y2 = center + int(r2 * math.sin(rad))
            alpha = max(30, 80 - abs(a - 180) // 3)
            draw.line([(x1, y1), (x2, y2)], fill=(*color, alpha), width=3)

    # Pickaxe icon
    px, py = center, center - 10
    # Pickaxe head
    head_points = [
        (px - 60, py + 40), (px - 20, py - 50), (px, py - 55),
        (px + 20, py - 50), (px + 60, py + 40), (px + 30, py + 45),
        (px + 10, py + 10), (px - 10, py + 10), (px - 30, py + 45),
    ]
    draw.polygon(head_points, fill=(60, 70, 80), outline=(100, 120, 140), width=2)
    # Pickaxe handle (angled)
    handle_points = [
        (px - 18, py + 35), (px - 15, py + 35),
        (px + 40, py + 120), (px + 35, py + 122),
    ]
    draw.polygon(handle_points, fill=(80, 60, 40), outline=(120, 100, 70), width=1)

    # Minecraft grass block style cube (bottom right)
    cube_size = int(center * 0.35)
    cx, cy = center + int(center * 0.35), center + int(center * 0.3)
    # Top face (green)
    top = [
        (cx, cy - cube_size),
        (cx + cube_size, cy - cube_size - cube_size//3),
        (cx + cube_size*2, cy - cube_size),
        (cx + cube_size, cy - cube_size//3),
    ]
    draw.polygon(top, fill=(80, 180, 80), outline=(100, 220, 100), width=2)
    # Left face
    left = [
        (cx, cy - cube_size),
        (cx, cy),
        (cx + cube_size, cy - cube_size//3),
        (cx + cube_size, cy - cube_size - cube_size//3),
    ]
    draw.polygon(left, fill=(60, 140, 60), outline=(80, 180, 80), width=2)
    # Right face  
    right = [
        (cx + cube_size, cy - cube_size - cube_size//3),
        (cx + cube_size, cy - cube_size//3),
        (cx + cube_size*2, cy - cube_size),
        (cx + cube_size*2, cy - cube_size*2 - cube_size//3),
    ]
    draw.polygon(right, fill=(50, 120, 50), outline=(70, 160, 70), width=2)

    # Stars sparkle effect
    for _ in range(30):
        sx = int(math.cos(_ * 137.5) * center * 0.7) + center
        sy = int(math.sin(_ * 137.5) * center * 0.7) + center
        sz = max(1, int(4 * abs(math.sin(_ * 0.5))))
        draw.ellipse([sx-sz, sy-sz, sx+sz, sy+sz], fill=(255, 255, 255, 180))

    # Glow filter
    glow = img.filter(ImageFilter.GaussianBlur(radius=8))
    img = Image.blend(img, glow, 0.3)

    return img


def create_splash_bg(width=1920, height=600):
    img = Image.new('RGBA', (width, height), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    
    # Gradient background
    for y in range(height):
        t = y / height
        r = int(10 + 15 * t)
        g = int(15 + 25 * t)
        b = int(40 + 55 * t)
        draw.line([(0, y), (width, y)], fill=(r, g, b, 200))

    # Accent lines
    colors = [(0, 180, 255, 60), (0, 230, 118, 40), (255, 200, 0, 30)]
    for idx, color in enumerate(colors):
        y_base = height // 4 * (idx + 1)
        for x in range(0, width, 3):
            y = y_base + int(20 * math.sin(x * 0.01 + idx * 2))
            draw.point((x, y), fill=color)

    return img


def create_robot_avatar(size=128):
    """Create a cute robot assistant avatar"""
    img = Image.new('RGBA', (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    c = size // 2
    s = size // 2 - 5

    # Body
    draw.rounded_rectangle([c-s, c-s//2, c+s, c+s], radius=12, fill=(0, 150, 200, 220))
    # Head
    draw.rounded_rectangle([c-s//2, c-s-10, c+s//2, c-s//2+5], radius=8, fill=(0, 180, 230, 230))
    # Eyes
    eye_y = c - s//2 - 2
    draw.ellipse([c-10, eye_y-6, c-2, eye_y+2], fill=(255, 255, 255, 230))
    draw.ellipse([c+2, eye_y-6, c+10, eye_y+2], fill=(255, 255, 255, 230))
    draw.ellipse([c-8, eye_y-4, c-4, eye_y], fill=(0, 0, 0, 200))
    draw.ellipse([c+4, eye_y-4, c+8, eye_y], fill=(0, 0, 0, 200))
    # Antenna
    draw.line([(c, c-s-10), (c, c-s-18)], fill=(0, 180, 230, 220), width=3)
    draw.ellipse([c-4, c-s-22, c+4, c-s-14], fill=(255, 200, 0, 220))
    # Mouth
    draw.rounded_rectangle([c-8, c-s//2+8, c+8, c-s//2+12], radius=2, fill=(100, 220, 255, 200))
    # Arms
    draw.rounded_rectangle([c-s-8, c-s//2+10, c-s-2, c+s//2], radius=4, fill=(0, 130, 180, 200))
    draw.rounded_rectangle([c+s+2, c-s//2+10, c+s+8, c+s//2], radius=4, fill=(0, 130, 180, 200))

    return img


def generate_all_assets(output_dir):
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    print("Generating logo...")
    logo = create_logo(512)
    logo.save(output_dir / 'logo.png')
    logo.thumbnail((256, 256), Image.LANCZOS)
    logo.save(output_dir / 'logo_256.png')
    logo.thumbnail((64, 64), Image.LANCZOS)
    logo.save(output_dir / 'logo_64.png')

    print("Generating splash background...")
    splash = create_splash_bg(1920, 600)
    splash.save(output_dir / 'splash_bg.png')
    splash.thumbnail((1200, 400), Image.LANCZOS)
    splash.save(output_dir / 'splash_bg_thumb.png')

    print("Generating robot avatar...")
    robot = create_robot_avatar(128)
    robot.save(output_dir / 'robot.png')
    robot.thumbnail((64, 64), Image.LANCZOS)
    robot.save(output_dir / 'robot_64.png')

    print(f"All assets generated in {output_dir}")


if __name__ == '__main__':
    generate_all_assets('D:\\minecraft cllent\\assets')
