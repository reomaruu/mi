from pathlib import Path
import re

START = "<!-- MI_EMBEDDED_PAGE_LOADER_START -->"
END = "<!-- MI_EMBEDDED_PAGE_LOADER_END -->"

LOADER = r'''
<!-- MI_EMBEDDED_PAGE_LOADER_START -->
<script id="mi-internal-page-loader">
(() => {
    'use strict';

    const PAGE_FILES = {
        portal: 'index.html',
        programming: 'p.html',
        sns: 's.html',
        movie: 'd.html',
        design: 'de.html'
    };

    const SITE_URLS = {
        portal: 'https://sites.google.com/view/mi-lab/mi-lab',
        programming: 'https://sites.google.com/view/mi-lab/programming',
        sns: 'https://sites.google.com/view/mi-lab/sns',
        movie: 'https://sites.google.com/view/mi-lab/movie',
        design: 'https://sites.google.com/view/mi-lab/design'
    };

    function resolveInternalPage(href) {
        if (!href) return null;

        const value = href.trim();
        const lower = value.toLowerCase();
        const isGoogleSites = lower.startsWith('https://sites.google.com/view/mi-lab/');
        const isGithubPages = lower.startsWith('https://reomaruu.github.io/mi/');
        const isLocalFile = /^(?:\.\/|\.\.\/)?(?:index|p|s|d|de)\.html(?:#.*)?$/i.test(value);

        if (!isGoogleSites && !isGithubPages && !isLocalFile) return null;

        const fragmentIndex = value.indexOf('#');
        const fragment = fragmentIndex >= 0 ? value.slice(fragmentIndex) : '';
        const pathOnly = fragmentIndex >= 0 ? lower.slice(0, fragmentIndex) : lower;

        let key = null;
        if (/(?:\/programming|\/p\.html)$/.test(pathOnly)) key = 'programming';
        else if (/(?:\/sns|\/s\.html)$/.test(pathOnly)) key = 'sns';
        else if (/(?:\/movie|\/d\.html)$/.test(pathOnly)) key = 'movie';
        else if (/(?:\/design|\/de\.html)$/.test(pathOnly)) key = 'design';
        else if (/(?:\/mi-lab|\/home|\/index\.html)$/.test(pathOnly) || /^index\.html$/i.test(pathOnly)) key = 'portal';
        else if (/^p\.html$/i.test(pathOnly)) key = 'programming';
        else if (/^s\.html$/i.test(pathOnly)) key = 'sns';
        else if (/^d\.html$/i.test(pathOnly)) key = 'movie';
        else if (/^de\.html$/i.test(pathOnly)) key = 'design';

        return key ? { key, file: PAGE_FILES[key], fragment, fallbackUrl: SITE_URLS[key] + fragment } : null;
    }

    function showLoading() {
        let overlay = document.getElementById('mi-page-loading-overlay');
        if (!overlay) {
            overlay = document.createElement('div');
            overlay.id = 'mi-page-loading-overlay';
            overlay.setAttribute('aria-live', 'polite');
            Object.assign(overlay.style, {
                position: 'fixed',
                inset: '0',
                zIndex: '2147483647',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                padding: '24px',
                background: 'rgba(0, 0, 0, 0.42)',
                backdropFilter: 'blur(4px)',
                WebkitBackdropFilter: 'blur(4px)'
            });
            const box = document.createElement('div');
            box.textContent = 'ページを読み込んでいます…';
            Object.assign(box.style, {
                padding: '18px 24px',
                borderRadius: '12px',
                background: 'var(--section-bg, #fff)',
                color: 'var(--text-color, #333)',
                boxShadow: '0 12px 32px rgba(0,0,0,.25)',
                fontWeight: 'bold'
            });
            overlay.appendChild(box);
            document.body.appendChild(overlay);
        }
        return overlay;
    }

    function showLoadError(overlay, fallbackUrl) {
        if (!overlay) return;
        overlay.innerHTML = '';
        const box = document.createElement('div');
        Object.assign(box.style, {
            maxWidth: '520px',
            padding: '22px',
            borderRadius: '12px',
            background: 'var(--section-bg, #fff)',
            color: 'var(--text-color, #333)',
            boxShadow: '0 12px 32px rgba(0,0,0,.25)',
            textAlign: 'center'
        });
        const message = document.createElement('p');
        message.textContent = 'ページの読み込みに失敗しました。通信状態を確認して、もう一度押してください。';
        message.style.margin = '0 0 14px';
        const retry = document.createElement('button');
        retry.type = 'button';
        retry.textContent = '閉じる';
        retry.addEventListener('click', () => overlay.remove());
        Object.assign(retry.style, {
            padding: '10px 18px',
            borderRadius: '8px',
            border: '1px solid currentColor',
            background: 'transparent',
            color: 'inherit',
            cursor: 'pointer'
        });
        box.append(message, retry);
        overlay.appendChild(box);
        console.warn('Mi-lab page load failed. Fallback URL:', fallbackUrl);
    }

    async function fetchPageHtml(file) {
        const rawUrl = `https://raw.githubusercontent.com/reomaruu/mi/main/${encodeURIComponent(file)}?v=${Date.now()}`;
        try {
            const rawResponse = await fetch(rawUrl, { cache: 'no-store' });
            if (rawResponse.ok) {
                const html = await rawResponse.text();
                if (/<!doctype\s+html|<html[\s>]/i.test(html)) return html;
            }
        } catch (error) {
            console.warn('Raw GitHub fetch failed:', error);
        }

        const apiUrl = `https://api.github.com/repos/reomaruu/mi/contents/${encodeURIComponent(file)}?ref=main&_=${Date.now()}`;
        const apiResponse = await fetch(apiUrl, {
            cache: 'no-store',
            headers: { Accept: 'application/vnd.github+json' }
        });
        if (!apiResponse.ok) throw new Error(`GitHub API returned ${apiResponse.status}`);

        const data = await apiResponse.json();
        const encoded = String(data.content || '').replace(/\s/g, '');
        if (!encoded) throw new Error('GitHub API returned no file content');

        const binary = atob(encoded);
        const bytes = Uint8Array.from(binary, char => char.charCodeAt(0));
        return new TextDecoder('utf-8').decode(bytes);
    }

    function addInitialScroll(html, fragment) {
        if (!fragment) return html;
        const id = decodeURIComponent(fragment.slice(1));
        const script = `<script>window.addEventListener('load',function(){var el=document.getElementById(${JSON.stringify(id)});if(el){setTimeout(function(){el.scrollIntoView({behavior:'auto',block:'start'});},80);}});<\/script>`;
        return /<\/body>/i.test(html) ? html.replace(/<\/body>/i, `${script}</body>`) : html + script;
    }

    async function loadInternalPage(request) {
        const overlay = showLoading();
        try {
            let html = await fetchPageHtml(request.file);
            html = addInitialScroll(html, request.fragment);
            document.open('text/html', 'replace');
            document.write(html);
            document.close();
        } catch (error) {
            console.error('Mi-lab internal navigation failed:', error);
            showLoadError(overlay, request.fallbackUrl);
        }
    }

    document.addEventListener('click', event => {
        if (event.button !== 0 || event.metaKey || event.ctrlKey || event.shiftKey || event.altKey) return;
        const anchor = event.target.closest && event.target.closest('a[href]');
        if (!anchor) return;

        const request = resolveInternalPage(anchor.getAttribute('href'));
        if (!request) return;

        event.preventDefault();
        event.stopPropagation();
        event.stopImmediatePropagation();

        const toggle = document.getElementById('menu-toggle');
        if (toggle) toggle.checked = false;
        loadInternalPage(request);
    }, true);

    window.miLoadPage = key => {
        const file = PAGE_FILES[key];
        if (!file) return;
        loadInternalPage({ key, file, fragment: '', fallbackUrl: SITE_URLS[key] });
    };

    window.navigateTo = window.miLoadPage;
})();
</script>
<!-- MI_EMBEDDED_PAGE_LOADER_END -->
'''.strip()

pattern = re.compile(re.escape(START) + r'.*?' + re.escape(END), re.DOTALL)
changed = []

for path in sorted(Path('.').glob('*.html')):
    original = path.read_text(encoding='utf-8')
    updated = pattern.sub('', original).rstrip()
    if '</body>' in updated:
        updated = updated.replace('</body>', LOADER + '\n</body>', 1)
    else:
        updated += '\n' + LOADER + '\n'

    if updated != original:
        path.write_text(updated, encoding='utf-8')
        changed.append(path.name)

print('Updated:', ', '.join(changed) if changed else 'no files')
