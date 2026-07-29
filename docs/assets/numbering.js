// ============================================================
//  MkDocs (Material) 章番号注入スクリプト
//  mkdocs.yml の extra_javascript から読み込まれる。
//
//  wiki.js の wikijs/head-injection.html と同じ役割:
//  ページパス末尾の数字プレフィックス (例: /01_overview/ → 1,
//  /03-functions/ → 3) を章番号として CSS カウンタに設定する。
//
//  Material の instant loading (SPA遷移) では window.document$ が
//  ページ切替ごとに発火するので、それを購読する。無効時は
//  DOMContentLoaded にフォールバックする。
// ============================================================
(function () {
  function applyChapterNumber() {
    var el = document.querySelector('.md-content .md-typeset');
    if (!el) return;
    // 末尾スラッシュ / .html を除いた最終セグメントの先頭数字を章番号とみなす
    var path = decodeURIComponent(location.pathname).replace(/\/+$/, '');
    var seg = (path.split('/').pop() || '').replace(/\.html$/, '');
    var m = seg.match(/^0*(\d+)[-_]/);
    if (m) {
      el.style.counterReset = 'chapter ' + parseInt(m[1], 10) + ' sec2 0';
      el.classList.add('numbered');
    } else {
      el.style.counterReset = '';
      el.classList.remove('numbered');
    }
  }

  if (window.document$ && typeof window.document$.subscribe === 'function') {
    // Material instant loading: ページ遷移ごとに発火
    window.document$.subscribe(applyChapterNumber);
  } else {
    document.addEventListener('DOMContentLoaded', applyChapterNumber);
  }
})();
