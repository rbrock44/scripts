// ==UserScript==
// @name         LinkedIn Careers Button Injector
// @namespace    http://tampermonkey.net/
// @version      1.0
// @description  Add a "${Company Name} Careers" button to job postings
// @author       You
// @match        https://www.linkedin.com/jobs/view/*
// @match        https://linkedin.com/jobs/view/*
// @match        *linkedin.com/jobs/view*
// @grant        none
// @run-at       document-end
// ==/UserScript==

(function () {
    'use strict';
    const COMPANY_LINK_SELECTOR = '.jobs-details .p5 .job-details-jobs-unified-top-card__company-name';
    const MAX_RETRIES = 10;
    const RETRY_INTERVAL_MS = 500;

    function createButton(companyName) {
        const button = document.createElement('button');
        button.textContent = `Go To careers`;
        button.style.backgroundColor = '#0073b1'; // LinkedIn blue
        button.style.color = '#fff';
        button.style.border = 'none';
        button.style.borderRadius = '20px';
        button.style.padding = '10px 16px';
        button.style.cursor = 'pointer';
        button.style.fontWeight = 'bold';
        button.style.marginTop = '12px';
        button.style.marginLeft = '12px';
        button.style.display = 'block';

        button.addEventListener('click', () => {
            const query = encodeURIComponent(`${companyName} careers`);
            window.open(`https://www.google.com/search?q=${query}`, '_blank');
        });

        return button;
    }

    function tryInject(retriesLeft) {
        const companyLink = document.querySelector(COMPANY_LINK_SELECTOR);

        if (companyLink && companyLink.textContent.trim()) {
            const companyName = companyLink.textContent.trim();

            // Check if button already exists
            if (document.getElementById('careers-button')) return;

            const button = createButton(companyName);
            button.id = 'careers-button';

            // Append the button below the company name section
            companyLink.parentElement.appendChild(button);
        } else if (retriesLeft > 0) {
            console.log('Retying: retries lefft: ', retriesLeft);
            setTimeout(() => tryInject(retriesLeft - 1), RETRY_INTERVAL_MS);
        }
    }

    setTimeout(() => tryInject(MAX_RETRIES), 5000);
})();
