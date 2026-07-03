// ==UserScript==
// @name         YouTube Continuer
// @namespace    https://github.com/rbrock44/scripts
// @version      0.1.1
// @description  click ok on the continue watching popup
// @author       Rbrock44
// @match        https://www.youtube.com/watch?*
// @icon         https://www.google.com/s2/favicons?sz=64&domain=youtube.com
// @grant        none
// @license      MIT
// @supportURL   https://github.com/rbrock44/scripts/issues
// @homepageURL  https://github.com/rbrock44/scripts/tree/master/tampermonkey
// @updateURL    https://raw.githubusercontent.com/rbrock44/scripts/master/tampermonkey/youtube-continuer.user.js
// @downloadURL  https://raw.githubusercontent.com/rbrock44/scripts/master/tampermonkey/youtube-continuer.user.js
// ==/UserScript==
(function() {
    let checkForPopup = function() {
        let popup = document.getElementsByClassName('yt-confirm-dialog-renderer');
        if (popup.length = 0) {
            return;
        }
        let confirmButton = document.getElementById('confirm-button');
        if (confirmButton) {
            confirmButton.click();
        }
    };

    setInterval(checkForPopup, 33000);
})();