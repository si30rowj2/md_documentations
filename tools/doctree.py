# ============================================================
# docs.yml から章番号付きのドキュメントツリーを組み立てる共通ライブラリ。
#
# 採番ロジックはこのファイルにしか存在しない。
# MkDocs (tools/mkdocs_hook.py)・結合md/wiki.js (tools/render.py)・
# PDF/HTML (build/build.py) はすべてここを経由するので、
# どの出力でも番号は完全に一致する。
#
# 採番モデル (docs.yml の nav 上の位置がそのまま番号になる):
#   セクション     nav の項目        3.
#   ページ         nav 内のファイル  3-1.      (= md の H1)
#   中項目         ページ内の H2     3-1-1.
#   小項目         ページ内の H3     3-1-1-1.
# ============================================================
from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterator

import yaml

CONFIG_NAME = "docs.yml"
DOCS_DIRNAME = "docs"

_FRONT_MATTER = re.compile(r"\A---\s*\n(.*?)\n(?:---|\.\.\.)\s*(?:\n|\Z)", re.S)
_FENCE = re.compile(r"^\s*(```+|~~~+)")
_HEADING = re.compile(r"^(#{1,6})\s+(.*?)\s*$")


class DocError(Exception):
    """docs.yml の記述ミスなど、利用者が直すべきエラー。"""


@dataclass
class Node:
    kind: str                    # 'section' | 'page'
    number: list[int]            # [3, 1] など。nav 上の位置
    title: str
    path: Path | None = None     # page のみ。docs/ からの相対パス
    children: list["Node"] = field(default_factory=list)

    @property
    def depth(self) -> int:
        return len(self.number)


@dataclass
class Doc:
    root: Path                   # リポジトリのルート
    docs_dir: Path
    meta: dict                   # title / subtitle / author / date …
    separator: str
    suffix: str
    heading_depth: int
    home: str | None
    output: str                  # 生成ファイルのベース名
    tree: list[Node]

    # --- 番号の書式 ---------------------------------------------------

    def fmt(self, number: list[int]) -> str:
        """[3, 1, 1] → '3-1-1.'"""
        return self.separator.join(str(n) for n in number) + self.suffix

    def numbered_title(self, node: Node) -> str:
        return f"{self.fmt(node.number)} {node.title}"

    # --- ツリーの走査 -------------------------------------------------

    def walk(self, nodes: list[Node] | None = None) -> Iterator[Node]:
        """ツリーを nav 順(深さ優先)に走査する。"""
        for node in self.tree if nodes is None else nodes:
            yield node
            yield from self.walk(node.children)

    def pages(self) -> Iterator[Node]:
        return (n for n in self.walk() if n.kind == "page")

    def page_of(self, rel_path: str | Path) -> Node | None:
        """docs/ からの相対パスに対応するページノードを返す (無ければ None)。"""
        key = Path(rel_path).as_posix()
        return next((p for p in self.pages() if p.path.as_posix() == key), None)

    # --- 本文の採番 ---------------------------------------------------

    def render_page(self, node: Node, text: str | None = None, shift: int = 0) -> str:
        """ページ本文の見出しに章番号を前置する。

        front matter は除去する。`shift` を渡すと見出しをその段数だけ下げる
        (結合md でセクション見出しの下にぶら下げるときに使う)。
        コードフェンス内の `#` は見出しとして扱わない。
        """
        if text is None:
            text = (self.docs_dir / node.path).read_text(encoding="utf-8")

        out: list[str] = []
        # counters[0] が H2、counters[1] が H3 … の連番
        counters = [0] * max(0, self.heading_depth - 1)
        in_fence = False

        for line in strip_front_matter(text).splitlines():
            if _FENCE.match(line):
                in_fence = not in_fence
                out.append(line)
                continue

            m = None if in_fence else _HEADING.match(line)
            if not m:
                out.append(line)
                continue

            level, body = len(m.group(1)), m.group(2)
            if level <= self.heading_depth:
                if level == 1:
                    number = node.number
                    counters = [0] * len(counters)
                else:
                    idx = level - 2
                    counters[idx] += 1
                    counters[idx + 1:] = [0] * (len(counters) - idx - 1)
                    # H2 を飛ばして H3 が来た場合でも 0 を出さない
                    used = [c or 1 for c in counters[:idx]] + [counters[idx]]
                    number = node.number + used
                body = f"{self.fmt(number)} {body}"
            out.append("#" * (level + shift) + " " + body)

        return "\n".join(out).strip() + "\n"

    # --- 整合性チェック -----------------------------------------------

    def check(self) -> list[str]:
        """docs.yml と docs/ の食い違いを列挙する (問題が無ければ空リスト)。"""
        problems: list[str] = []
        listed: set[str] = set()

        for page in self.pages():
            rel = page.path.as_posix()
            if rel in listed:
                problems.append(f"docs.yml に重複して登録されています: {rel}")
            listed.add(rel)
            if not (self.docs_dir / page.path).is_file():
                problems.append(f"docs.yml に書かれたファイルがありません: docs/{rel}")

        if self.home:
            listed.add(Path(self.home).as_posix())
            if not (self.docs_dir / self.home).is_file():
                problems.append(f"home のファイルがありません: docs/{self.home}")

        for md in sorted(self.docs_dir.rglob("*.md")):
            rel = md.relative_to(self.docs_dir).as_posix()
            if rel.startswith("assets/"):
                continue
            if rel not in listed:
                problems.append(f"docs.yml に登録されていません (出力対象外): docs/{rel}")

        return problems


# ============================================================
#  読み込み
# ============================================================

def find_root(start: Path | None = None) -> Path:
    """docs.yml のあるディレクトリを上に向かって探す。"""
    here = (start or Path(__file__)).resolve()
    for candidate in [here, *here.parents]:
        if (candidate / CONFIG_NAME).is_file():
            return candidate
    raise DocError(f"{CONFIG_NAME} が見つかりません")


def load(root: Path | None = None) -> Doc:
    root = find_root(root)
    config = yaml.safe_load((root / CONFIG_NAME).read_text(encoding="utf-8")) or {}
    docs_dir = root / DOCS_DIRNAME
    numbering = config.get("numbering") or {}

    doc = Doc(
        root=root,
        docs_dir=docs_dir,
        meta={k: v for k, v in config.items()
              if k in ("title", "subtitle", "author", "date")},
        separator=str(numbering.get("separator", "-")),
        suffix=str(numbering.get("suffix", ".")),
        heading_depth=int(numbering.get("heading_depth", 3)),
        home=config.get("home"),
        output=str(config.get("output") or "document"),
        tree=[],
    )
    doc.tree = _build(config.get("nav") or [], [], docs_dir)
    return doc


def _build(entries, prefix: list[int], docs_dir: Path) -> list[Node]:
    """nav のリストを Node のリストへ (番号を振りながら再帰)。"""
    nodes: list[Node] = []
    for i, entry in enumerate(entries, start=1):
        number = prefix + [i]

        if isinstance(entry, str):                      # - path/to.md
            nodes.append(_page(entry, number, None, docs_dir))
            continue

        if not isinstance(entry, dict) or len(entry) != 1:
            raise DocError(f"nav の項目が不正です: {entry!r}")

        (title, value), = entry.items()
        if isinstance(value, str):                      # - 表示名: path/to.md
            nodes.append(_page(value, number, title, docs_dir))
        elif isinstance(value, list):                   # - セクション名: [...]
            nodes.append(Node("section", number, str(title),
                              children=_build(value, number, docs_dir)))
        else:
            raise DocError(f"nav の項目が不正です: {entry!r}")

    return nodes


def _page(rel: str, number: list[int], title: str | None, docs_dir: Path) -> Node:
    path = Path(rel)
    return Node("page", number, title or page_title(docs_dir / path, path), path=path)


def page_title(abs_path: Path, rel_path: Path) -> str:
    """ページタイトルを front matter の title → H1 → ファイル名 の順で解決する。"""
    if not abs_path.is_file():
        return rel_path.stem
    text = abs_path.read_text(encoding="utf-8")

    m = _FRONT_MATTER.match(text)
    if m:
        data = yaml.safe_load(m.group(1)) or {}
        if isinstance(data, dict) and data.get("title"):
            return str(data["title"])

    for line in strip_front_matter(text).splitlines():
        h = _HEADING.match(line)
        if h and len(h.group(1)) == 1:
            return h.group(2)

    return rel_path.stem


def strip_front_matter(text: str) -> str:
    return _FRONT_MATTER.sub("", text, count=1)
