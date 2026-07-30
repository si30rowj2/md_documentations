# ============================================================
# MkDocs フック (mkdocs.yml の hooks: から読み込まれる)
#
# docs.yml を唯一のソースとして、
#   - サイトタイトル (site_name)
#   - ナビゲーション (nav) … 表示名は「3-1. ログイン画面」と番号付き
#   - 本文の見出し番号
# を注入する。CSS カウンタや JS は使わないので、
# 左ナビ・ページ内 TOC・検索結果にも番号がそのまま出る。
# ============================================================
from __future__ import annotations

import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import doctree
from doctree import Doc, Node

_doc: Doc | None = None


def on_config(config):
    """docs.yml を読み込み、site_name と nav を差し替える。"""
    global _doc
    # mkdocs serve では設定変更のたびに呼ばれるので、毎回読み直す
    _doc = doctree.load(Path(config["config_file_path"]).parent)

    if _doc.meta.get("title"):
        config["site_name"] = _doc.meta["title"]

    nav = []
    if _doc.home:
        nav.append(_doc.home)          # トップページは採番対象外
    nav.extend(_nav_entry(_doc, node) for node in _doc.tree)
    config["nav"] = nav

    return config


def on_page_markdown(markdown, page, config, files):
    """ページ本文の見出し (H1..heading_depth) に章番号を前置する。"""
    src = getattr(page.file, "src_uri", None) or page.file.src_path.replace(os.sep, "/")
    node = _doc.page_of(src) if _doc else None
    if node is None:
        return markdown

    # ブラウザのタブ名も番号付きに揃える (front matter の title は番号を持たないため)
    page.title = _doc.numbered_title(node)
    return _doc.render_page(node, markdown)


def _nav_entry(doc: Doc, node: Node):
    """Node を MkDocs の nav 記法へ。表示名に章番号を含める。"""
    title = doc.numbered_title(node)
    if node.kind == "page":
        return {title: node.path.as_posix()}
    return {title: [_nav_entry(doc, child) for child in node.children]}
