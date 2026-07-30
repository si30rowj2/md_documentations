# ============================================================
# ソフトウェア仕様書 PDF / HTML ビルド (Pandoc)
#
#   python build/build.py                    … output/仕様書.pdf
#   python build/build.py --format html      … output/仕様書.html
#   python build/build.py --main-font "Yu Gothic" --mono-font "BIZ UDGothic"
#
# 必要: Pandoc (+ PDF なら TeX 環境の xelatex と日本語フォント)
#
# docs.yml の順序に従って tools/render.py が 1 つの md に結合する。
# 章番号はその時点で見出しテキストに焼き込まれるので、pandoc の
# --number-sections は使わない (これで PDF / MkDocs / wiki.js の番号が完全に一致する)。
# ============================================================
from __future__ import annotations

import argparse
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))
import doctree
import render

WINDOWS_FONTS = ("Yu Mincho", "MS Gothic")
OTHER_FONTS = ("Noto Serif CJK JP", "Noto Sans Mono CJK JP")


def main(argv: list[str] | None = None) -> int:
    default_main, default_mono = WINDOWS_FONTS if sys.platform == "win32" else OTHER_FONTS

    parser = argparse.ArgumentParser(description="docs.yml から PDF / HTML を生成する")
    parser.add_argument("--format", choices=("pdf", "html"), default="pdf")
    parser.add_argument("--output", help="出力先 (既定: output/<docs.yml の output>.<形式>)")
    parser.add_argument("--main-font", default=default_main, help=f"本文フォント (既定: {default_main})")
    parser.add_argument("--mono-font", default=default_mono, help=f"等幅フォント (既定: {default_mono})")
    args = parser.parse_args(argv)

    # PATH に無い場合は環境変数 PANDOC でフルパスを指定できる
    pandoc = os.environ.get("PANDOC") or shutil.which("pandoc")
    if not pandoc:
        print("エラー: pandoc が見つかりません。インストールするか、環境変数 PANDOC に "
              "実行ファイルのパスを設定してください", file=sys.stderr)
        return 1

    doc = doctree.load()
    output = Path(args.output) if args.output else doc.root / "output" / f"{doc.output}.{args.format}"
    output.parent.mkdir(parents=True, exist_ok=True)

    with tempfile.TemporaryDirectory() as tmp:
        merged = Path(tmp) / "merged.md"
        render.write_text(merged, render.build_section(doc, doc.tree))

        cmd = [
            pandoc, str(merged),
            "--from", "markdown",
            "--resource-path", str(doc.docs_dir),
            "--toc", "--toc-depth=4",
            "-o", str(output),
        ]
        for key, value in doc.meta.items():
            cmd += ["-M", f"{key}={value}"]

        if args.format == "pdf":
            cmd += [
                "--pdf-engine=xelatex",
                "--include-in-header", str(doc.root / "build" / "header.tex"),
                "-V", "documentclass=article",
                "-V", "classoption=titlepage",   # 表紙を独立した1ページにする
                "-V", f"mainfont={args.main_font}",
                "-V", f"monofont={args.mono_font}",
                "-V", "papersize=a4",
                "-V", "geometry:margin=25mm",
                "-V", "colorlinks=true",
                "-V", "linkcolor=blue",
            ]
        else:
            cmd += ["--to", "html5", "--standalone", "--embed-resources"]

        # pandoc(xelatex) は MiKTeX の非致命警告を stderr に出すことがあるため、
        # stderr の有無ではなく終了コードだけで成否を判定する
        result = subprocess.run(cmd, cwd=doc.root)

    if result.returncode != 0:
        print(f"エラー: pandoc が失敗しました (exit {result.returncode})", file=sys.stderr)
        return result.returncode

    print(f"OK: {output}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
