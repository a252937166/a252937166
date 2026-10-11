#!/usr/bin/env python3
"""Generate the compact GitHub profile card artwork."""
from html import escape
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / 'assets'
FONT = '-apple-system, BlinkMacSystemFont, Segoe UI, Arial, PingFang SC, Microsoft YaHei, sans-serif'
THEMES = {
    'light': dict(bg='#F3F5FC', surface='#FFFFFF', fg='#26334A', muted='#67758D', line='#DEE4EF', accent='#6166B2', icon='#EEF0FA', gold='#8D6118', gold_bg='#FFF3D7', blue='#46658C', blue_bg='#EDF3FB'),
    'dark': dict(bg='#141B2D', surface='#1B2437', fg='#E6ECF7', muted='#A2AEC4', line='#303D56', accent='#AAADED', icon='#28314A', gold='#E6C689', gold_bg='#403525', blue='#ACC7E9', blue_bg='#28364C'),
}
PROJECTS = [
    ('faktura', 'Faktura-Casper', 'Casper 上的智能发票融资', 'Casper Agentic Buildathon 2026', '冠军', 'invoice', 'gold'),
    ('croocred', 'CrooCred', '通过实际下单验证 AI Agent 的服务', 'CROO Agent Hackathon', '第 8 名', 'check', 'blue'),
    ('video', 'claude-video-studio', '用 Claude Code 制作动画和短视频', 'Python / HyperFrames / FFmpeg', '开源工具', 'video', 'accent'),
]


def text(x, y, content, size, color, weight=400, anchor='start'):
    return f'<text x="{x}" y="{y}" font-size="{size}" fill="{color}" font-weight="{weight}" text-anchor="{anchor}">{escape(content)}</text>'


def rect(x, y, width, height, fill, stroke='none', radius=10):
    return f'<rect x="{x}" y="{y}" width="{width}" height="{height}" rx="{radius}" fill="{fill}" stroke="{stroke}"/>'


def svg(body, width, height, title, desc):
    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}" role="img" aria-labelledby="title desc">
<title id="title">{escape(title)}</title><desc id="desc">{escape(desc)}</desc>
<g font-family="{FONT}">{''.join(body)}</g></svg>\n'''


def glyph(kind, x, y, color):
    paths = {
        'code': '<path d="M-6-6-12 0-6 6M6-6 12 0 6 6M3-10-3 10"/>',
        'invoice': '<path d="M-8-12H5L11-6V12H-8ZM5-12V-6H11M-3 0H6M-3 5H6"/>',
        'check': '<path d="M0-12 10-8V1Q10 8 0 13Q-10 8-10 1V-8ZM-5 0-1 4 6-4"/>',
        'video': '<rect x="-12" y="-9" width="24" height="18" rx="4"/><path d="M-3-5 5 0-3 5Z"/>',
    }
    return f'<g transform="translate({x} {y})" fill="none" stroke="{color}" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round">{paths[kind]}</g>'


def header(c, mobile=False):
    w = 380 if mobile else 560
    frame = f'<path d="M14 .5H{w-14}Q{w-.5} .5 {w-.5} 14V91.5H.5V14Q.5 .5 14 .5Z" fill="{c["bg"]}" stroke="{c["line"]}"/>'
    body = [frame, rect(18, 22, 46, 46, c['surface'], c['line'], 12), glyph('code', 41, 45, c['accent'])]
    body += [text(80, 42, 'Mr.ooo', 24 if mobile else 26, c['fg'], 600), text(80, 65, 'AI 智能体开发', 14, c['muted'])]
    body += [text(w-22, 48, 'axiqo.xyz', 12 if mobile else 13, c['accent'], 500, 'end')]
    return svg(body, w, 92, 'Mr.ooo · AI 智能体开发', 'Mr.ooo. AI 智能体开发。个人网站 axiqo.xyz。')


def project(p, c, mobile=False):
    slug, name, desc, event, label, kind, accent = p
    w = 380 if mobile else 560
    h = 111 if mobile else 100
    x = 65 if mobile else 74
    icon_size = 34 if mobile else 40
    icon_x = 16 if mobile else 18
    icon_y = 20
    color = c[accent]
    badge_bg = c.get(accent+'_bg', c['icon'])
    badge_width = 50 if label == '冠军' else 66
    badge_y = 78 if mobile else 17
    badge_x = w-badge_width-18
    if slug == 'video':
        frame = f'<path d="M.5 .5H{w-.5}V{h-14}Q{w-.5} {h-.5} {w-14} {h-.5}H14Q.5 {h-.5} .5 {h-14}Z" fill="{c["surface"]}" stroke="{c["line"]}"/>'
    else:
        frame = rect(.5, .5, w-1, h-1, c['surface'], c['line'], 0)
    body = [frame, rect(icon_x, icon_y, icon_size, icon_size, c['icon'], radius=10), glyph(kind, icon_x+icon_size/2, icon_y+icon_size/2, c['accent'])]
    body += [text(x, 34, name, 18 if mobile else 19, c['fg'], 550), text(x, 59, desc, 13 if mobile else 14, c['muted'])]
    body += [text(x, 94 if mobile else 84, event, 10.5 if mobile else 12, c['muted']), rect(badge_x, badge_y, badge_width, 22, badge_bg, radius=6), text(badge_x+badge_width/2, badge_y+15, label, 11, color, 500, 'middle')]
    return svg(body, w, h, name, f'{name}。{desc}。{event}。{label}。点击查看 GitHub 项目。')


for mode, colors in THEMES.items():
    for mobile in (False, True):
        screen = '-mobile' if mobile else ''
        (ASSETS / f'identity{screen}-{mode}.svg').write_text(header(colors, mobile), encoding='utf-8')
        for item in PROJECTS:
            (ASSETS / f'{item[0]}{screen}-{mode}.svg').write_text(project(item, colors, mobile), encoding='utf-8')
print('Generated compact profile UI artwork.')
