from pathlib import Path
import re

SITE_PAGES = {
    "index.html": "https://sites.google.com/view/mi-lab/mi-lab",
    "p.html": "https://sites.google.com/view/mi-lab/programming",
    "s.html": "https://sites.google.com/view/mi-lab/sns",
    "d.html": "https://sites.google.com/view/mi-lab/movie",
    "de.html": "https://sites.google.com/view/mi-lab/design",
}

ALIASES = {
    **SITE_PAGES,
    "https://reomaruu.github.io/mi/index.html": SITE_PAGES["index.html"],
    "https://reomaruu.github.io/mi/p.html": SITE_PAGES["p.html"],
    "https://reomaruu.github.io/mi/s.html": SITE_PAGES["s.html"],
    "https://reomaruu.github.io/mi/d.html": SITE_PAGES["d.html"],
    "https://reomaruu.github.io/mi/de.html": SITE_PAGES["de.html"],
    "https://sites.google.com/view/mi-lab/home": SITE_PAGES["index.html"],
}

WRAP_CSS = r'''

        /* 日本語の紹介文を自然な位置で折り返す */
        .hero p,
        section p,
        .group-card p,
        .activity-card p,
        .portfolio-card p,
        .contact-card p,
        .info-box p {
            white-space: normal;
            line-break: strict;
            word-break: normal;
            word-break: auto-phrase;
            overflow-wrap: break-word;
            text-wrap: pretty;
        }
'''

MARKER = "/* 日本語の紹介文を自然な位置で折り返す */"
INTERNAL_URL = re.compile(
    r'https://sites\.google\.com/view/mi-lab/(?:mi-lab|programming|sns|movie|design)(?:#[^"\']*)?',
    re.IGNORECASE,
)
ANCHOR = re.compile(r'<a\b[^>]*>', re.IGNORECASE)
TARGET = re.compile(r'\btarget\s*=\s*(["\'])[^"\']*\1', re.IGNORECASE)
HREF = re.compile(r'\bhref\s*=\s*(["\'])([^"\']+)\1', re.IGNORECASE)


def replace_aliases(html: str) -> str:
    for old, new in sorted(ALIASES.items(), key=lambda item: len(item[0]), reverse=True):
        html = re.sub(
            rf'(?P<quote>["\']){re.escape(old)}(?P<fragment>#[^"\']*)?(?P=quote)',
            lambda match, new=new: (
                f'{match.group("quote")}{new}{match.group("fragment") or ""}{match.group("quote")}'
            ),
            html,
        )
    return html


def fix_anchor(match: re.Match[str]) -> str:
    tag = match.group(0)
    href_match = HREF.search(tag)
    if not href_match or not INTERNAL_URL.fullmatch(href_match.group(2)):
        return tag

    if TARGET.search(tag):
        return TARGET.sub('target="_parent"', tag, count=1)
    return tag[:-1].rstrip() + ' target="_parent">'


def fix_html(html: str) -> str:
    html = replace_aliases(html)
    html = ANCHOR.sub(fix_anchor, html)

    html = re.sub(
        r'(window\.open\s*\(\s*[^,]+,\s*["\'])(?:_self|_top|_blank)(["\'])',
        r'\1_parent\2',
        html,
        flags=re.IGNORECASE,
    )

    html = re.sub(
        r'(<p\b[^>]*id=["\']hero-desc["\'][^>]*>.*?)<br\s*/?>(.*?</p>)',
        r'\1 \2',
        html,
        flags=re.IGNORECASE | re.DOTALL,
    )

    if MARKER not in html:
        html = html.replace('</style>', WRAP_CSS + '\n    </style>', 1)

    return html


changed = []
for path in sorted(Path('.').glob('*.html')):
    original = path.read_text(encoding='utf-8')
    updated = fix_html(original)
    if updated != original:
        path.write_text(updated, encoding='utf-8')
        changed.append(path.name)

print('Updated:', ', '.join(changed) if changed else 'no files')
