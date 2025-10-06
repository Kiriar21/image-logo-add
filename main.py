# CREATED BY Artur from pema-IT
import os
import sys
import glob
import string
import datetime as dt
from typing import Tuple

import yaml
from PIL import Image, ImageOps
import piexif

def load_config(path: str = "config.yaml") -> dict:
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def ensure_dirs():
    os.makedirs("src", exist_ok=True)
    os.makedirs("out", exist_ok=True)
    os.makedirs("logo", exist_ok=True)


def parse_hex_color(s: str):
    s = s.strip().lstrip("#")
    if len(s) == 6:
        r = int(s[0:2], 16); g = int(s[2:4], 16); b = int(s[4:6], 16); a = 255
    elif len(s) == 8:
        r = int(s[0:2], 16); g = int(s[2:4], 16); b = int(s[4:6], 16); a = int(s[6:8], 16)
    else:
        raise ValueError("pad_color should be #RRGGBB or #RRGGBBAA")
    return (r, g, b, a)

def resize_to_canvas(img: Image.Image, size: Tuple[int, int], mode: str, pad_color: str) -> Image.Image:
    w, h = img.size
    tw, th = size
    mode = (mode or "none").lower()
    
    if mode == "none":
        return img

    if mode == "stretch":
        return img.resize((tw, th), Image.Resampling.LANCZOS)

    if mode == "cover":
        return ImageOps.fit(img, (tw, th), method=Image.Resampling.LANCZOS, centering=(0.5, 0.5))

    if mode == "fit_pad":
        scale = min(tw / w, th / h)
        nw, nh = max(1, int(w * scale)), max(1, int(h * scale))
        resized = img.resize((nw, nh), Image.Resampling.LANCZOS)
        bg = Image.new("RGBA", (tw, th), parse_hex_color(pad_color))
        x = (tw - nw) // 2
        y = (th - nh) // 2
        bg.alpha_composite(resized.convert("RGBA"), (x, y))
        return bg

    raise ValueError("resize_mode: use none | fit_pad | stretch | cover")


def compute_logo_xy(canvas_w: int, canvas_h: int, logo_w: int, logo_h: int, position: str, offset: int) -> Tuple[int, int]:
    position = position.lower().strip()
    if position not in {"left_top", "left_bottom", "right_top", "right_bottom"}:
        raise ValueError("Incorrect value for logo_position. Use: left_top | left_bottom | right_top | right_bottom")

    if position == "left_top":
        return offset, offset
    if position == "left_bottom":
        return offset, canvas_h - logo_h - offset
    if position == "right_top":
        return canvas_w - logo_w - offset, offset
    return canvas_w - logo_w - offset, canvas_h - logo_h - offset


def next_output_name(cfg: dict, counter: int) -> str:
    fn = cfg.get("filename", {}) or {}
    prefix = fn.get("prefix", "img")
    date_fmt = fn.get("date_format", "%Y%m%d")
    pad = int(fn.get("counter_padding", 2))
    today = dt.datetime.now().strftime(date_fmt)
    name = f"{prefix}_{today}_{str(counter).zfill(pad)}.jpg"
    return os.path.join("out", name)


def iter_source_images():
    patterns = ["*.jpg", "*.jpeg", "*.png", "*.webp", "*.bmp", "*.tif", "*.tiff"]
    files = []
    for p in patterns:
        files.extend(glob.glob(os.path.join("src", p)))
    return sorted(files)

def to_xp(s: str) -> bytes:
    return (s or "").encode("utf-16le")

def build_jpeg_exif(cfg: dict) -> bytes:
    md = cfg.get("metadata", {}) or {}
    now_dt = dt.datetime.now().strftime("%Y:%m:%d %H:%M:%S")
    today_iso = dt.datetime.now().strftime("%Y-%m-%d")
    
    author = md.get("author", "") or ""
    copyright_ = md.get("copyright", "") or ""
    software = md.get("software", "") or ""
    title = md.get("title", "") or ""
    subject = md.get("subject", "") or ""
    keywords = (md.get("keywords", "") or "").replace(",", ";")

    title_final = f"{title} {today_iso}".strip()    

    def to_xp(s: string) -> bytes:
        return (s or "").encode("utf-16le")

    zeroth = {
        piexif.ImageIFD.Software: software,
        piexif.ImageIFD.Artist: author,
        piexif.ImageIFD.Copyright: copyright_,
        piexif.ImageIFD.ImageDescription: title or subject,
        piexif.ImageIFD.XPTitle: to_xp(title_final),
        piexif.ImageIFD.XPSubject: to_xp(subject),
        piexif.ImageIFD.XPKeywords: to_xp(keywords),
        piexif.ImageIFD.XPAuthor: to_xp(author),
        piexif.ImageIFD.DateTime: now_dt,
    }

    exif_ifd = {
        piexif.ExifIFD.DateTimeOriginal: now_dt,
        piexif.ExifIFD.DateTimeDigitized: now_dt, 
    }

    exif_dict = {"0th": zeroth, "Exif": exif_ifd, "1st": {}, "GPS": {}, "Interop": {}}
    return piexif.dump(exif_dict)

def scale_logo_for_canvas(logo: Image.Image, canvas_w: int, canvas_h: int, max_ratio: float) -> tuple[Image.Image, float]:
    max_w = int(canvas_w * max_ratio)
    max_h = int(canvas_h * max_ratio)
    w, h = logo.size
    if w <= max_w and h <= max_h:
        return logo, 1.0
    scale = min(max_w / w, max_h / h)
    new_size = (max(1, int(w * scale)), max(1, int(h * scale)))
    return logo.resize(new_size, Image.Resampling.LANCZOS), scale


def main():
    ensure_dirs()
    cfg = load_config()
    exif_bytes = build_jpeg_exif(cfg)
    resize_mode = (cfg.get("resize_mode") or "fit_pad")
    pad_color = cfg.get("pad_color", "#00000000")
    out_w = int(cfg.get("output_width", 1920))
    out_h = int(cfg.get("output_height", 1080))
    logo_path = cfg.get("logo_path", "logo/logotype.png")
    logo_w = int(cfg.get("logo_width", 200))
    logo_h = int(cfg.get("logo_height", 200))
    logo_pos = cfg.get("logo_position", "right_bottom")
    logo_off = int(cfg.get("logo_offset", 50))
    max_logo_ratio = float(cfg.get("max_logo_ratio", 0.25))

    if not os.path.isfile(logo_path):
        print(f"[ERROR] Not found file with logo: {logo_path}", file=sys.stderr)
        sys.exit(1)
    logo_img = Image.open(logo_path).convert("RGBA").resize((logo_w, logo_h), Image.Resampling.LANCZOS)

    start_counter = int(cfg.get("filename", {}).get("start_counter", 1))
    counter = start_counter

    sources = iter_source_images()
    if not sources:
        print("[INFO] Not found any file in 'src/'. Add minimum 1 photo and try again.")
        return

    for src_path in sources:
        try:
            with Image.open(src_path) as im:
                base = im.convert("RGBA")

                if resize_mode != "none":
                    base = resize_to_canvas(base, (out_w, out_h), resize_mode, pad_color)

                cw, ch = base.size
                logo_use, scale = scale_logo_for_canvas(logo_img, cw, ch, max_logo_ratio)

                offset_eff = max(0, int(round(logo_off * scale)))
                x, y = compute_logo_xy(cw, ch, logo_use.width, logo_use.height, logo_pos, offset_eff)
                base.alpha_composite(logo_use, (x, y))


                out_path = next_output_name(cfg, counter)
                rgb = Image.new("RGB", base.size, (255, 255, 255))
                rgb.paste(base, mask=base.split()[-1])
                quality = int(cfg.get("jpeg_quality", 100))
                rgb.save(out_path, format="JPEG", quality=quality, optimize=True, subsampling=1, exif=exif_bytes)

                print(f"[OK] {src_path} -> {out_path}")
                counter += 1

        except Exception as e:
            print(f"[ERROR] {src_path}: {e}", file=sys.stderr)

    print(f"[READY] Covered {counter - start_counter} file(s).")


if __name__ == "__main__":
    main()
