#!/usr/bin/env python3
"""Build the profile's self-hosted SVG artwork. No third-party dependencies."""
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
PROJECTS = [
    ('localpilot', 'LocalPilot', 'AI 开发工具', '把 ChatGPT 对话接上本机代码、技能与浏览器。', '让工具执行和测试结果回到同一段对话。', 'Python / MCP / Playwright', 'tools', 'blue'),
    ('engram', 'ENGRAM', '智能体记忆', '为 Qwen 智能体提供持久、可检索的长期记忆。', '混合检索、信念修订与记忆整合。', 'Python / SQLite / Qwen', 'memory', 'violet'),
    ('mirofishcodex', 'MiroFishCodex', '多角色推演', '将 MiroFish 适配为 Codex / Claude 原生技能。', '结合本地时序记忆，探索多角色分支情境。', 'Python / BGE-M3 / SQLite', 'branch', 'mint'),
    ('claude-video-studio', 'claude-video-studio', 'AI 创意工具', '让 Claude 用代码制作像素动画与短视频。', '节拍同步、配音、剪辑和成片质量检查。', 'HyperFrames / GSAP / FFmpeg', 'video', 'blue'),
    ('arcpreflight', 'ArcPreflight', 'Agent 支付', '面向智能体 USDC 支付的执行工作台。', '审批绑定、签前校验、中断恢复与可验证凭证。', 'TypeScript / React / viem', 'proof', 'violet'),
    ('alphapilot', 'AlphaPilot-AI', 'AI 金融研究', '结合量化因子、回测与 LLM 解读的研究平台。', '专注研究与决策辅助，当前禁用实盘下单。', 'Python / FastAPI / Vue 3', 'chart', 'mint'),
]


def text(x, y, value, size, color, weight=400, anchor='start'):
    return f'<text x="{x}" y="{y}" font-size="{size}" fill="{color}" font-weight="{weight}" text-anchor="{anchor}">{escape(value)}</text>'


def svg(body, width, height, title, description):
    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}" role="img" aria-labelledby="title desc">
<title id="title">{escape(title)}</title><desc id="desc">{escape(description)}</desc>
<g font-family="{FONT}">{body}</g></svg>\n'''


def rect(x, y, w, h, fill, stroke='none', r=16):
    return f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="{r}" fill="{fill}" stroke="{stroke}"/>'


def icon(kind, x, y, color):
    shapes = {
        'tools': '<path d="M-15-10-26 0-15 10M15-10 26 0 15 10M6-20-6 20"/>',
        'memory': '<rect x="-20" y="-20" width="40" height="40" rx="10"/><path d="M-10-6H10M-10 6H5M-26-8H-20M-26 8H-20M20-8H26M20 8H26"/>',
        'branch': '<path d="M-16-20V20M-16 0H6Q18 0 18-12V-20"/><circle cx="-16" cy="-20" r="5"/><circle cx="-16" cy="20" r="5"/><circle cx="18" cy="-20" r="5"/>',
        'video': '<rect x="-25" y="-18" width="50" height="36" rx="8"/><path d="M-5-9 10 0-5 9Z"/>',
        'proof': '<path d="M0-25 21-16V2Q21 17 0 26Q-21 17-21 2V-16ZM-10 0-2 8 12-8"/>',
        'chart': '<path d="M-25-20V20H25M-17 10-6-5 5 2 22-18"/><circle cx="22" cy="-18" r="3"/>',
    }
    return f'<g transform="translate({x} {y})" fill="none" stroke="{color}" stroke-width="2.6" stroke-linecap="round" stroke-linejoin="round">{shapes[kind]}</g>'


def hero(c):
    parts = [rect(1, 1, 1198, 358, c['bg'], c['line'], 24)]
    # The graph is the visual identity: one agent connected to tools, memory and proof.
    parts += [f'<circle cx="944" cy="180" r="146" fill="none" stroke="{c["line"]}" stroke-dasharray="3 10"/>',
              f'<circle cx="944" cy="180" r="92" fill="none" stroke="{c["line"]}"/>']
    for x, y, label, accent, kind in [(837, 72, 'Tools', 'blue', 'tools'), (1072, 131, 'Memory', 'violet', 'memory'), (951, 293, 'Proof', 'mint', 'proof')]:
        parts.append(f'<path d="M944 180L{x} {y}" fill="none" stroke="{c[accent]}" stroke-width="2" opacity=".5"/>')
        parts += [rect(x-49, y-38, 98, 76, c['panel'], c['line'], 18), icon(kind, x, y-7, c[accent]), text(x, y+25, label, 15, c['muted'], anchor='middle')]
    parts += [f'<circle cx="944" cy="180" r="57" fill="{c["panel"]}" stroke="{c["violet"]}" stroke-width="2"/>',
              f'<circle cx="944" cy="180" r="48" fill="none" stroke="{c["violet"]}" opacity=".18"/>',
              text(944, 187, 'Agent', 25, c['fg'], 650, 'middle')]
    parts += [text(48, 61, 'Mr.ooo', 26, c['fg'], 600), text(48, 146, 'Build useful AI.', 64, c['fg'], 750),
              text(50, 195, '让 AI 能记住、能执行、能交付。', 25, c['muted']),
              text(50, 237, 'Applied AI & agent engineering', 22, c['violet'], 550)]
    parts.append(f'<path d="M50 269H700" stroke="{c["line"]}"/>')
    parts += [text(50, 311, 'Agents', 18, c['blue'], 550), text(161, 311, '/', 18, c['muted']),
              text(187, 311, 'MCP & memory', 18, c['violet'], 550), text(353, 311, '/', 18, c['muted']),
              text(380, 311, 'AI × Web3', 18, c['mint'], 550), text(693, 311, '@a252937166', 16, c['muted'], anchor='end')]
    return svg(''.join(parts), 1200, 360, 'Mr.ooo — Build useful AI.', 'Applied AI and agent engineering. Agents connected to tools, memory and verifiable outcomes. 让 AI 能记住、能执行、能交付。')


def project_card(project, c):
    slug, name, category, desc1, desc2, stack, kind, accent = project
    a = c[accent]
    parts = [rect(1, 1, 588, 218, c['panel'], c['line'], 20), rect(25, 26, 5, 20, a, r=2),
             text(41, 43, category, 17, c['muted']), text(25, 89, name, 29, c['fg'], 680),
             text(25, 128, desc1, 19, c['muted']), text(25, 158, desc2, 19, c['muted']),
             text(25, 197, stack, 16, a, 550), icon(kind, 541, 57, a)]
    return svg(''.join(parts), 590, 220, name, f'{category}。{desc1}{desc2} {stack}')


def toolkit(c):
    parts = [rect(1, 1, 1198, 156, c['bg'], c['line'], 20)]
    groups = [('Build', 'Python · TypeScript · Java', 'blue'), ('Connect', 'MCP · SQLite · FastAPI', 'violet'), ('Create', 'React · Vue · HyperFrames', 'mint')]
    for i, (label, stack, accent) in enumerate(groups):
        x = 35+i*395
        parts += [text(x, 52, label, 21, c[accent], 600), text(x, 95, stack, 20, c['fg'])]
        if i < 2:
            parts.append(f'<path d="M{x+361} 31V118" stroke="{c["line"]}"/>')
    return svg(''.join(parts), 1200, 158, 'My toolkit', 'Python, TypeScript, Java, MCP, SQLite, FastAPI, React, Vue and HyperFrames.')


MOBILE_COPY = {
    'localpilot': ('LocalPilot', 'ChatGPT 连接本机工具', '代码 / 浏览器 / 测试', 'Python / MCP'),
    'engram': ('ENGRAM', '给智能体长期记忆', '检索 / 修订 / 整合', 'Qwen / SQLite'),
    'mirofishcodex': ('MiroFishCodex', 'Codex / Claude 技能', 'MiroFish 适配与推演', 'Python / BGE-M3'),
    'claude-video-studio': ('Claude Video', '用代码制作短视频', '动画 / 节拍 / 配音', 'GSAP / FFmpeg'),
    'arcpreflight': ('ArcPreflight', '智能体 USDC 支付', '校验 / 恢复 / 凭证', 'TypeScript / viem'),
    'alphapilot': ('AlphaPilot-AI', 'AI 股票研究与回测', '研究模式 / 禁用实盘', 'FastAPI / Vue'),
}


def mobile_project(project, c):
    slug, name, category, desc1, desc2, stack, kind, accent = project
    title, line1, line2, tags = MOBILE_COPY[slug]
    a = c[accent]
    parts = [rect(1, 1, 588, 358, c['panel'], c['line'], 24),
             rect(27, 31, 6, 29, a, r=3), text(47, 56, category, 31, c['muted']),
             text(27, 130, title, 52, c['fg'], 680), text(27, 197, line1, 38, c['muted']),
             text(27, 251, line2, 38, c['muted']), text(27, 316, tags, 33, a, 550),
             icon(kind, 540, 49, a)]
    return svg(''.join(parts), 590, 360, name, f'{category}。{desc1}{desc2}')


def mobile_hero(c):
    parts = [rect(1, 1, 598, 398, c['bg'], c['line'], 24), text(31, 55, 'Mr.ooo', 27, c['fg'], 600),
             text(31, 133, 'Build useful AI.', 60, c['fg'], 750), text(31, 190, '让 AI 能记住、能执行、能交付。', 29, c['muted']),
             text(31, 236, 'Applied AI & agent engineering', 25, c['violet'], 550)]
    parts.append(f'<path d="M31 263H566" stroke="{c["line"]}"/>')
    for x, label, accent in [(90, 'Tools', 'blue'), (292, 'Agent', 'violet'), (496, 'Memory', 'mint')]:
        if x != 496:
            parts.append(f'<path d="M{x+53} 320H{x+146}" stroke="{c[accent]}" stroke-width="2"/>')
        parts += [rect(x-53, 288, 106, 64, c['panel'], c['line'], 18), text(x, 329, label, 23, c[accent], 600, 'middle')]
    return svg(''.join(parts), 600, 400, 'Mr.ooo — Build useful AI.', '让 AI 能记住、能执行、能交付。Applied AI and agent engineering.')


def mobile_toolkit(c):
    parts = [rect(1, 1, 598, 328, c['bg'], c['line'], 24)]
    groups = [('Build', 'Python · TypeScript · Java', 'blue'), ('Connect', 'MCP · SQLite · FastAPI', 'violet'), ('Create', 'React · Vue · HyperFrames', 'mint')]
    for i, (label, stack, accent) in enumerate(groups):
        y = 49+i*100
        parts += [text(28, y, label, 25, c[accent], 650), text(28, y+40, stack, 28, c['fg'])]
    return svg(''.join(parts), 600, 330, 'My toolkit', 'Python, TypeScript, Java, MCP, SQLite, FastAPI, React, Vue and HyperFrames.')


for theme, colors in THEMES.items():
    (ASSETS / f'hero-{theme}.svg').write_text(hero(colors), encoding='utf-8')
    (ASSETS / f'toolkit-{theme}.svg').write_text(toolkit(colors), encoding='utf-8')
    (ASSETS / f'toolkit-mobile-{theme}.svg').write_text(mobile_toolkit(colors), encoding='utf-8')
    for project in PROJECTS:
        (ASSETS / f'{project[0]}-{theme}.svg').write_text(project_card(project, colors), encoding='utf-8')
        (ASSETS / f'{project[0]}-mobile-{theme}.svg').write_text(mobile_project(project, colors), encoding='utf-8')
(ASSETS / 'hero-mobile.svg').write_text(mobile_hero(THEMES['dark']), encoding='utf-8')
print('Built desktop and mobile profile artwork assets.')
