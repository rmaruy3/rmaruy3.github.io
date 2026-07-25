"""
generate_book_ogp.py — 書影入りのOGPカードを生成する（読書メモ用）

generate_post_ogp.py のB-2デザイン（白背景／短い赤ライン＋ラベル／黒タイトル／下部URL）に、
右側に書影を配置したバリエーション。読書メモのように「本の顔」を見せたい記事で使う。

使い方（リポジトリのルートで実行）:
    python scripts/generate_book_ogp.py _posts/2026-07-25-post.md assets/images/hito-to-ai-cover.jpg

  - 記事の front matter から title を読み、カードを
    assets/images/ogp/<記事ファイル名>.png に出力する（既存ファイルは上書き）。
  - front matter に image: が無ければ追記する（既にあれば触らない）。
  - generate_post_ogp.py は image: がある記事をスキップするので、
    このスクリプトで作ったカードがGitHub Actionsに上書きされることはない。
"""

import sys
from pathlib import Path

from PIL import Image, ImageDraw

from generate_post_ogp import (  # 同じディレクトリの共通処理を再利用
    ACCENT,
    BG,
    FG,
    H,
    LABEL_GRAY,
    LABEL_Y,
    PAD_X,
    URL_BASELINE_PAD,
    URL_GRAY,
    W,
    draw_tracked,
    get_title,
    insert_image,
    load_font,
    split_front_matter,
    wrap_cjk,
)

COVER_H = 430           # 書影の高さ
COVER_GAP = 64          # 書影とテキスト列のあいだの余白
BORDER = "#e0e0e0"      # 書影の縁取り（白い表紙でも輪郭が出るように）


def render_book_card(title, cover_path, out_path, label="重ね描き日記"):
    img = Image.new("RGB", (W, H), BG)
    d = ImageDraw.Draw(img)

    # --- 書影（右側・縦中央） ---
    cover = Image.open(cover_path).convert("RGB")
    cover_w = round(cover.width * COVER_H / cover.height)
    cover = cover.resize((cover_w, COVER_H), Image.LANCZOS)
    cover_x = W - PAD_X - cover_w
    cover_y = (H - COVER_H) // 2
    img.paste(cover, (cover_x, cover_y))
    d.rectangle(
        [cover_x - 1, cover_y - 1, cover_x + cover_w, cover_y + COVER_H],
        outline=BORDER,
        width=1,
    )

    # --- 短い赤ライン ＋ ラベル ---
    label_font = load_font(26, bold=False)
    d.rectangle([PAD_X, LABEL_Y + 12, PAD_X + 44, LABEL_Y + 18], fill=ACCENT)
    draw_tracked(d, (PAD_X + 64, LABEL_Y), label, label_font, LABEL_GRAY, 6)

    # --- URL（下端） ---
    url_font = load_font(24, bold=False)
    url_y = H - URL_BASELINE_PAD - 24
    d.text((PAD_X, url_y), "rmaruy3.github.io", font=url_font, fill=URL_GRAY)

    # --- タイトル（書影の左側に収まるよう折り返し・自動縮小） ---
    title_top = LABEL_Y + 26 + 44
    avail_h = url_y - 40 - title_top
    max_w = cover_x - COVER_GAP - PAD_X
    for size in (48, 44, 40, 36):
        font = load_font(size, bold=True)
        # 『書名』が行をまたぐと読みにくいので、収まらない場合は『の前で改行する
        text = title
        if "『" in title and d.textlength(title, font=font) > max_w:
            head, _, tail = title.partition("『")
            if d.textlength(head, font=font) <= max_w and d.textlength("『" + tail, font=font) <= max_w:
                text = head + "\n『" + tail
        lines = wrap_cjk(d, text, font, max_w)
        line_h = int(size * 1.55)
        if len(lines) * line_h <= avail_h and len(lines) <= 5:
            break
    else:
        lines = lines[:5]
        lines[-1] = lines[-1][:-1] + "…"

    y = title_top
    for line in lines:
        d.text((PAD_X, y), line, font=font, fill=FG)
        y += line_h

    out_path.parent.mkdir(parents=True, exist_ok=True)
    img.save(out_path)


def main():
    if len(sys.argv) != 3:
        sys.exit(__doc__)
    post = Path(sys.argv[1])
    cover = Path(sys.argv[2])
    if not post.is_file() or not cover.is_file():
        sys.exit("記事ファイルまたは書影ファイルが見つかりません")

    text = post.read_text(encoding="utf-8")
    fm, _ = split_front_matter(text)
    if fm is None:
        sys.exit("front matter が見つかりません")

    out = Path("assets/images/ogp") / (post.stem + ".png")
    render_book_card(get_title(fm.group(1)), cover, out)
    print(f"生成: {out}")

    if "\nimage:" not in "\n" + fm.group(1):
        post.write_text(insert_image(text, fm, "/" + out.as_posix()), encoding="utf-8")
        print(f"front matter に image: を追記しました")


if __name__ == "__main__":
    main()
