// ==UserScript==
// @name         LinkedIn Job Excel Scraper
// @namespace    http://tampermonkey.net/
// @version      1.3
// @description  Add line to clipboard to paste in job posting Excel file (LinkedIn version)
// @author       You
// @include      *linkedin.com/jobs/view*
// @match        https://www.linkedin.com/jobs/view/*
// @grant        none
// @run-at       document-end
// ==/UserScript==

(function () {
    'use strict';

    const MAX_RETRIES = 10;
    const RETRY_INTERVAL_MS = 500;

    function copyToClipboard(text) {
        navigator.clipboard.writeText(text).then(() => {
            console.log('Job data copied to clipboard!');
            showNotification('Job data copied to clipboard!');
        }).catch(err => {
            console.error('Clipboard copy failed, falling back:', err);
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
        Object.assign(notification.style, {
            position: 'fixed',
            top: '20px',
            right: '20px',
            backgroundColor: '#0073b1', // LinkedIn blue
            color: '#fff',
            padding: '10px 15px',
            borderRadius: '5px',
            zIndex: '10000',
            fontSize: '14px',
            fontWeight: 'bold'
        });
        document.body.appendChild(notification);
        setTimeout(() => notification.remove(), 3000);
    }

    function getJobUrl() {
        const match = window.location.href.match(/https:\/\/www\.linkedin\.com\/jobs\/view\/(\d+)/);
        if (match && match[1]) {
            return `https://www.linkedin.com/jobs/view/${match[1]}/`;
        }
        return window.location.href;
    }

    function createCopyButton() {
        const button = document.createElement('button');
        button.textContent = 'Copy Job Data';
        Object.assign(button.style, {
            backgroundColor: '#0073b1',
            color: '#fff',
            border: 'none',
            borderRadius: '20px',
            padding: '10px 16px',
            cursor: 'pointer',
            fontWeight: 'bold',
            marginLeft: '12px',
            fontSize: '14px',
            display: 'inline-block'
        });

        button.addEventListener('click', () => {
            // 7th a tag
            const companyElement = document.querySelectorAll('a')[9];
            // 4th p tag
            const jobTitleElement = document.querySelectorAll('h1')[0];

            if (!jobTitleElement || !companyElement) {
                alert('Could not find job title or company name.');
                return;
            }

            const jobTitle = jobTitleElement.textContent.trim();
            const company = companyElement.textContent.trim();
            const websiteFirstFound = 'LinkedIn';
            const appliedOnCompanySite = '';
            const customizedResume = '';
            const jobPost = getJobUrl();
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
        const saveButtons = document.querySelectorAll('.jobs-save-button');
        // 7th a tag
        const companyLink = document.querySelectorAll('a')[6];
        // 4th p tag
        const jobTitle = document.querySelectorAll('p')[3];

        if (saveButtons.length >= 2 && companyLink && jobTitle && companyLink.textContent.trim() && jobTitle.textContent.trim()) {
            // Check if button already exists
            if (document.getElementById('copy-job-data-button')) return;

            const button = createCopyButton();
            button.id = 'copy-job-data-button';

            // Insert after the second save button
            const secondSaveButton = saveButtons[1];
            secondSaveButton.insertAdjacentElement('afterend', button);

            console.log('Copy Job Data button injected after second save button!');
        } else if (retriesLeft > 0) {
            console.log(saveButtons.length,companyLink,jobTitle, companyLink.textContent.trim(), jobTitle.textContent.trim());
            console.log('Retrying: retries left: ', retriesLeft);
            setTimeout(() => tryInject(retriesLeft - 1), RETRY_INTERVAL_MS);
        } else {
            console.log('Failed to inject button after maximum retries');
        }
    }


    setTimeout(() => tryInject(MAX_RETRIES), 2000);
})();
