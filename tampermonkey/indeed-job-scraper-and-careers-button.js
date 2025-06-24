// ==UserScript==
// @name         Indeed Job Excel Scraper and Career Button
// @namespace    http://tampermonkey.net/
// @version      1.1
// @description  Add line to clipboard to paste in job posting excel file
// @author       You
// @match        https://www.indeed.com/viewjob*
// @grant        none
// @run-at       document-end
// ==/UserScript==

(function () {
    'use strict';

    const COMPANY_SELECTOR = '[data-testid="inlineHeader-companyName"]';
    const JOB_TITLE_SELECTOR = '.jobsearch-JobInfoHeader-title-container';
    const TARGET_CONTAINER_SELECTOR = '.jobsearch-JobInfoHeader-title-container';
    const MAX_RETRIES = 10;
    const RETRY_INTERVAL_MS = 500;
    const BUTTON_ID = 'indeed-careers-button';

    function copyToClipboard(text) {
        navigator.clipboard.writeText(text).then(() => {
            console.log('Job data copied to clipboard!');
            showNotification('Job data copied to clipboard!');
        }).catch(err => {
            console.error('Failed to copy to clipboard:', err);
            const textArea = document.createElement('textarea');
            textArea.value = text;
            document.body.appendChild(textArea);
            textArea.select();
            document.execCommand('copy');
            document.body.removeChild(textArea);
            showNotification('Job data copied to clipboard!');
        });
    }

    function showNotification(message) {
        const notification = document.createElement('div');
        notification.textContent = message;
        notification.style.position = 'fixed';
        notification.style.top = '20px';
        notification.style.right = '20px';
        notification.style.backgroundColor = '#2557a7'; // Indeed blue
        notification.style.color = '#fff';
        notification.style.padding = '10px 15px';
        notification.style.borderRadius = '5px';
        notification.style.zIndex = '10000';
        notification.style.fontSize = '14px';
        notification.style.fontWeight = 'bold';

        document.body.appendChild(notification);

        setTimeout(() => {
            notification.remove();
        }, 3000);
    }

    function getIndeedJobUrl() {
        const match = window.location.href.match(/https:\/\/www\.indeed\.com\/viewjob\?[^#]*?jk=([a-zA-Z0-9]+)/);
        if (match && match[1]) {
            return `https://www.indeed.com/viewjob?jk=${match[1]}`;
        }
        return window.location.href;
    }

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

    function createCopyButton() {
        const button = document.createElement('button');
        button.textContent = 'Copy Job Data';
        button.style.backgroundColor = '#2557a7';
        button.style.color = '#fff';
        button.style.border = 'none';
        button.style.borderRadius = '20px';
        button.style.padding = '10px 16px';
        button.style.cursor = 'pointer';
        button.style.fontWeight = 'bold';
        button.style.marginLeft = '12px';
        button.style.fontSize = '14px';
        button.style.display = 'inline-block';

        button.addEventListener('click', () => {
            const companyElement = document.querySelector(COMPANY_SELECTOR);
            const jobTitleElement = document.querySelector(JOB_TITLE_SELECTOR);

            if (!companyElement || !jobTitleElement) {
                alert('Could not find job details. Please make sure the page is fully loaded.');
                return;
            }

            const jobTitle = jobTitleElement.textContent.trim()
                .replace('Copy Job Data','')
                .replace('Go To Careers', '');
            const company = companyElement.textContent.trim();
            const websiteFirstFound = 'Indeed';
            const appliedOnCompanySite = '';
            const customizedResume = '';
            const jobPost = getIndeedJobUrl();
            const emptyValue1 = '';
            const emptyValue2 = '';
            const currentDate = new Date();
            const dateApplied = `${String(currentDate.getMonth() + 1).padStart(2, '0')}/${String(currentDate.getDate()).padStart(2, '0')}/${currentDate.getFullYear()}`;

            const jobData = [
                jobTitle,
                company,
                websiteFirstFound,
                appliedOnCompanySite,
                customizedResume,
                jobPost,
                emptyValue1,
                emptyValue2,
                dateApplied
            ].join('\t');

            copyToClipboard(jobData);
        });

        return button;
    }

    function tryInject(retriesLeft) {
        const targetContainer = document.querySelector(TARGET_CONTAINER_SELECTOR);
        const companyElement = document.querySelector(COMPANY_SELECTOR);
        const jobTitleElement = document.querySelector(JOB_TITLE_SELECTOR);

        if (targetContainer && companyElement && jobTitleElement && companyElement.textContent.trim() && jobTitleElement.textContent.trim()) {

            if (!document.getElementById('copy-job-data-button') ) {
                const button = createCopyButton();
                button.id = 'copy-job-data-button';

                targetContainer.appendChild(button);
                console.log('Indeed copy job data button injected successfully!');
            }

            if (!document.getElementById(BUTTON_ID) ) {
                const button = createCareersButton(companyElement.textContent.trim());

                targetContainer.appendChild(button);
                console.log('Indeed career button injected successfully!');

            }

        } else if (retriesLeft > 0) {
            console.log('Retrying injection... Retries left:', retriesLeft);
            setTimeout(() => tryInject(retriesLeft - 1), RETRY_INTERVAL_MS);
        } else {
            console.log('Failed to inject button after maximum retries.');
        }
    }

    setTimeout(() => tryInject(MAX_RETRIES), 2000);
})();
