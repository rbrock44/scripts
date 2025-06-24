// ==UserScript==
// @name YouTube Continuer
// @namespace http://tampermonkey.net/
// @version 0.1
// @description click ok on the continue watching popup
// @author Ryan Brock
// @match https://www.youtube.com/watch?*
// @grant none
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