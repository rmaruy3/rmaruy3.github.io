"""
generate_ogp.py — デフォルトOGP画像 (assets/images/ogp-default.png, 1200x630) を生成

使い方:
  pip install pillow
  python scripts/generate_ogp.py

レイアウト:
  Ryuichi Maruyama       ← 黒・太字
  Metascience Communicator  ← 赤・イタリック（LPのタグラインと同じスタイル）
  rmaruy3.github.io      ← グレー・小
"""

from PIL import Image, ImageDraw, ImageFont

W, H = 1200, 630
BG, FG, GRAY, ACCENT = "#ffffff", "#0d0d0d", "#999999", "#cc2b2b"


def load_font(size, style="bold"):
    candidates = {
        "bold": [
            "C:/Windows/Fonts/segoeuib.ttf",   # Segoe UI Bold (Windows)
            "C:/Windows/Fonts/arialbd.ttf",
            "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
        ],
        "italic": [
            "C:/Windows/Fonts/segoeuii.ttf",   # Segoe UI Italic (Windows)
            "C:/Windows/Fonts/ariali.ttf",
            "/usr/share/fonts/truetype/dejavu/DejaVuSans-Oblique.ttf",
        ],
        "regular": [
            "C:/Windows/Fonts/segoeui.ttf",    # Segoe UI (Windows)
            "C:/Windows/Fonts/arial.ttf",
            "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        ],
    }
    for path in candidates[style]:
        try:
            return ImageFont.truetype(path, size)
        except OSError:
            continue
    raise SystemExit("フォントが見つかりませんでした。candidates を編集してください。")


def draw_centered(d, text, y, font, fill):
    w = d.textlength(text, font=font)
    d.text(((W - w) / 2, y), text, font=font, fill=fill)


def main():
    img = Image.new("RGB", (W, H), BG)
    d = ImageDraw.Draw(img)

    # 角丸の枠線（LPのカード風）
    d.rounded_rectangle([40, 40, W - 40, H - 40], radius=24, outline=FG, width=4)

    # 名前（黒・太字）
    draw_centered(d, "Ryuichi Maruyama", 200, load_font(92, "bold"), FG)

    # 肩書き（赤・イタリック）
    draw_centered(d, "Metascience Communicator", 350, load_font(44, "italic"), ACCENT)

    # URL（グレー・小）
    draw_centered(d, "rmaruy3.github.io", 480, load_font(30, "regular"), GRAY)

    out = "assets/images/ogp-default.png"
    img.save(out)
    print("saved:", out)


if __name__ == "__main__":
    main()
