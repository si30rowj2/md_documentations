// ============================================================
//  MkDocs (Material) 見出し番号注入スクリプト
//  mkdocs.yml の extra_javascript から読み込まれる。
//
//  wiki.js の wikijs/head-injection.html と同じ役割:
//  2階層フォルダ構成のパス末尾2セグメント
//    (例 /03_screens/01_login/ → 大分類 cat=3, 小分類 sub=1)
//  を数字プレフィックスから取り出し、CSS カウンタに設定する。
//
//  - 数字プレフィックス付きセグメントが2つ取れれば lvl2 (cat + sub)
//  - 1つだけなら lvl1 (cat のみ。フォルダ index 等のフォールバック)
//  - 0 なら番号なし (トップページ等)
//
//  Material の instant loading (SPA遷移) では window.document$ が
//  ページ切替ごとに発火するので、それを購読する。
// ============================================================
(function () {
  function applyChapterNumber() {
    var el = document.querySelector('.md-content .md-typeset');
    if (!el) return;

    // 末尾スラッシュ / .html を除いたパスを / で分割し、
    // 「先頭が数字プレフィックス」のセグメントの番号だけを順に集める
    var path = decodeURIComponent(location.pathname).replace(/\/+$/, '');
    var nums = path.split('/').reduce(function (acc, seg) {
      var s = seg.replace(/\.html$/, '');
      var m = s.match(/^0*(\d+)[-_]/);
      if (m) acc.push(parseInt(m[1], 10));
      return acc;
    }, []);

    el.classList.remove('numbered', 'lvl1', 'lvl2');
    if (nums.length >= 2) {
      // 末尾2つを 大分類(cat) / 小分類(sub) とみなす
      var sub = nums[nums.length - 1];
      var cat = nums[nums.length - 2];
      el.style.counterReset = 'cat ' + cat + ' sub ' + sub + ' h2 0 h3 0';
      el.classList.add('numbered', 'lvl2');
    } else if (nums.length === 1) {
      el.style.counterReset = 'cat ' + nums[0] + ' h2 0 h3 0';
      el.classList.add('numbered', 'lvl1');
    } else {
      el.style.counterReset = '';
    }
  }

  if (window.document$ && typeof window.document$.subscribe === 'function') {
    // Material instant loading: ページ遷移ごとに発火
    window.document$.subscribe(applyChapterNumber);
  } else {
    document.addEventListener('DOMContentLoaded', applyChapterNumber);
  }
})();
