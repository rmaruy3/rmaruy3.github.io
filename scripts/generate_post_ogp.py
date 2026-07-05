"""
generate_post_ogp.py — 各記事（ブログ・noteアーカイブ）のOGP画像を設定する

動作:
  _posts/*.md と _note/*.md を全記事スキャンし、front matter に image: が無い記事について
    1. 本文に画像がある記事 → 最初の画像を og:image に使う（front matter に image: を追記）
    2. 画像が無い記事       → タイトルカードPNG（B-2デザイン）を生成して設定
       出力先: assets/images/ogp/<記事ファイル名>.png（noteは assets/images/ogp/note/）
       カードのラベルはブログ記事=「重ね描き日記」、note記事=「note」

  すでに image: がある記事はスキップするので、何度実行しても安全（冪等）。
  GitHub Actions（.github/workflows/generate-ogp.yml）が記事のpush時に自動実行する。
  手動で実行する場合:
    pip install pillow
    python scripts/generate_post_ogp.py

デザイン（B-2）:
  白背景 / 短い赤ライン＋ラベル / 記事タイトル（黒・太字）/ URL（グレー・小）
  タイトルが長い場合は自動でフォントを縮小して収める。
"""

import re
import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

# (記事ディレクトリ, カード出力先, カードのラベル)
TARGETS = [
    (Path("_posts"), Path("assets/images/ogp"), "重ね描き日記"),
    (Path("_note"), Path("assets/images/ogp/note"), "note"),
]

W, H = 1200, 630
PAD_X = 96
LABEL_Y = 92
URL_BASELINE_PAD = 56          # 下端からURLまでの余白
FG, LABEL_GRAY, URL_GRAY, ACCENT = "#0d0d0d", "#555555", "#aaaaaa", "#cc2b2b"
BG = "#ffffff"

IMG_MD = re.compile(r"!\[[^\]]*\]\(([^)\s]+)")
IMG_TAG = re.compile(r'<img[^>]+src="([^"]+)"', re.IGNORECASE)


def load_font(size, bold=True):
    candidates = (
        ["C:/Windows/Fonts/YuGothB.ttc", "C:/Windows/Fonts/meiryob.ttc",
         "/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc"]
        if bold else
        ["C:/Windows/Fonts/YuGothM.ttc", "C:/Windows/Fonts/YuGothR.ttc",
         "C:/Windows/Fonts/meiryo.ttc",
         "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc"]
    )
    for path in candidates:
        try:
            return ImageFont.truetype(path, size)
        except OSError:
            continue
    raise SystemExit("日本語フォントが見つかりませんでした。candidates を編集してください。")


def split_front_matter(text):
    """front matter 部分と本文を分離。無ければ (None, text)"""
    if not text.startswith("---"):
        return None, text
    m = re.match(r"^---\s*\n(.*?)\n---\s*\n", text, re.DOTALL)
    if not m:
        return None, text
    return m, text[m.end():]


def get_title(fm_text):
    m = re.search(r'^title:\s*["\']?(.*?)["\']?\s*$', fm_text, re.MULTILINE)
    return m.group(1).strip() if m else ""


def first_image(body):
    """本文中の最初の画像パスを返す（無ければ None）"""
    hits = []
    for rx in (IMG_MD, IMG_TAG):
        m = rx.search(body)
        if m:
            hits.append((m.start(), m.group(1)))
    if not hits:
        return None
    path = min(hits)[1]
    if not path.startswith(("http://", "https://", "/")):
        path = "/" + path
    return path


def wrap_cjk(d, text, font, max_width):
    """CJK向けに文字単位で折り返し"""
    lines, line = [], ""
    for ch in text:
        if ch == "\n":
            lines.append(line)
            line = ""
            continue
        if d.textlength(line + ch, font=font) <= max_width:
            line += ch
        else:
            lines.append(line)
            line = ch
    if line:
        lines.append(line)
    return lines


def draw_tracked(d, xy, text, font, fill, tracking):
    """字間(tracking)を空けて1文字ずつ描画"""
    x, y = xy
    for ch in text:
        d.text((x, y), ch, font=font, fill=fill)
        x += d.textlength(ch, font=font) + tracking


def render_card(title, out_path, label):
    img = Image.new("RGB", (W, H), BG)
    d = ImageDraw.Draw(img)

    # 短い赤ライン ＋ ラベル
    label_font = load_font(26, bold=False)
    d.rectangle([PAD_X, LABEL_Y + 12, PAD_X + 44, LABEL_Y + 18], fill=ACCENT)
    draw_tracked(d, (PAD_X + 64, LABEL_Y), label, label_font, LABEL_GRAY, 6)

    # URL（下端）
    url_font = load_font(24, bold=False)
    url_y = H - URL_BASELINE_PAD - 24
    d.text((PAD_X, url_y), "rmaruy3.github.io", font=url_font, fill=URL_GRAY)

    # タイトル（長さに応じて 54 → 48 → 42 と縮小）
    title_top = LABEL_Y + 26 + 44
    avail_h = url_y - 40 - title_top
    max_w = W - PAD_X * 2
    for size in (54, 48, 42):
        font = load_font(size, bold=True)
        lines = wrap_cjk(d, title, font, max_w)
        line_h = int(size * 1.55)
        if len(lines) * line_h <= avail_h and len(lines) <= 4:
            break
    else:
        lines = lines[:4]
        if len(wrap_cjk(d, title, font, max_w)) > 4:
            lines[-1] = lines[-1][:-1] + "…"

    y = title_top
    for line in lines:
        d.text((PAD_X, y), line, font=font, fill=FG)
        y += line_h

    out_path.parent.mkdir(parents=True, exist_ok=True)
    img.save(out_path)


def insert_image(text, fm_match, image_path):
    """front matter の閉じ --- の直前に image: 行を挿入"""
    fm_end = fm_match.end()
    closing = text.rfind("---", 0, fm_end)
    return text[:closing] + f"image: {image_path}\n" + text[closing:]


def main():
    if not Path("_posts").is_dir():
        sys.exit("リポジトリのルートで実行してください（_posts が見つかりません）")

    n_img, n_card, n_skip = 0, 0, 0
    for src_dir, out_dir, label in TARGETS:
        if not src_dir.is_dir():
            continue
        for post in sorted(src_dir.glob("*.md")):
            text = post.read_text(encoding="utf-8")
            fm, body = split_front_matter(text)
            if fm is None:
                print(f"  skip (front matterなし): {post.name}")
                continue
            if re.search(r"^image:", fm.group(1), re.MULTILINE):
                n_skip += 1
                continue

            title = get_title(fm.group(1))
            img = first_image(body)
            if img:
                image_path = img
                n_img += 1
            else:
                card = out_dir / (post.stem + ".png")
                render_card(title or label, card, label)
                image_path = "/" + card.as_posix()
                n_card += 1

            post.write_text(insert_image(text, fm, image_path), encoding="utf-8")

    print(f"完了: 記事内画像を使用 {n_img} 件 / カード生成 {n_card} 件 / スキップ(設定済み) {n_skip} 件")


if __name__ == "__main__":
    main()
