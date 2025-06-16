// ==UserScript==
// @name         Indeed Careers Manual Injector
// @namespace    http://tampermonkey.net/
// @version      1.0
// @description  Manually inject a "Go To Careers" button on Indeed job pages using a floating refresh button in the corner.
// @author       You
// @match        https://www.indeed.com/jobs*
// @grant        none
// @run-at       document-end
// ==/UserScript==

(function () {
    'use strict';

    const BUTTON_ID = 'indeed-careers-button';
    const FLOATING_REFRESH_ID = 'floating-refresh-careers-button';

    function createCareersButton(companyName) {
        const button = document.createElement('button');
        button.textContent = 'Go To Careers';
        button.id = BUTTON_ID;

        button.style.backgroundColor = '#2557a7';
        button.style.color = '#fff';
        button.style.border = 'none';
        button.style.borderRadius = '20px';
        button.style.padding = '10px 16px';
        button.style.cursor = 'pointer';
        button.style.fontWeight = 'bold';
        button.style.marginTop = '12px';
        button.style.display = 'block';

        button.addEventListener('click', () => {
            const query = encodeURIComponent(`${companyName} careers`);
            window.open(`https://www.google.com/search?q=${query}`, '_blank');
        });

        return button;
    }

    function injectCareersButton() {
        const companyDiv = document.querySelector('div[data-company-name="true"]');
        if (!companyDiv) {
            console.warn('Company element not found.');
            return;
        }

        const companyAnchor = companyDiv.querySelector('a');
        const companyName = companyAnchor?.textContent?.trim();
        if (!companyName) {
            console.warn('Company name not found.');
            return;
        }

        // Avoid duplicating the button
        if (document.getElementById(BUTTON_ID)) {
            console.log('Careers button already exists.');
            return;
        }

        const careersButton = createCareersButton(companyName);
        companyDiv.appendChild(careersButton);
    }

    function createFloatingRefreshButton() {
        const refreshButton = document.createElement('button');
        refreshButton.textContent = '↻ Careers';
        refreshButton.id = FLOATING_REFRESH_ID;

        refreshButton.style.position = 'fixed';
        refreshButton.style.bottom = '20px';
        refreshButton.style.left = '20px';
        refreshButton.style.backgroundColor = '#e0e0e0';
        refreshButton.style.border = 'none';
        refreshButton.style.borderRadius = '12px';
        refreshButton.style.padding = '8px 14px';
        refreshButton.style.cursor = 'pointer';
        refreshButton.style.zIndex = '9999';
        refreshButton.style.boxShadow = '0 2px 6px rgba(0,0,0,0.3)';
        refreshButton.style.fontWeight = 'bold';

        refreshButton.addEventListener('click', injectCareersButton);

        document.body.appendChild(refreshButton);
    }

    // Wait for the page to stabilize, then add the refresh button
    setTimeout(createFloatingRefreshButton, 2000);
})();
