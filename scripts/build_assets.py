#!/usr/bin/env python3
"""Build profile header and toolkit artwork with the Python standard library."""
from html import escape
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / 'assets'
ASSETS.mkdir(exist_ok=True)
FONT = '-apple-system, BlinkMacSystemFont, Segoe UI, Arial, PingFang SC, Microsoft YaHei, sans-serif'
THEMES = {
    'dark': dict(bg='#111629', panel='#192039', fg='#F3F5FF', muted='#A8B4D1', line='#2D3654', violet='#AFA4FF', blue='#75D1F5', mint='#82D5B6'),
    'light': dict(bg='#F3F5FF', panel='#FFFFFF', fg='#222943', muted='#5E6886', line='#DDE3F3', violet='#6655C8', blue='#147FA5', mint='#21806B'),
}


def text(x, y, value, size, color, weight=400, anchor='start'):
    return f'<text x="{x}" y="{y}" font-size="{size}" fill="{color}" font-weight="{weight}" text-anchor="{anchor}">{escape(value)}</text>'


def svg(body, width, height, title, description):
    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}" role="img" aria-labelledby="title desc">
<title id="title">{escape(title)}</title><desc id="desc">{escape(description)}</desc>
<g font-family="{FONT}">{body}</g></svg>\n'''


def rect(x, y, w, h, fill, stroke='none', r=16):
    return f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="{r}" fill="{fill}" stroke="{stroke}"/>'


def hero(c):
    parts = [rect(1, 1, 1198, 278, c['bg'], c['line'], 20)]
    parts += [f'<circle cx="970" cy="140" r="106" fill="none" stroke="{c["line"]}" stroke-dasharray="3 10"/>',
              f'<circle cx="970" cy="140" r="67" fill="none" stroke="{c["line"]}"/>']
    for x, y, label, accent in [(868, 59, 'Tools', 'blue'), (1091, 95, 'Memory', 'violet'), (1001, 230, 'Checks', 'mint')]:
        parts.append(f'<path d="M970 140L{x} {y}" fill="none" stroke="{c[accent]}" stroke-width="1.5" opacity=".5"/>')
        parts += [rect(x-47, y-21, 94, 42, c['panel'], c['line'], 12), text(x, y+6, label, 17, c['muted'], anchor='middle')]
    parts += [f'<circle cx="970" cy="140" r="42" fill="{c["panel"]}" stroke="{c["violet"]}" stroke-width="1.5"/>',
              text(970, 147, 'Agent', 22, c['fg'], 500, 'middle')]
    parts += [text(48, 54, 'Mr.ooo', 27, c['fg'], 500),
              text(48, 123, 'AI tools & experiments', 46, c['fg'], 600),
              text(50, 166, 'AI 工具与智能体开发', 23, c['muted'])]
    parts.append(f'<path d="M50 199H714" stroke="{c["line"]}"/>')
    parts += [text(50, 240, 'Python / TypeScript', 18, c['muted']), text(711, 240, '@a252937166', 17, c['muted'], anchor='end')]
    return svg(''.join(parts), 1200, 280, 'Mr.ooo — AI tools & experiments', 'AI 工具与智能体开发。Python / TypeScript.')


def mobile_hero(c):
    parts = [rect(1, 1, 598, 278, c['bg'], c['line'], 20), text(28, 51, 'Mr.ooo', 27, c['fg'], 500),
             text(28, 118, 'AI tools & experiments', 40, c['fg'], 600), text(28, 164, 'AI 工具与智能体开发', 27, c['muted'])]
    parts.append(f'<path d="M28 195H571" stroke="{c["line"]}"/>')
    parts += [text(28, 242, 'Python / TypeScript', 24, c['muted']), text(571, 242, '@a252937166', 22, c['muted'], anchor='end')]
    return svg(''.join(parts), 600, 280, 'Mr.ooo — AI tools & experiments', 'AI 工具与智能体开发。')


def toolkit(c):
    parts = [rect(1, 1, 1198, 136, c['bg'], c['line'], 16),
             text(35, 48, 'Languages', 19, c['muted'], 500), text(35, 87, 'Python · TypeScript · Java', 20, c['fg']),
             text(535, 48, 'Frameworks & tools', 19, c['muted'], 500), text(535, 87, 'MCP · FastAPI · React · Vue · HyperFrames', 20, c['fg']),
             f'<path d="M495 28V108" stroke="{c["line"]}"/>']
    return svg(''.join(parts), 1200, 138, 'Tech stack', 'Python, TypeScript, Java, MCP, FastAPI, React, Vue and HyperFrames.')


def mobile_toolkit(c):
    parts = [rect(1, 1, 598, 228, c['bg'], c['line'], 20),
             text(28, 45, 'Languages', 24, c['muted'], 500), text(28, 83, 'Python · TypeScript · Java', 28, c['fg']),
             text(28, 138, 'Frameworks & tools', 24, c['muted'], 500), text(28, 180, 'MCP · FastAPI · React · Vue · HyperFrames', 24, c['fg'])]
    return svg(''.join(parts), 600, 230, 'Tech stack', 'Python, TypeScript, Java, MCP, FastAPI, React, Vue and HyperFrames.')


for theme, colors in THEMES.items():
    (ASSETS / f'hero-{theme}.svg').write_text(hero(colors), encoding='utf-8')
    (ASSETS / f'toolkit-{theme}.svg').write_text(toolkit(colors), encoding='utf-8')
    (ASSETS / f'toolkit-mobile-{theme}.svg').write_text(mobile_toolkit(colors), encoding='utf-8')
(ASSETS / 'hero-mobile.svg').write_text(mobile_hero(THEMES['dark']), encoding='utf-8')
print('Built profile header and toolkit artwork.')
