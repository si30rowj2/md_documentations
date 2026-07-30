# ============================================================
# docs.yml をもとに各種の出力を生成する CLI。
#
#   python tools/render.py check                      … docs.yml と docs/ の整合性チェック
#   python tools/render.py combine                    … 全体を1つの md に結合 → dist/仕様書.md
#   python tools/render.py combine --mode per-section … セクションごとに1md → dist/3_画面仕様.md …
#   python tools/render.py combine --out PATH         … 出力先を明示 (PDF ビルドから利用)
#
# 章番号は tools/doctree.py が付ける。ここは並べて書き出すだけ。
# wiki.js 連携は tools/wikijs.py (md に番号を焼き込まず、表示時に採番する)。
# ============================================================
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import doctree
from doctree import Doc, DocError, Node

_INVALID_FILENAME_CHARS = re.compile(r'[\\/:*?"<>|]')


# ============================================================
#  check
# ============================================================

def cmd_check(doc: Doc, _args) -> int:
    problems = doc.check()
    if problems:
        print("docs.yml と docs/ に食い違いがあります:")
        for p in problems:
            print(f"  - {p}")
        return 1

    print(f"OK: {sum(1 for _ in doc.pages())} ページ、すべて docs.yml と一致しています")
    for node in doc.walk():
        indent = "  " * (node.depth - 1)
        target = f"  ({node.path.as_posix()})" if node.kind == "page" else ""
        print(f"  {indent}{doc.numbered_title(node)}{target}")
    return 0


# ============================================================
#  combine
# ============================================================

def build_section(doc: Doc, nodes: list[Node]) -> str:
    """ノード列を結合済み md のテキストにする。

    セクションはその階層の見出し (深さ1 なら `#`) として出力し、
    ページの見出しはその分だけ下げる。結果として
    `# 3. 画面仕様` / `## 3-1. ログイン画面` / `### 3-1-1. 画面仕様` になる。
    """
    chunks: list[str] = []
    for node in nodes:
        if node.kind == "section":
            chunks.append("#" * node.depth + " " + doc.numbered_title(node))
            chunks.append(build_section(doc, node.children))
        else:
            chunks.append(doc.render_page(node, shift=node.depth - 1))
    return "\n\n".join(c for c in chunks if c.strip())


def cmd_combine(doc: Doc, args) -> int:
    dist = doc.root / "dist"

    if args.mode == "single":
        target = Path(args.out) if args.out else dist / f"{doc.output}.md"
        write_text(target, build_section(doc, doc.tree))
        print(f"OK: {target}")
        return 0

    for node in doc.tree:
        stem = doc.separator.join(str(n) for n in node.number)
        target = dist / f"{stem}_{safe_filename(node.title)}.md"
        body = (build_section(doc, [node]) if node.kind == "page"
                else "#" * node.depth + " " + doc.numbered_title(node)
                     + "\n\n" + build_section(doc, node.children))
        write_text(target, body)
        print(f"OK: {target}")
    return 0


# ============================================================
#  ユーティリティ
# ============================================================

def safe_filename(name: str) -> str:
    return _INVALID_FILENAME_CHARS.sub("_", name).strip()


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text.rstrip() + "\n", encoding="utf-8", newline="\n")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="docs.yml から各種ドキュメントを生成する")
    sub = parser.add_subparsers(dest="command", required=True)

    sub.add_parser("check", help="docs.yml と docs/ の整合性をチェックする")

    combine = sub.add_parser("combine", help="採番済みの md を結合して dist/ に出力する")
    combine.add_argument("--mode", choices=("single", "per-section"), default="single",
                         help="single=全体を1ファイル (既定) / per-section=セクションごと")
    combine.add_argument("--out", help="出力先 (single のときのみ)")

    args = parser.parse_args(argv)
    handlers = {"check": cmd_check, "combine": cmd_combine}

    try:
        doc = doctree.load()
        return handlers[args.command](doc, args)
    except DocError as e:
        print(f"エラー: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
