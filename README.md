# image-batch — simple photo batcher with logo + EXIF

Reads images from `src/`, optionally resizes, overlays a logo, writes JPEGs with EXIF to `out/`. Filenames use a prefix, date, and counter.

## Project layout
```
image-batch/
├─ main.py
├─ config.yaml
├─ requirements.txt
├─ src/          # input images
├─ out/          # output JPEGs
└─ logo/
   └─ logotype.png
```

## Requirements
- Python 3.10+
- Windows/macOS/Linux

`requirements.txt`
```
Pillow>=10.4.0
PyYAML>=6.0.2
piexif>=1.1.3
```

## Setup
```bash
python -m venv .venv
# Windows
.venv\Scripts\pip install -r requirements.txt
# macOS/Linux
.venv/bin/pip install -r requirements.txt
```

## Configuration (`config.yaml` example)
```yaml
# Target size for modes other than "none"
output_width: 1920
output_height: 1080

# Image resize mode: none | fit_pad | stretch | cover
resize_mode: "fit_pad"

# Pad color for fit_pad; #RRGGBB or #RRGGBBAA (AA = alpha)
pad_color: "#00000000"   # transparent; will be flattened to white in JPEG

# Logo
logo_path: "logo/logotype.png"
logo_width: 200           # preferred logo size
logo_height: 200
logo_position: "right_bottom"   # left_top | left_bottom | right_top | right_bottom
logo_offset: 50                   # px from edges
max_logo_ratio: 0.25              # auto-downscale so logo ≤ 25% of image width/height

# EXIF metadata (visible in Windows Explorer)
metadata:
  author: "name-company"
  copyright: "name-company"
  software: "name-program"
  title: "Images title"          # YYYY-MM-DD is appended automatically
  subject: "Images subject"
  keywords: "tag1, tag2, tag3"   # commas become semicolons for Windows

# Output filenames
filename:
  prefix: "prefix"
  date_format: "%Y-%m-%d"   # date in filename
  start_counter: 1
  counter_padding: 2        # 01, 02, ...

# JPEG quality
jpeg_quality: 92
```

## Run
1. Put input images into `src/`.
2. Place your logo at `logo/logotype.png`.
3. Execute:
```bash
# Windows
.venv\Scripts\python main.py
# macOS/Linux
.venv/bin/python main.py
```

## How it works
- **Inputs:** `jpg`, `jpeg`, `png`, `webp`, `bmp`, `tif`, `tiff`
- **Output:** always **JPEG** with EXIF
- **Resize modes:**
  - `none` — no resize; keep original size
  - `fit_pad` — keep aspect, center, pad to target with `pad_color`
  - `stretch` — force to `output_width × output_height`
  - `cover` — fill target; crops overflow
- **Logo:**
  - Loaded with transparency.
  - First resized to `logo_width × logo_height`.
  - Then auto-downscaled if it exceeds `max_logo_ratio` of the image (both width and height limits).
  - The **offset** scales proportionally when the logo is auto-downscaled.
- **EXIF written:**
  - `Artist`, `Copyright`, `Software`, `XPTitle` (title + date `YYYY-MM-DD`), `DateTime`, `DateTimeOriginal`, `DateTimeDigitized`
- **Filenames:** `prefix_{date}_{counter}.jpg` using `filename` settings.

## Notes
- JPEG does not support alpha. The final image is flattened to a solid background (white by default). To change it, edit `rgb = Image.new("RGB", base.size, (R, G, B))` in `main.py`.
- Windows Explorer shows EXIF on JPEG. It ignores PNG text chunks.
- With `fit_pad` + transparent `pad_color`, the final JPEG still becomes opaque.

## Troubleshooting
- **`Not found file with logo`**: check `logo_path`.
- **No outputs**: add at least one image to `src/`.
- **Quality issues**: increase `jpeg_quality`, or choose an appropriate resize mode (`cover` vs `fit_pad`).

## License
Internal use is fine. Keep the header `# CREATED BY Artur from pema-IT` in `main.py` if you wish to retain attribution.
