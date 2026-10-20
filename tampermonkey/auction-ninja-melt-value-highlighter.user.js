// ==UserScript==
// @name         AuctionNinja Melt Value Highlighter
// @namespace    https://github.com/rbrock44/scripts
// @version      1.5.1
// @description  Highlights AuctionNinja lots whose current bid is under 80% of melt value, using live spot prices from home-page-api
// @author       Rbrock44
// @match        https://www.auctionninja.com/*
// @icon         https://www.google.com/s2/favicons?sz=64&domain=auctionninja.com
// @grant        GM_xmlhttpRequest
// @grant        GM_getValue
// @grant        GM_setValue
// @connect      home-page-api.ryan-brock.com
// @license      MIT
// @supportURL   https://github.com/rbrock44/scripts/issues
// @homepageURL  https://github.com/rbrock44/scripts/tree/master/tampermonkey
// @updateURL    https://raw.githubusercontent.com/rbrock44/scripts/master/tampermonkey/auction-ninja-melt-value-highlighter.user.js
// @downloadURL  https://raw.githubusercontent.com/rbrock44/scripts/master/tampermonkey/auction-ninja-melt-value-highlighter.user.js
// ==/UserScript==

(function() {
    'use strict';

    const SPOT_URL = 'https://home-page-api.ryan-brock.com/spot-price';
    const SPOT_CACHE_MS = 10 * 60 * 1000;
    // Add the auction's buyer's premium to the bid before comparing to melt
    const INCLUDE_BUYERS_PREMIUM = false;

    const GRAMS_PER_TROY_OZ = 31.1034768;

    // Index 0 = 70-80% of melt, each step another 10% cheaper and darker
    const GREENS = ['#d9f7d9', '#b3eeb3', '#8ce08c', '#62cc62', '#3fae3f', '#2a8a2a', '#1b661b', '#0f440f'];
    // 80-90%, 90-100%
    const YELLOWS = ['#fff7c7', '#ffe680'];
    // 100-125%, 125-150%, 150-175%, 175-200%, 200%+
    const REDS = ['#ffeaea', '#ffc9c9', '#ffa0a0', '#f06a6a', '#c93a3a'];
    // Metal, weight, or bid couldn't be parsed
    const UNPARSED_COLOR = '#f2f2f2';
    const PANEL_ROWS = 5;

    const UNITS = [
        { re: 'kilograms?|kilos?|kgs?', grams: 1000 },
        { re: 'pounds?|lbs?', grams: 453.59237 },
        { re: 'troy\\s*ounces?|troy\\s*oz|t\\.?\\s*oz|ozt|toz', grams: GRAMS_PER_TROY_OZ },
        { re: 'ounces?|oz', grams: 28.349523 },
        { re: 'dwt', grams: 1.55517384 },
        { re: 'grams?|gms?|grs?|g', grams: 1 },
    ];
    const WEIGHT_RE = new RegExp(
        '(\\d+\\s*\\/\\s*\\d+|\\d+(?:[.,]\\d+)?)\\s*(' + UNITS.map(u => u.re).join('|') + ')(?![a-z])', 'i'
    );
    // Plain "oz" on coins and bullion means troy
    const BULLION_RE = /coin|\bbar\b|round|bullion|ingot|\bfine\b|\.?999|eagle|maple|buffalo|panda|krugerrand|britannia|philharmonic|kangaroo|libertad/i;

    const GOLD_KARATS = { 8: 0.333, 9: 0.375, 10: 0.417, 12: 0.5, 14: 0.585, 18: 0.75, 21: 0.875, 22: 0.917, 24: 0.999 };

    // Fine metal content (troy oz) of common coins, checked in order so "half dollar" wins over "dollar"
    const COINS = [
        { name: 'Silver Eagle', re: /silver\s*eagle|\base\b/, metal: 'silver', ozt: 1 },
        { name: 'Silver Maple Leaf', re: /silver\s*maple/, metal: 'silver', ozt: 1 },
        { name: 'Gold Double Eagle $20', re: /double\s*eagle|\$20\s*(gold|liberty|saint)/, metal: 'gold', ozt: 0.9675 },
        { name: 'Gold Half Eagle $5', re: /half\s*eagle|\$5\s*(gold|liberty|indian)/, metal: 'gold', ozt: 0.24187 },
        { name: 'Gold Quarter Eagle $2.5', re: /quarter\s*eagle|\$2(\.5|\s*1\/2)\s*(gold|liberty|indian)/, metal: 'gold', ozt: 0.12094 },
        { name: 'Gold Eagle $10', re: /\$10\s*(gold|liberty|indian)|(liberty|indian)\s*(head\s*)?(gold\s*)?eagle/, metal: 'gold', ozt: 0.48375 },
        { name: 'Gold $3', re: /\$3\s*(gold|indian|princess)/, metal: 'gold', ozt: 0.14512 },
        { name: 'Gold Dollar', re: /gold\s*dollar|\$1\s*gold/, metal: 'gold', ozt: 0.04837 },
        { name: 'War Nickel 35%', re: /war\s*nickel|(silver.*(jefferson|5c|nickel))|((jefferson|5c|nickel).*silver)/, metal: 'silver', ozt: 0.05626, years: [1942, 1945] },
        { name: 'Canada Dollar 80%', re: /canada.*(dollar|\$1)/, metal: 'silver', ozt: 0.6, years: [1935, 1967] },
        { name: 'Canada 50c 80%', re: /canada.*(50\s*cents?|half)/, metal: 'silver', ozt: 0.3, years: [1920, 1967] },
        { name: 'Canada 25c 80%', re: /canada.*(25\s*cents?|quarter)/, metal: 'silver', ozt: 0.15, years: [1920, 1967] },
        { name: 'Canada 10c 80%', re: /canada.*(10\s*cents?|dime)/, metal: 'silver', ozt: 0.06, years: [1920, 1967] },
        { name: 'Half Dime 90%', re: /half\s*dime/, metal: 'silver', ozt: 0.03617 },
        { name: 'Kennedy Half 40%', re: /kennedy/, metal: 'silver', ozt: 0.14792, years: [1965, 1970] },
        { name: 'Half Dollar 90%', re: /barber.*half|walking\s*liberty|franklin|seated.*half|columbian|kennedy|silver\s*half/, metal: 'silver', ozt: 0.36169, silverYears: true },
        { name: 'Quarter 90%', re: /barber.*quarter|standing\s*liberty|seated.*quarter|washington.*quarter|silver\s*quarter/, metal: 'silver', ozt: 0.18084, silverYears: true },
        { name: 'Dime 90%', re: /mercury|barber.*dime|seated.*dime|roosevelt|silver\s*dime/, metal: 'silver', ozt: 0.07234, silverYears: true },
        { name: 'Eisenhower Dollar 40%', re: /eisenhower|\bike\b/, metal: 'silver', ozt: 0.31610, years: [1971, 1976], needsSilver: true },
        { name: 'Morgan/Peace Dollar 90%', re: /morgan|peace\s*(silver\s*)?dollar|trade\s*dollar|seated.*dollar|silver\s*dollar/, metal: 'silver', ozt: 0.77344, silverYears: true, exclude: /eisenhower|\bike\b|susan|anthony|sacagawea|presidential/ },
    ];

    function parseNumber(raw) {
        const fraction = raw.match(/^(\d+)\s*\/\s*(\d+)$/);
        if (fraction) return parseInt(fraction[1], 10) / parseInt(fraction[2], 10);
        // "1,250" is thousands, "9,2" is a decimal comma
        if (/^\d{1,3},\d{3}$/.test(raw)) return parseFloat(raw.replace(',', ''));
        return parseFloat(raw.replace(',', '.'));
    }

    function parseWeight(title) {
        const match = title.match(WEIGHT_RE);
        if (!match) return null;
        const amount = parseNumber(match[1]);
        let unit = UNITS.find(u => new RegExp('^(?:' + u.re + ')$', 'i').test(match[2]));
        if (!unit || isNaN(amount) || amount <= 0) return null;
        const isOunce = /oz|ounce/i.test(match[2]);
        if (isOunce && unit.grams !== GRAMS_PER_TROY_OZ && BULLION_RE.test(title)) unit = UNITS[2];
        return { grams: amount * unit.grams, isOunce };
    }

    function parseCoin(title) {
        const t = title.toLowerCase();
        // Paper money and clad/plated pieces have no melt
        if (/certificate|\bnote\b|\bclad\b|plated|copy|replica|token/.test(t)) return null;
        // Latest year wins so "1776-1976" bicentennials read as 1976
        const years = (t.match(/\b(1[789]\d{2}|20\d{2})\b/g) || []).map(y => parseInt(y, 10));
        const year = years.length ? Math.max(...years) : null;

        for (const coin of COINS) {
            if (!coin.re.test(t)) continue;
            if (coin.exclude && coin.exclude.test(t)) continue;
            if (coin.years && (!year || year < coin.years[0] || year > coin.years[1])) continue;
            if (coin.needsSilver && !/silver/.test(t)) continue;
            // US 90% coinage ended 1964, silver commemoratives came back in 1982
            if (coin.silverYears && year && year > 1964 && !(year >= 1982 && /silver|commemorative/.test(t))) continue;
            return { metal: coin.metal, fineOz: coin.ozt, detail: coin.name };
        }
        return null;
    }

    function parseLot(title) {
        const metal = parseMetal(title);
        const weight = parseWeight(title);

        if (metal && weight) {
            const fineOz = weight.grams / GRAMS_PER_TROY_OZ * metal.purity;
            return { metal: metal.metal, fineOz, detail: `${weight.grams.toFixed(2)}g @ ${(metal.purity * 100).toFixed(1)}%` };
        }

        // "1/10 oz Gold Eagle" - bullion coins state fine content, so no purity needed
        const t = title.toLowerCase();
        const bareMetal = /platinum/.test(t) ? 'platinum' : /gold/.test(t) ? 'gold' : /silver/.test(t) ? 'silver' : null;
        if (!metal && weight && weight.isOunce && bareMetal && BULLION_RE.test(title)) {
            const fineOz = weight.grams / GRAMS_PER_TROY_OZ;
            return { metal: bareMetal, fineOz, detail: `${fineOz.toFixed(4)} ozt fine` };
        }

        return parseCoin(title);
    }

    function parseMetal(title) {
        const t = title.toLowerCase();

        // Plated / filled gold is worthless as gold, but "gold over sterling" is still sterling
        const fakeGold = /gold\s*(over|tone|toned|filled|plated|plate|wash|electroplate)|\bgf\b|\bgp\b|\bgep\b|vermeil|rolled\s*gold/.test(t);
        const fakeSilver = /silver\s*(plate|plated|tone|toned|over)|\bsp\b|\bepns\b|nickel\s*silver|german\s*silver/.test(t);

        if (!fakeGold) {
            const karat = t.match(/\b(8|9|10|12|14|18|21|22|24)\s*(?:k|kt|karat|carat|ct)\b/);
            if (karat && /gold|\d\s*k/.test(t)) return { metal: 'gold', purity: GOLD_KARATS[karat[1]] };
            const fineness = t.match(/\b(333|375|417|585|750|875|916|917|999|9999)\b/);
            if (fineness && /gold/.test(t)) return { metal: 'gold', purity: parseInt(fineness[1], 10) / 10 ** fineness[1].length };
        }

        if (/platinum|\bplat\b|\bpt\s*\d{3}\b/.test(t)) {
            const fineness = t.match(/\b(850|900|950|999)\b/);
            return { metal: 'platinum', purity: fineness ? parseInt(fineness[1], 10) / 1000 : 0.95 };
        }

        if (/sterling|\b925\b|\.925\b/.test(t)) return { metal: 'silver', purity: 0.925 };
        if (!fakeSilver) {
            if (/fine\s*silver|\b9999?\b|silver\s*(bar|round|bullion)/.test(t)) return { metal: 'silver', purity: 0.999 };
            if (/coin\s*silver|\b900\s*silver/.test(t)) return { metal: 'silver', purity: 0.9 };
            if (/\b800\b/.test(t) && /silver/.test(t)) return { metal: 'silver', purity: 0.8 };
        }
        return null;
    }

    function parseBuyersPremium() {
        const boxes = document.querySelectorAll('.auction-detail-top-img-detail-box');
        for (const box of boxes) {
            if (/buyer'?s premium/i.test(box.textContent)) {
                const pct = box.querySelector('p')?.textContent.match(/(\d+(?:\.\d+)?)\s*%/);
                if (pct) return parseFloat(pct[1]) / 100;
            }
        }
        return 0;
    }

    function fetchSpotPrices() {
        const cached = GM_getValue('spotPrices', null);
        if (cached && Date.now() - cached.fetchedAt < SPOT_CACHE_MS) return Promise.resolve(cached);

        return new Promise((resolve, reject) => {
            GM_xmlhttpRequest({
                method: 'GET',
                url: SPOT_URL,
                timeout: 60000, // heroku cold start
                onload: res => {
                    try {
                        const data = JSON.parse(res.responseText);
                        const prices = { gold: data.gold, silver: data.silver, platinum: data.platinum, fetchedAt: Date.now() };
                        GM_setValue('spotPrices', prices);
                        resolve(prices);
                    } catch (e) {
                        reject(e);
                    }
                },
                onerror: reject,
                ontimeout: () => reject(new Error('spot price request timed out')),
            });
        });
    }

    function colorFor(ratio) {
        if (ratio < 0.8) {
            const i = Math.min(Math.floor((0.8 - ratio) * 10 + 1e-9), GREENS.length - 1);
            return { bg: GREENS[i], darkBg: i >= 4 };
        }
        if (ratio < 1) return { bg: YELLOWS[ratio < 0.9 ? 0 : 1], darkBg: false };
        const i = Math.min(Math.floor((ratio - 1) * 4 + 1e-9), REDS.length - 1);
        return { bg: REDS[i], darkBg: i >= 3 };
    }

    // Info icon on the image's top left (mirrors the heart on the right), click drops down bid levels
    function addInfoPanel(box, melt, ratio, premium) {
        const imgWrap = box.querySelector('.hot-items-img');
        if (!imgWrap) return;
        if (getComputedStyle(imgWrap).position === 'static') imgWrap.style.position = 'relative';

        let wrap = imgWrap.querySelector('.melt-info');
        if (!wrap) {
            wrap = document.createElement('div');
            wrap.className = 'melt-info';
            wrap.style.cssText = 'position:absolute;top:8px;left:8px;z-index:20;';

            const icon = document.createElement('a');
            icon.href = '#';
            icon.title = 'Melt value bid levels';
            icon.innerHTML = '<i class="fa fa-info-circle" aria-hidden="true"></i>';
            icon.style.cssText = 'display:flex;align-items:center;justify-content:center;width:30px;height:30px;' +
                'border-radius:50%;background:#fff;color:#068999;font-size:20px;text-decoration:none;box-shadow:0 1px 3px rgba(0,0,0,.3);';

            const panel = document.createElement('div');
            panel.className = 'melt-info-panel';
            panel.style.cssText = 'display:none;margin-top:4px;padding:6px 8px;background:#fff;color:#2d2d2d;' +
                'border-radius:6px;box-shadow:0 2px 8px rgba(0,0,0,.3);font-size:12px;line-height:1.6;white-space:nowrap;';

            icon.addEventListener('click', e => {
                e.preventDefault();
                e.stopPropagation();
                panel.style.display = panel.style.display === 'none' ? 'block' : 'none';
            });

            wrap.append(icon, panel);
            imgWrap.appendChild(wrap);
        }

        // Over 100% the table starts at the current ratio rounded down to 10% (123% -> 120, 110, 100, 90, 80)
        const startPct = ratio > 1 ? Math.floor(ratio * 10 + 1e-9) * 10 : 100;

        // Bid that lands at each % of melt, backing out the premium when it's included
        const rows = Array.from({ length: PANEL_ROWS }, (_, i) => startPct - i * 10).map(pct => {
            const color = colorFor(pct / 100);
            const text = color.darkBg ? '#fff' : '#2d2d2d';
            return `<div style="display:flex;justify-content:space-between;gap:12px;padding:0 6px;margin:1px 0;` +
                `border-radius:3px;background:${color.bg};color:${text};">` +
                `<span style="color:${text};">${pct}%</span>` +
                `<b>$${(melt * pct / 100 / (1 + premium)).toFixed(2)}</b></div>`;
        }).join('');
        wrap.querySelector('.melt-info-panel').innerHTML = rows;
    }

    function highlight(spot, premium) {
        document.querySelectorAll('.search-catalog-item-box').forEach(box => {
            const titleEl = box.querySelector('.hot-items-title a');
            const priceEl = box.querySelector('.ci-price');
            const inner = box.querySelector('.search-catalog-item-box-in') || box;
            if (!titleEl || !priceEl) return;

            const title = titleEl.textContent.trim();
            const bid = parseFloat(priceEl.textContent.replace(/[$,\s]/g, ''));
            const key = title + '|' + bid;
            if (box.dataset.meltKey === key) return;
            box.dataset.meltKey = key;

            const lot = parseLot(title);
            const spotPrice = lot && spot[lot.metal];
            if (!lot || !(spotPrice > 0) || isNaN(bid)) {
                inner.style.backgroundColor = UNPARSED_COLOR;
                return;
            }

            const melt = lot.fineOz * spotPrice;
            const cost = bid * (1 + premium);
            const ratio = cost / melt;
            const color = colorFor(ratio);

            let badge = box.querySelector('.melt-value-badge');
            if (!badge) {
                badge = document.createElement('div');
                badge.className = 'melt-value-badge';
                badge.style.cssText = 'font-size:12px;font-weight:bold;margin-top:2px;';
                priceEl.insertAdjacentElement('afterend', badge);
            }
            badge.textContent = `Melt $${melt.toFixed(2)} | ${Math.round(ratio * 100)}%`;
            badge.title = `${lot.detail}, ${lot.fineOz.toFixed(4)} ozt ${lot.metal}, spot $${spotPrice}/ozt` +
                (premium ? `, incl ${Math.round(premium * 100)}% premium` : '');

            addInfoPanel(box, melt, ratio, premium);

            const textColor = color.darkBg ? '#fff' : '';
            inner.style.backgroundColor = color.bg;
            inner.style.color = textColor;
            inner.querySelectorAll('a, .ci-price, span, p, .melt-value-badge').forEach(el => {
                if (!el.closest('.melt-info')) el.style.color = textColor;
            });
        });
    }

    fetchSpotPrices().then(spot => {
        const premium = INCLUDE_BUYERS_PREMIUM ? parseBuyersPremium() : 0;
        let timer = null;
        const run = () => highlight(spot, premium);
        run();
        // Bids update live, re-run when the catalog changes
        new MutationObserver(() => {
            clearTimeout(timer);
            timer = setTimeout(run, 300);
        }).observe(document.body, { childList: true, subtree: true, characterData: true });
    }).catch(err => console.error('[melt highlighter] could not load spot prices', err));

})();
