// ==UserScript==
// @name         ZipRecruiter Careers + Excel Row Copy
// @namespace    http://tampermonkey.net/
// @version      1.4
// @description  Adds "Go To Careers" and "Copy Excel Data" buttons on ZipRecruiter job pages, with full row copy and a floating refresh button to re-inject them on demand.
// @author       You
// @match        https://www.ziprecruiter.com/jobs-search?*
// @grant        none
// @run-at       document-end
// ==/UserScript==

(function () {
    'use strict';

    const BUTTON_ID = 'zip-careers-button';
    const EXCEL_BUTTON_ID = 'zip-excel-button';
    const FLOATING_REFRESH_ID = 'zip-floating-refresh-button';

    function createStyledButton(text, id, bgColor) {
        const button = document.createElement('button');
        button.textContent = text;
        button.id = id;

        button.style.backgroundColor = bgColor;
        button.style.color = '#fff';
        button.style.border = 'none';
        button.style.borderRadius = '20px';
        button.style.padding = '10px 16px';
        button.style.cursor = 'pointer';
        button.style.fontWeight = 'bold';
        button.style.marginTop = '12px';
        button.style.display = 'block';

        return button;
    }

    function createCareersButton(companyName) {
        const button = createStyledButton('Go To Careers', BUTTON_ID, '#00635d');
        button.addEventListener('click', () => {
            const query = encodeURIComponent(`${companyName} careers`);
            window.open(`https://www.google.com/search?q=${query}`, '_blank');
        });
        return button;
    }

    function createExcelCopyButton(jobTitle, companyName) {
        const button = createStyledButton('Copy Excel Data', EXCEL_BUTTON_ID, '#0a4b44');

        button.addEventListener('click', () => {
            const websiteFirstFound = 'ZipRecruiter';
            const appliedOnCompanySite = '';
            const customizedResume = '';
            const jobPost = ''; // per your request: blank URL
            const emptyValue1 = '';
            const emptyValue2 = '';
            const currentDate = new Date();
            const dateApplied = `${String(currentDate.getMonth() + 1).padStart(2, '0')}/${String(currentDate.getDate()).padStart(2, '0')}/${currentDate.getFullYear()}`;

            const jobData = [
                jobTitle,
                companyName,
                websiteFirstFound,
                appliedOnCompanySite,
                customizedResume,
                jobPost,
                emptyValue1,
                emptyValue2,
                dateApplied
            ].join('\t');

            navigator.clipboard.writeText(jobData).then(() => {
                button.textContent = 'Copied!';
                setTimeout(() => (button.textContent = 'Copy Excel Data'), 1500);
            }).catch(err => {
                console.error('Failed to copy:', err);
            });
        });

        return button;
    }

    function injectButtons() {
        const rightPane = document.querySelector('[data-testid="right-pane"]');
        if (!rightPane) return;

        const innerDivs = rightPane.querySelectorAll('div > div');
        if (innerDivs.length < 2) return;

        const targetDiv = innerDivs[1];
        const companyElement = targetDiv.querySelector('a');
        const jobTitleElement = targetDiv.querySelector('h1');

        if (!companyElement || !companyElement.textContent.trim() || !jobTitleElement) return;

        const companyName = companyElement.textContent.trim();
        const jobTitle = jobTitleElement.textContent.trim();

        if (document.getElementById(BUTTON_ID)) return;

        const careersButton = createCareersButton(companyName);
        const excelButton = createExcelCopyButton(jobTitle, companyName);

        companyElement.insertAdjacentElement('afterend', careersButton);
        careersButton.insertAdjacentElement('afterend', excelButton);
    }

    function createFloatingRefreshButton() {
        if (document.getElementById(FLOATING_REFRESH_ID)) return;

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

        refreshButton.addEventListener('click', injectButtons);
        document.body.appendChild(refreshButton);
    }

    setTimeout(() => {
        createFloatingRefreshButton();
        injectButtons();
    }, 2000);
})();
