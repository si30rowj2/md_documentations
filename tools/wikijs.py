# ============================================================
# wiki.js 連携 CLI。
#
#   python tools/wikijs.py theme   … docs.yml から採番スクリプトを生成
#                                     → wikijs/head-injection.html
#   python tools/wikijs.py push    … docs/ の md と サイドバーを wiki.js に反映
#   python tools/wikijs.py nav     … サイドバーだけを docs.yml の順序に更新
#
# 方針:
#   md には番号を焼き込まない。docs/ の md をそのまま wiki.js に載せ、
#   採番は wiki.js 側の表示時に行う (theme が生成するスクリプトが担当)。
#   番号の元データ (どのページが何番か) は docs.yml → tools/doctree.py から
#   取り出してスクリプトに埋め込むので、PDF / MkDocs と番号は一致する。
#
#   採番ロジック自体は doctree.py にしかない。このファイルは
#   「doctree が決めた番号を JS へ渡す」だけなので、
#   PDF / MkDocs の出力には一切影響しない。
#
#   wiki.js 上のページパスは docs.yml の `wikijs.path_prefix` を先頭に付けた
#   /docs/screens/login … になる (リバースプロキシで /docs を wiki.js へ
#   転送する運用のため)。theme と push は同じ設定を見るので必ず一致する。
#
# 注意: docs.yml の nav を変更したら theme を実行し直し、
#       生成された HTML を wiki.js に貼り直すこと (番号が埋め込みのため)。
# ============================================================
from __future__ import annotations

import argparse
import json
import os
import sys
import urllib.error
import urllib.request
import uuid
from pathlib import Path

import yaml

sys.path.insert(0, str(Path(__file__).resolve().parent))
import doctree
from doctree import Doc, DocError

DEFAULT_THEME_OUT = "wikijs/head-injection.html"
DEFAULT_LOCALE = "ja"


# ============================================================
#  設定 (docs.yml の wikijs セクション)
# ============================================================

def settings(doc: Doc) -> dict:
    """docs.yml の `wikijs:` を読む。

    doctree.py が扱わない項目なので、doctree に手を入れずここで直接読む
    (PDF / MkDocs から見れば存在しないのと同じ)。
    """
    config = yaml.safe_load((doc.root / doctree.CONFIG_NAME).read_text(encoding="utf-8")) or {}
    section = config.get("wikijs") or {}
    if not isinstance(section, dict):
        raise DocError("docs.yml の wikijs は `キー: 値` のマップで書いてください")
    return section


def path_prefix(section: dict, override: str | None = None) -> str:
    """wiki.js 上のページパスの先頭に付ける階層 (例 'docs')。無指定なら空。"""
    value = override if override is not None else section.get("path_prefix", "")
    return str(value or "").strip("/")


def wiki_path(prefix: str, rel: Path) -> str:
    """docs/ からの相対パス → wiki.js のページパス (screens/login.md → docs/screens/login)。"""
    path = rel.with_suffix("").as_posix()
    return f"{prefix}/{path}" if prefix else path


# ============================================================
#  theme … wiki.js に貼り付ける採番スクリプトを生成する
# ============================================================

def numbering_data(doc: Doc, prefix: str = "") -> dict:
    """JS に埋め込む採番テーブルを docs.yml から作る。

    キーは wiki.js 上のページパス (docs/screens/login.md → docs/screens/login)。
    number は doctree が nav 上の位置から決めた番号そのもの。
    """
    pages = {}
    for page in doc.pages():
        pages[wiki_path(prefix, page.path)] = {"number": page.number, "title": page.title}

    return {
        "separator": doc.separator,
        "suffix": doc.suffix,
        "headingDepth": doc.heading_depth,
        "pathPrefix": prefix,
        "pages": pages,
    }


def data_literal(data: dict) -> str:
    """採番テーブルを JS に埋め込む形に整形する (1 ページ 1 行で読めるように)。"""
    def js(value) -> str:
        return json.dumps(value, ensure_ascii=False)

    pages = list(data["pages"].items())
    lines = [
        "{",
        f'    "separator": {js(data["separator"])},',
        f'    "suffix": {js(data["suffix"])},',
        f'    "headingDepth": {data["headingDepth"]},',
        f'    "pathPrefix": {js(data["pathPrefix"])},',
        '    "pages": {',
    ]
    for i, (key, page) in enumerate(pages):
        lines.append(f"      {js(key)}: {js(page)}" + ("" if i == len(pages) - 1 else ","))
    lines += ["    }", "  }"]
    return "\n".join(lines)


# 生成される HTML の中身。%%DATA%% に numbering_data() の JSON が入る。
_TEMPLATE = """<!-- ============================================================
  wiki.js 見出し自動採番スクリプト  (tools/wikijs.py theme が生成 / 直接編集しない)

  貼り付け先: wiki.js 管理画面 → テーマ → 「HTMLヘッド注入」

  docs.yml の nav 上の位置から決まる番号を、表示時に
    ページタイトル / 本文の H1..H%%DEPTH%% / 右の目次 / 左のサイドバー
  へ付ける。md 本文には番号を書かないので、章を挿入しても md は無変更。

  docs.yml の nav を変更したときは
      python tools/wikijs.py theme
  を実行し、このファイルの内容を貼り直すこと (番号表を埋め込んでいるため)。
============================================================ -->
<style>
  .doc-num { white-space: nowrap; }
</style>
<script>
(function () {
  'use strict';

  var DATA = %%DATA%%;

  // --- 番号の書式 (doctree.py の fmt と同じ) ---
  function fmt(number) {
    return number.join(DATA.separator) + DATA.suffix;
  }

  // --- URL のパスから docs.yml のエントリを引く ---
  // 想定するパス: /docs/screens/login (pathPrefix 付き)、多言語構成なら /ja/docs/screens/login。
  // リバースプロキシがプレフィックスを落として wiki.js に渡す構成でも引けるよう、
  // プレフィックスを足した形も候補にする。
  function lookup(rawPath) {
    var path = rawPath.replace(/^\\/+|\\/+$/g, '');
    var candidates = [path];

    var slash = path.indexOf('/');                       // 先頭のロケールを外した形
    if (slash > 0 && /^[a-z]{2}(-[a-zA-Z]{2})?$/.test(path.slice(0, slash))) {
      candidates.push(path.slice(slash + 1));
    }
    if (DATA.pathPrefix) {                               // プレフィックスを足した形
      for (var n = candidates.length, i = 0; i < n; i++) {
        candidates.push(DATA.pathPrefix + '/' + candidates[i]);
      }
    }
    for (var c = 0; c < candidates.length; c++) {
      if (DATA.pages[candidates[c]]) return DATA.pages[candidates[c]];
    }
    return null;
  }

  function currentPage() {
    return lookup(decodeURIComponent(location.pathname));
  }

  function pageOfHref(href) {
    try {
      return lookup(decodeURIComponent(new URL(href, location.href).pathname));
    } catch (e) {
      return null;
    }
  }

  // --- 要素の先頭に番号を差し込む (再実行しても二重に付かない) ---
  function setNumber(el, text) {
    if (!el || el.getAttribute('data-doc-num') === text) return;
    var span = el.querySelector(':scope > span.doc-num');
    if (!span && el.textContent.indexOf(text) === 0) {
      el.setAttribute('data-doc-num', text);   // すでに番号入り (カスタムナビの項目名など)
      return;
    }
    if (!span) {
      span = document.createElement('span');
      span.className = 'doc-num';
      el.insertBefore(span, el.firstChild);
    }
    span.textContent = text + ' ';
    el.setAttribute('data-doc-num', text);
  }

  // --- 本文の見出し (doctree.py の render_page と同じ数え方) ---
  function numberHeadings(root, page) {
    var counters = [];                                   // counters[0]=H2, [1]=H3 ...
    for (var i = 0; i < DATA.headingDepth - 1; i++) counters.push(0);

    var heads = root.querySelectorAll('h1, h2, h3, h4, h5, h6');
    for (var k = 0; k < heads.length; k++) {
      var el = heads[k];
      var level = parseInt(el.tagName.charAt(1), 10);
      if (level > DATA.headingDepth) continue;

      var number;
      if (level === 1) {
        number = page.number.slice();
        for (var r = 0; r < counters.length; r++) counters[r] = 0;
      } else {
        var idx = level - 2;
        counters[idx] += 1;
        for (var z = idx + 1; z < counters.length; z++) counters[z] = 0;
        var used = [];                                   // H2 を飛ばして H3 が来ても 0 を出さない
        for (var u = 0; u < idx; u++) used.push(counters[u] || 1);
        used.push(counters[idx]);
        number = page.number.concat(used);
      }
      setNumber(el, fmt(number));
    }
  }

  // --- ページタイトル (ヘッダ見出しとブラウザのタブ名) ---
  function numberTitle(page) {
    var prefix = fmt(page.number);
    var heads = document.querySelectorAll(
      '.page-header .headline, .page-header-section .headline, ' +
      '.page-header h1, .page-header-section h1');
    for (var i = 0; i < heads.length; i++) setNumber(heads[i], prefix);

    if (document.title.indexOf(prefix + ' ') !== 0) {
      document.title = prefix + ' ' + document.title;
    }
  }

  // --- 右側のページ内目次 (本文の見出しから番号をコピーする) ---
  function numberToc(root) {
    var links = document.querySelectorAll('a[href^="#"]');
    for (var i = 0; i < links.length; i++) {
      var link = links[i];
      if (root.contains(link)) continue;                 // 本文内のアンカーは対象外
      var id = link.getAttribute('href').slice(1);
      if (!id) continue;
      var target = null;
      try {
        target = root.querySelector('#' + CSS.escape(id));
      } catch (e) {
        continue;
      }
      var number = target && target.getAttribute('data-doc-num');
      if (number) setNumber(link.querySelector('.v-list-item__title') || link, number);
    }
  }

  // --- 左のサイドバー (並び順は wiki.js 側の順のまま。表示名にだけ番号を付ける) ---
  function numberSidebar() {
    var links = document.querySelectorAll('.v-navigation-drawer a[href]');
    for (var i = 0; i < links.length; i++) {
      var page = pageOfHref(links[i].getAttribute('href'));
      if (page) {
        setNumber(links[i].querySelector('.v-list-item__title') || links[i], fmt(page.number));
      }
    }
  }

  function apply() {
    var root = document.querySelector('.contents') || document.querySelector('.page-contents');
    var page = currentPage();
    if (root && page) {
      numberHeadings(root, page);
      numberTitle(page);
      numberToc(root);
    }
    numberSidebar();
  }

  // wiki.js は SPA なので、DOM の差し替えを監視して付け直す。
  // setNumber が冪等なので、自分の書き換えで再実行されても 1 回で収束する。
  var queued = false;
  function schedule() {
    if (queued) return;
    queued = true;
    setTimeout(function () { queued = false; apply(); }, 50);
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', schedule);
  } else {
    schedule();
  }
  window.addEventListener('load', schedule);
  new MutationObserver(schedule).observe(document.documentElement, {
    childList: true, subtree: true
  });
})();
</script>
"""


def cmd_theme(doc: Doc, args) -> int:
    prefix = path_prefix(settings(doc), args.prefix)
    data = numbering_data(doc, prefix)
    html = (_TEMPLATE
            .replace("%%DEPTH%%", str(doc.heading_depth))
            .replace("%%DATA%%", data_literal(data)))

    target = Path(args.out) if args.out else doc.root / DEFAULT_THEME_OUT
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(html, encoding="utf-8", newline="\n")

    where = f"/{prefix}/…" if prefix else "/…"
    print(f"OK: {target}  ({len(data['pages'])} ページ分の番号を埋め込み / パス {where})")
    print("wiki.js 管理画面 → テーマ → 「HTMLヘッド注入」に貼り付けてください")
    return 0


# ============================================================
#  push … docs/ の md を wiki.js に反映する (GraphQL API)
# ============================================================

_LIST_QUERY = """
query { pages { list { id path locale title } } }
"""

_CREATE_MUTATION = """
mutation ($content: String!, $description: String!, $locale: String!,
          $path: String!, $title: String!) {
  pages {
    create(content: $content, description: $description, editor: "markdown",
           isPublished: true, isPrivate: false, locale: $locale,
           path: $path, tags: [], title: $title) {
      responseResult { succeeded errorCode message }
    }
  }
}
"""

_UPDATE_MUTATION = """
mutation ($id: Int!, $content: String!, $description: String!, $title: String!) {
  pages {
    update(id: $id, content: $content, description: $description,
           editor: "markdown", isPublished: true, title: $title) {
      responseResult { succeeded errorCode message }
    }
  }
}
"""

_DELETE_MUTATION = """
mutation ($id: Int!) {
  pages { delete(id: $id) { responseResult { succeeded errorCode message } } }
}
"""


# ============================================================
#  nav … サイドバーを docs.yml の並び順どおりに組み替える
#
#  wiki.js 組み込みのサイトツリーは
#    - フォルダ名がパスの断片そのまま (screens は screens のまま)
#    - 並び順がパスのアルファベット順で固定
#  なので、docs.yml の順序も日本語のセクション名も表現できない。
#  そのため「カスタムナビゲーション」を docs.yml から組み立てて流し込む。
#  カスタムナビゲーションは入れ子を持てない平坦なリストなので、
#  セクションは見出し (header) + 区切り (divider) で表現する。
# ============================================================

NAV_MODES = ("STATIC", "MIXED", "TREE", "NONE")
DEFAULT_NAV_MODE = "STATIC"
HOME_ICON = "mdi-home"
PAGE_ICON = "mdi-file-document-outline"

_NAV_QUERY = """
query {
  navigation {
    tree {
      locale
      items { id kind label icon targetType target visibilityMode visibilityGroups }
    }
  }
}
"""

_NAV_UPDATE_MUTATION = """
mutation ($tree: [NavigationTreeInput]!) {
  navigation {
    updateTree(tree: $tree) { responseResult { succeeded errorCode message } }
  }
}
"""

_NAV_CONFIG_MUTATION = """
mutation ($mode: NavigationMode!) {
  navigation {
    updateConfig(mode: $mode) { responseResult { succeeded errorCode message } }
  }
}
"""


def navigation_mode(section: dict, override: str | None = None) -> str:
    value = str(override or section.get("navigation_mode") or DEFAULT_NAV_MODE).upper()
    if value not in NAV_MODES:
        raise DocError(f"navigation_mode は {' / '.join(NAV_MODES)} のいずれかです: {value}")
    return value


def navigation_items(doc: Doc, prefix: str, locale: str) -> list[dict]:
    """docs.yml の nav 順に、wiki.js のカスタムナビゲーション項目を組み立てる。"""
    def item(kind: str, **fields) -> dict:
        return {"id": str(uuid.uuid4()), "kind": kind,
                "visibilityMode": "all", "visibilityGroups": [], **fields}

    def link(label: str, rel: Path, icon: str) -> dict:
        # target はそのまま href になる。wiki.js は /<locale>/<path> 形式を常に解釈する
        return item("link", label=label, icon=icon,
                    targetType="page", target=f"/{locale}/{wiki_path(prefix, rel)}")

    items: list[dict] = []
    if doc.home:                                     # 採番対象外のトップページ
        home = Path(doc.home)
        items.append(link(doctree.page_title(doc.docs_dir / home, home), home, HOME_ICON))

    def walk(nodes) -> None:
        for node in nodes:
            if node.kind == "section":
                items.append(item("header", label=doc.numbered_title(node)))
                walk(node.children)
            else:
                items.append(link(doc.numbered_title(node), node.path, PAGE_ICON))

    for node in doc.tree:
        if items:
            items.append(item("divider"))            # セクションの区切り
        walk([node])
    return items


def print_navigation(items: list[dict], mode: str, locale: str) -> None:
    print(f"ナビゲーション ({mode} / {locale}):")
    for entry in items:
        if entry["kind"] == "header":
            print(f"  [見出し] {entry['label']}")
        elif entry["kind"] == "divider":
            print("  --------")
        else:
            print(f"    {entry['label']}  →  {entry['target']}")


def sync_navigation(doc: Doc, url: str, token: str, prefix: str, locale: str,
                    mode: str, dry_run: bool) -> None:
    items = navigation_items(doc, prefix, locale)
    print_navigation(items, mode, locale)
    if dry_run:
        return

    # 他ロケールのナビゲーションは触らずに残す (updateTree は全体を置き換えるため)
    others = [tree for tree in graphql(url, token, _NAV_QUERY)["navigation"]["tree"]
              if tree["locale"] != locale]
    payload = others + [{"locale": locale, "items": items}]

    check_result(graphql(url, token, _NAV_UPDATE_MUTATION, {"tree": payload}),
                 "ナビゲーションの更新")
    check_result(graphql(url, token, _NAV_CONFIG_MUTATION, {"mode": mode}),
                 f"ナビゲーションモードの変更 ({mode})")
    print(f"OK: サイドバーを docs.yml の順序に更新しました ({len(items)} 項目)")


def cmd_nav(doc: Doc, args) -> int:
    url, token = endpoint(args)
    section = settings(doc)
    sync_navigation(doc, url, token,
                    path_prefix(section, args.prefix),
                    args.locale or str(section.get("locale") or DEFAULT_LOCALE),
                    navigation_mode(section, args.mode),
                    args.dry_run)
    return 0


def graphql(url: str, token: str, query: str, variables: dict | None = None) -> dict:
    request = urllib.request.Request(
        url.rstrip("/") + "/graphql",
        data=json.dumps({"query": query, "variables": variables or {}}).encode("utf-8"),
        headers={"Content-Type": "application/json",
                 "Authorization": f"Bearer {token}"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            payload = json.load(response)
    except urllib.error.HTTPError as e:
        raise DocError(f"wiki.js への接続に失敗しました ({e.code} {e.reason})") from e
    except urllib.error.URLError as e:
        raise DocError(f"wiki.js への接続に失敗しました ({e.reason})") from e

    if payload.get("errors"):
        raise DocError("wiki.js が拒否しました: "
                       + "; ".join(e.get("message", "?") for e in payload["errors"]))
    return payload["data"]


def check_result(result: dict, what: str) -> None:
    """mutation の responseResult を見て、失敗なら DocError にする。

    data の形は { pages: { create: { responseResult } } } のように
    「グループ名 → 操作名」の 2 段なので、名前を問わず辿る。
    """
    status = next(iter(next(iter(result.values())).values()))["responseResult"]
    if not status["succeeded"]:
        raise DocError(f"{what} に失敗しました: {status.get('message') or status.get('errorCode')}")


def read_front_matter(text: str) -> dict:
    m = doctree._FRONT_MATTER.match(text)
    data = yaml.safe_load(m.group(1)) if m else None
    return data if isinstance(data, dict) else {}


def source_pages(doc: Doc, prefix: str = "") -> list[tuple[str, str, str, str]]:
    """wiki.js に送るページを (path, title, description, content) で返す。

    番号は焼き込まない (表示時に theme のスクリプトが付ける)。
    front matter は wiki.js 側のメタデータになるので本文からは取り除く。
    """
    entries = []
    targets = [(Path(doc.home), None)] if doc.home else []
    targets += [(page.path, page) for page in doc.pages()]

    for rel, node in targets:
        source = (doc.docs_dir / rel).read_text(encoding="utf-8")
        meta = read_front_matter(source)
        title = node.title if node else str(meta.get("title") or rel.stem)
        entries.append((
            wiki_path(prefix, rel),
            title,
            str(meta.get("description") or ""),
            doctree.strip_front_matter(source).strip() + "\n",
        ))
    return entries


def endpoint(args) -> tuple[str, str]:
    url = args.url or os.environ.get("WIKIJS_URL")
    token = args.token or os.environ.get("WIKIJS_TOKEN")
    if not url or not token:
        raise DocError("wiki.js の URL と API トークンが必要です "
                       "(--url / --token、または環境変数 WIKIJS_URL / WIKIJS_TOKEN)")
    return url, token


def cmd_push(doc: Doc, args) -> int:
    url, token = endpoint(args)

    problems = doc.check()
    if problems:
        raise DocError("docs.yml と docs/ に食い違いがあります。"
                       "先に python tools/render.py check で確認してください")

    section = settings(doc)
    prefix = path_prefix(section, args.prefix)
    locale = args.locale or str(section.get("locale") or DEFAULT_LOCALE)

    # プレフィックスを付けている場合、その配下だけを管理対象にする
    # (同じ wiki.js に載っている他のページを --prune で消さないため)
    existing = {p["path"]: p for p in graphql(url, token, _LIST_QUERY)["pages"]["list"]
                if p["locale"] == locale
                and (not prefix or p["path"] == prefix or p["path"].startswith(prefix + "/"))}
    pushed: set[str] = set()

    for path, title, description, content in source_pages(doc, prefix):
        pushed.add(path)
        current = existing.get(path)
        variables = {"content": content, "description": description, "title": title}

        if current is None:
            if not args.dry_run:
                check_result(graphql(url, token, _CREATE_MUTATION,
                                     {**variables, "locale": locale, "path": path}),
                             f"作成 ({path})")
            print(f"作成: /{path}")
        else:
            if not args.dry_run:
                check_result(graphql(url, token, _UPDATE_MUTATION,
                                     {**variables, "id": current["id"]}),
                             f"更新 ({path})")
            print(f"更新: /{path}")

    for path, page in sorted(existing.items()):
        if path in pushed:
            continue
        if not args.prune:
            print(f"※ wiki.js にのみ存在します (--prune で削除): /{path}")
            continue
        if not args.dry_run:
            check_result(graphql(url, token, _DELETE_MUTATION, {"id": page["id"]}),
                         f"削除 ({path})")
        print(f"削除: /{path}")

    print(f"OK: {len(pushed)} ページを {url} に反映しました"
          + (" (--dry-run のため送信はしていません)" if args.dry_run else ""))

    if not args.no_nav:
        sync_navigation(doc, url, token, prefix, locale,
                        navigation_mode(section, args.mode), args.dry_run)
    return 0


# ============================================================

def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="docs.yml と docs/ を wiki.js に連携する")
    sub = parser.add_subparsers(dest="command", required=True)

    theme = sub.add_parser("theme", help="wiki.js に貼り付ける採番スクリプトを生成する")
    theme.add_argument("--out", help=f"出力先 (既定: {DEFAULT_THEME_OUT})")
    theme.add_argument("--prefix", help="ページパスの先頭階層 (既定: docs.yml の wikijs.path_prefix)")

    def add_target_options(p) -> None:
        p.add_argument("--url", help="wiki.js の URL (既定: 環境変数 WIKIJS_URL)")
        p.add_argument("--token", help="API トークン (既定: 環境変数 WIKIJS_TOKEN)")
        p.add_argument("--prefix", help="ページパスの先頭階層 (既定: docs.yml の wikijs.path_prefix)")
        p.add_argument("--locale", help=f"ロケール (既定: docs.yml の wikijs.locale / {DEFAULT_LOCALE})")
        p.add_argument("--mode", choices=NAV_MODES,
                       help=f"ナビゲーションモード (既定: docs.yml の wikijs.navigation_mode / {DEFAULT_NAV_MODE})")
        p.add_argument("--dry-run", action="store_true", help="送信せず、何をするかだけ表示する")

    push = sub.add_parser("push", help="docs/ の md と サイドバーを wiki.js に反映する")
    add_target_options(push)
    push.add_argument("--prune", action="store_true",
                      help="docs.yml から外れたページを wiki.js からも削除する")
    push.add_argument("--no-nav", action="store_true",
                      help="サイドバー (カスタムナビゲーション) を更新しない")

    nav = sub.add_parser("nav", help="サイドバーだけを docs.yml の順序に更新する")
    add_target_options(nav)

    args = parser.parse_args(argv)
    handlers = {"theme": cmd_theme, "push": cmd_push, "nav": cmd_nav}

    try:
        doc = doctree.load()
        return handlers[args.command](doc, args)
    except DocError as e:
        print(f"エラー: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
