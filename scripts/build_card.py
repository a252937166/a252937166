#!/usr/bin/env python3
"""Build a compact, linked GitHub dashboard with original brand assets."""
import base64
from html import escape
from pathlib import Path
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / 'assets'
FONT = '-apple-system, BlinkMacSystemFont, Segoe UI, Arial, PingFang SC, Microsoft YaHei, sans-serif'
ET.register_namespace('', 'http://www.w3.org/2000/svg')
THEMES = {
    'light': dict(bg='#F6F7FA', surface='#FFFFFF', fg='#263248', muted='#68758A', line='#E1E5ED', accent='#6166AD', icon='#EEF0F6', gold='#90631E', gold_bg='#FFF4DC', blue='#4C698A', blue_bg='#EEF4FB'),
    'dark': dict(bg='#131C2C', surface='#1A2435', fg='#E7EDF6', muted='#A3AFC2', line='#303C50', accent='#B0B4EB', icon='#273247', gold='#E4C181', gold_bg='#3A3022', blue='#AAC8E9', blue_bg='#28384D'),
}
PROJECTS = [
    ('faktura', 'Faktura-Casper', 'Casper 上的智能发票融资', 'Casper Agentic Buildathon 2026', '冠军', 'casper', 'trophy', 'gold'),
    ('croocred', 'CrooCred', '用付费订单验证 AI Agent 服务', 'CROO Agent Hackathon', '第 8 名', 'croo', 'medal', 'blue'),
    ('video', 'claude-video-studio', '用 Claude Code 制作动画和短视频', 'Python / HyperFrames / FFmpeg', '开源工具', 'claude', 'video', 'accent'),
]


def text(x, y, content, size, color, weight=400, anchor='start'):
    return f'<text x="{x}" y="{y}" font-size="{size}" fill="{color}" font-weight="{weight}" text-anchor="{anchor}">{escape(content)}</text>'


def rect(x, y, width, height, fill, stroke='none', radius=10):
    return f'<rect x="{x}" y="{y}" width="{width}" height="{height}" rx="{radius}" fill="{fill}" stroke="{stroke}"/>'


def svg(body, width, height, title, desc):
    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}" role="img" aria-labelledby="title desc">
<title id="title">{escape(title)}</title><desc id="desc">{escape(desc)}</desc>
<g font-family="{FONT}">{''.join(body)}</g></svg>\n'''


def glyph(kind, x, y, color, scale=1):
    paths = {
        'code': '<path d="M-6-6-12 0-6 6M6-6 12 0 6 6M3-10-3 10"/>',
        'trophy': '<path d="M-7-10H7V-3C7 3 4 6 0 6S-7 3-7-3ZM-7-7H-12V-3Q-12 2-6 2M7-7H12V-3Q12 2 6 2M0 6V12M-6 12H6"/><path d="m0-6 1.3 2.4 2.7.4-2 1.9.5 2.6L0 0l-2.5 1.3.5-2.6-2-1.9 2.7-.4Z" fill="{color}" stroke="none"/>',
        'medal': '<path d="m-6 4-2 9 5-2 3 3 2-8M6 4l2 9-5-2-3 3"/><circle cy="-3" r="8"/><path d="m0-7 1.3 2.5 2.8.4-2 2 .5 2.7L0-.7-2.6.6l.5-2.7-2-2 2.8-.4Z"/>',
        'video': '<rect x="-12" y="-9" width="24" height="18" rx="4"/><path d="M-3-5 5 0-3 5Z"/>',
    }
    shape = paths[kind].replace('{color}', color)
    return f'<g transform="translate({x} {y}) scale({scale})" fill="none" stroke="{color}" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round">{shape}</g>'


def original_vector(name, x, y, width, height):
    # Embed original vector geometry and colors; only its placement is changed.
    node = ET.fromstring((ASSETS / 'brands' / f'{name}.svg').read_text())
    node.set('x', str(x))
    node.set('y', str(y))
    node.set('width', str(width))
    node.set('height', str(height))
    return ET.tostring(node, encoding='unicode')


def brand(name, x, y, size, c):
    if name == 'casper':
        return rect(x, y, size, size, '#FFF7F5', radius=12) + original_vector('casper', x+9, y+(size-(size-18)*86/158)/2, size-18, (size-18)*86/158)
    if name == 'croo':
        data = base64.b64encode((ASSETS / 'brands/croo.png').read_bytes()).decode()
        width = size-14
        height = width*612/2354
        return rect(x, y, size, size, '#171B22', radius=12) + f'<image x="{x+7}" y="{y+(size-height)/2}" width="{width}" height="{height}" href="data:image/png;base64,{data}"/>'
    return rect(x, y, size, size, '#F5EBDD', radius=12) + original_vector('claude', x+size*.23, y+size*.23, size*.54, size*.54)


def header(c, mobile=False):
    w, h = (380 if mobile else 560), 168
    frame = f'<path d="M16 .5H{w-16}Q{w-.5} .5 {w-.5} 16V{h-.5}H.5V16Q.5 .5 16 .5Z" fill="{c["bg"]}" stroke="{c["line"]}"/>'
    body = [frame, rect(20, 22, 44, 44, c['surface'], c['line'], 12), glyph('code', 42, 44, c['accent'])]
    body += [text(80, 42, 'Mr.ooo', 24 if mobile else 26, c['fg'], 600), text(80, 65, 'AI 智能体开发', 14, c['muted']), text(w-22, 48, 'axiqo.xyz ↗', 12 if mobile else 13, c['accent'], 500, 'end')]
    body += [rect(20, 89, w-40, 59, c['surface'], c['line'], 10)]
    col = (w-40)/3
    for i, (number, label, kind, accent) in enumerate([(1, '冠军项目', 'trophy', 'gold'), (2, '获奖项目', 'medal', 'blue'), (3, '精选项目', 'code', 'accent')]):
        left = 20+i*col
        if i:
            body += [f'<path d="M{left} 101V136" stroke="{c["line"]}"/>']
        icon_x = left+(22 if mobile else 30)
        tx = left+(42 if mobile else 56)
        body += [glyph(kind, icon_x, 117, c[accent], .65 if mobile else .8), text(tx, 117, str(number), 22, c['fg'], 600), text(tx, 135, label, 10.5 if mobile else 11, c['muted'])]
    return svg(body, w, h, 'Mr.ooo · AI 智能体开发', '个人项目看板。1 个冠军项目，2 个获奖项目，3 个精选项目。个人网站 axiqo.xyz。')


def project(p, c, mobile=False):
    slug, name, desc, event, label, platform, kind, accent = p
    w, h = (380, 134) if mobile else (560, 114)
    x = 86 if mobile else 108
    color = c[accent]
    badge_bg = c.get(accent+'_bg', c['icon'])
    if slug == 'video':
        frame = f'<path d="M.5 .5H{w-.5}V{h-16}Q{w-.5} {h-.5} {w-16} {h-.5}H16Q.5 {h-.5} .5 {h-16}Z" fill="{c["surface"]}" stroke="{c["line"]}"/>'
    else:
        frame = rect(.5, .5, w-1, h-1, c['surface'], c['line'], 0)
    body = [frame, brand(platform, 18 if mobile else 20, 22, 54 if mobile else 70, c)]
    body += [text(x, 34, name, 18 if mobile else 19, c['fg'], 600), text(x, 58, desc, 13 if mobile else 14, c['muted']), text(x, 82, event, 10.5 if mobile else 11.5, c['muted'])]
    badge_x, badge_y = w-112, 96 if mobile else 20
    body += [rect(badge_x, badge_y, 92, 27, badge_bg, radius=7), glyph(kind, badge_x+17, badge_y+13, color, .57), text(badge_x+34, badge_y+18, label, 11.5, color, 500)]
    body += [text(x if mobile else w-20, 114 if mobile else 94, '查看项目 ↗', 11, c['accent'], 400, 'start' if mobile else 'end')]
    return svg(body, w, h, name, f'{name}。{desc}。{event}。{label}。点击查看 GitHub 项目。')


for mode, colors in THEMES.items():
    for mobile in (False, True):
        screen = '-mobile' if mobile else ''
        (ASSETS / f'identity{screen}-{mode}.svg').write_text(header(colors, mobile), encoding='utf-8')
        for item in PROJECTS:
            (ASSETS / f'{item[0]}{screen}-{mode}.svg').write_text(project(item, colors, mobile), encoding='utf-8')
print('Generated dashboard: 1 champion, 2 awarded projects, 3 selected projects.')
