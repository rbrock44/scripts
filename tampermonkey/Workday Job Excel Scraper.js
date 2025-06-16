// ==UserScript==
// @name         Workday Job Excel Scraper
// @namespace    http://tampermonkey.net/
// @version      1.0
// @description  Copy job info from Workday jobs to clipboard for Excel pasting
// @author       You
// @match        https://*.myworkdayjobs.com/en-US/Careers/job/*
// @grant        none
// @run-at       document-end
// ==/UserScript==

(function () {
    'use strict';

    const JOB_TITLE_SELECTOR = '[data-automation-id="jobPostingHeader"]';
    const REQUISITION_ID_SELECTOR = '[data-automation-id="requisitionId"] dd';
    const MAX_RETRIES = 10;
    const RETRY_INTERVAL_MS = 500;

    function copyToClipboard(text) {
        navigator.clipboard.writeText(text).then(() => {
            showNotification('Job data copied to clipboard!');
        }).catch(err => {
            console.error('Clipboard write failed, using fallback:', err);
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
            backgroundColor: '#0073b1',
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

    function createCopyButton() {
        const button = document.createElement('button');
        button.textContent = 'Copy Job Data';
        Object.assign(button.style, {
            backgroundColor: '#0a66c2',
            color: '#fff',
            border: 'none',
            borderRadius: '20px',
            padding: '10px 16px',
            cursor: 'pointer',
            fontWeight: 'bold',
            fontSize: '14px',
            marginTop: '10px'
        });

        button.addEventListener('click', () => {
            const jobTitleEl = document.querySelector(JOB_TITLE_SELECTOR);
            const reqIdEl = document.querySelector(REQUISITION_ID_SELECTOR);

            if (!jobTitleEl || !reqIdEl) {
                alert('Job title or requisition ID not found. Wait for page to fully load.');
                return;
            }

            const jobTitle = jobTitleEl.textContent.trim();
            const reqId = reqIdEl.textContent.trim();
            const fullTitle = `${jobTitle} - ${reqId}`;
            const company = window.location.hostname.split('.')[0]; // e.g., companyname.myworkdayjobs.com
            const websiteFirstFound = '';
            const appliedOnCompanySite = 'Yes';
            const customizedResume = '';
            const jobPost = window.location.href;
            const empty1 = '';
            const jobPortal = window.location.origin + '/en-US/careers/userHome';

            const currentDate = new Date();
            const dateApplied = `${String(currentDate.getMonth() + 1).padStart(2, '0')}/${String(currentDate.getDate()).padStart(2, '0')}/${currentDate.getFullYear()}`;

            const jobData = [
                fullTitle,
                company,
                websiteFirstFound,
                appliedOnCompanySite,
                customizedResume,
                jobPost,
                jobPortal,
                empty1,
                dateApplied
            ].join('\t');

            copyToClipboard(jobData);
        });

        return button;
    }

    function tryInject(retriesLeft) {
        const jobTitleEl = document.querySelector(JOB_TITLE_SELECTOR);
        const reqIdEl = document.querySelector(REQUISITION_ID_SELECTOR);

        if (jobTitleEl && reqIdEl && !document.getElementById('copy-job-data-button')) {
            const button = createCopyButton();
            button.id = 'copy-job-data-button';

            // Insert after job title
            jobTitleEl.parentNode.appendChild(button);
            console.log('Copy Job Data button injected!');
        } else if (retriesLeft > 0) {
            console.log(`Waiting for page to load... (${retriesLeft} retries left)`);
            setTimeout(() => tryInject(retriesLeft - 1), RETRY_INTERVAL_MS);
        } else {
            console.warn('Failed to inject button after maximum retries.');
        }
    }

    setTimeout(() => tryInject(MAX_RETRIES), 2000);
})();
