// ==UserScript==
// @name         GitHub PR Auto-Unsubscribe & Close
// @namespace    rbrock44
// @version      1.0
// @description  On PR pages, click Unsubscribe then close the tab
// @match        https://github.com/*/*/pull/*
// @grant        window.close
// @run-at       document-idle
// @updateURL    https://raw.githubusercontent.com/rbrock44/scripts/main/tampermonkey/github-pr-unsub-close.user.js
// @downloadURL  https://raw.githubusercontent.com/rbrock44/scripts/main/tampermonkey/github-pr-unsub-close.user.js
// ==/UserScript==

(function () {
  'use strict';

  function findUnsubscribeButton() {
    return document.querySelector('button[aria-label="Unsubscribe"], button[id$="-unsubscribe"]');
  }

  function attachCloseOnClick(attemptsLeft) {
    const btn = findUnsubscribeButton();
    if (btn) {
      btn.addEventListener('click', () => {
        // let the form submit/turbo update happen before closing
        setTimeout(() => window.close(), 800);
      });
      return;
    }
    if (attemptsLeft > 0) {
      setTimeout(() => attachCloseOnClick(attemptsLeft - 1), 300);
    }
  }

  attachCloseOnClick(15); // ~4.5s max wait for button to render
})();
