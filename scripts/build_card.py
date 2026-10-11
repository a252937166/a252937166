#!/usr/bin/env python3
"""Render the English GitHub profile from a public, dated data snapshot."""
import base64
import json
import math
import re
from html import escape
from pathlib import Path
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / 'assets'
DATA = json.loads((ROOT / 'data/profile.json').read_text())
FONT = '-apple-system, BlinkMacSystemFont, Segoe UI, Arial, sans-serif'
ET.register_namespace('', 'http://www.w3.org/2000/svg')
THEMES = {
    'light': dict(bg='#EAF2FB', surface='#FFFFFF', fg='#24364B', muted='#60738A', line='#DCE5EF', accent='#3479BE', soft='#F3F7FC', gold='#966722', gold_bg='#FFF3DA', blue_bg='#EDF4FB'),
    'dark': dict(bg='#1B2E45', surface='#152235', fg='#E7EFF8', muted='#A9BDD2', line='#314760', accent='#86B8EB', soft='#1C3049', gold='#E6C17C', gold_bg='#413522', blue_bg='#253E59'),
}
PROJECTS = [
    dict(slug='faktura', name='Faktura-Casper', brand='casper', award='Champion', icon='trophy', color='gold', lines=['AI invoice financing with', 'on-chain risk limits on Casper.'], event='Casper Agentic Buildathon 2026', stack='Rust / Odra · TypeScript · React'),
    dict(slug='croocred', name='CrooCred', brand='croo', award='8th place', icon='medal', color='accent', lines=['Tests paid AI agents and publishes', 'reports with transaction receipts.'], event='CROO Agent Hackathon', stack='TypeScript · CROO CAP · Base'),
    dict(slug='video', name='Claude Video Studio', brand='claude', award='Video tools', icon='video', color='accent', lines=['A Claude Code skill for', 'animations and short videos.'], event='claude-video-studio', stack='Python · HyperFrames · FFmpeg'),
]


def text(x, y, content, size, color, weight=400, anchor='start'):
    return f'<text x="{x}" y="{y}" font-size="{size}" fill="{color}" font-weight="{weight}" text-anchor="{anchor}">{escape(str(content))}</text>'


def rect(x, y, w, h, fill, stroke='none', radius=10):
    return f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="{radius}" fill="{fill}" stroke="{stroke}"/>'


def line(x1, y1, x2, y2, color):
    return f'<path d="M{x1} {y1}H{x2}" stroke="{color}"/>' if y1 == y2 else f'<path d="M{x1} {y1}L{x2} {y2}" stroke="{color}"/>'


def svg(body, w, h, title, desc):
    return f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}" role="img" aria-labelledby="title desc"><title id="title">{escape(title)}</title><desc id="desc">{escape(desc)}</desc><g font-family="{FONT}" style="font-variant-numeric:tabular-nums">{"".join(body)}</g></svg>\n'


def glyph(kind, x, y, color, scale=.7):
    shapes = {
        'trophy': '<path d="M-7-10H7V-3C7 3 4 6 0 6S-7 3-7-3ZM-7-7H-12V-3Q-12 2-6 2M7-7H12V-3Q12 2 6 2M0 6V12M-6 12H6"/>',
        'medal': '<path d="m-6 4-2 9 5-2 3 3 2-8M6 4l2 9-5-2-3 3"/><circle cy="-3" r="8"/><path d="m0-7 1.3 2.5 2.8.4-2 2 .5 2.7L0-.7-2.6.6l.5-2.7-2-2 2.8-.4Z"/>',
        'video': '<rect x="-12" y="-9" width="24" height="18" rx="4"/><path d="M-3-5 5 0-3 5Z"/>',
    }
    return f'<g transform="translate({x} {y}) scale({scale})" fill="none" stroke="{color}" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round">{shapes[kind]}</g>'


def vector(name, x, y, w, h):
    node = ET.fromstring((ASSETS / 'brands' / f'{name}.svg').read_text())
    for key, value in dict(x=x, y=y, width=w, height=h).items():
        node.set(key, str(value))
    return ET.tostring(node, encoding='unicode')


def raster(path, x, y, w, h, mime='image/png'):
    data = base64.b64encode(path.read_bytes()).decode()
    return f'<image x="{x}" y="{y}" width="{w}" height="{h}" href="data:{mime};base64,{data}"/>'


def brand(name, x, y):
    if name == 'casper':
        return rect(x, y, 94, 37, '#FFF7F5', radius=8) + vector('casper', x+20, y+4, 54, 29.4)
    if name == 'croo':
        return rect(x, y, 108, 37, '#171B22', radius=8) + raster(ASSETS/'brands/croo.png', x+9, y+6.8, 90, 23.4)
    return rect(x, y, 96, 37, '#F5EBDD', radius=8) + vector('claude', x+8, y+7, 23, 23) + text(x+39, y+24, 'Claude', 14, '#6B4D3A', 500)


def metric_items():
    m = DATA['metrics']
    return [(m['public_repositories'], 'Public repositories'), (m['received_stars'], 'Repository stars'), (m['followers'], 'Followers'), (m['public_contributions_last_year'], 'Past-year contributions')]


def header(c, mobile=False):
    w, h = (330, 344) if mobile else (830, 192)
    body = [rect(.5, .5, w-1, h-1, c['bg'], c['line'], 12)]
    body += ['<defs><clipPath id="avatar"><rect x="24" y="22" width="56" height="56" rx="12"/></clipPath></defs>']
    if (ASSETS/'avatar.jpg').exists():
        body += [f'<g clip-path="url(#avatar)">{raster(ASSETS/"avatar.jpg",24,22,56,56,"image/jpeg")}</g>']
    else:
        body += [rect(24,22,56,56,c['surface']),text(52,57,'ooo',20,c['accent'],600,'middle')]
    body += [text(96, 45, 'Mr.ooo', 27, c['fg'], 650), text(96, 67, 'AI tools & agent engineering', 13.5, c['muted'])]
    bio = ['I build tools for AI agents, from local workflows', 'to persistent memory. I also experiment with', 'on-chain services and code-driven video.'] if not mobile else ['I build tools for AI agents, from local', 'workflows to persistent memory. I also', 'experiment with on-chain services', 'and code-driven video.']
    for i, sentence in enumerate(bio):
        body += [text(24, 107+i*19, sentence, 15 if mobile else 14, c['fg'])]
    if mobile:
        body += [text(24, 190, 'Python · TypeScript · React · Rust · SQLite · MCP', 11.5, c['muted'])]
        body += [line(24, 209, w-24, 209, c['line'])]
        for i, (value,label) in enumerate(metric_items()):
            x = 24 + (i%2)*152
            y = 242 + (i//2)*62
            body += [text(x,y,f'{value:,}',25,c['fg'],600),text(x,y+19,label,11,c['muted'])]
    else:
        body += [text(24, 172, 'Python · TypeScript · React · Rust · SQLite · MCP', 12, c['muted'])]
        body += [line(512, 24, 512, 168, c['line'])]
        for i, (value,label) in enumerate(metric_items()):
            x = 540 + (i%2)*145
            y = 62 + (i//2)*76
            body += [text(x,y,f'{value:,}',27,c['fg'],600),text(x,y+21,label,11,c['muted'])]
    return svg(body,w,h,'Mr.ooo — AI tools & agent engineering', 'I build tools for AI agents, from local development workflows to persistent memory. I also experiment with on-chain services and code-driven video. '+ '. '.join(f'{v:,} {label}' for v,label in metric_items())+'. Repository stars count owned public non-fork repositories. Contributions cover the rolling year, with private activity excluded.')


def project(p, c):
    w,h = 264,208
    body = [rect(.5,4.5,w-1,199,c['surface'],c['line'],10),brand(p['brand'],18,18)]
    badge_color = c[p['color']]
    badge_bg = c['gold_bg'] if p['color']=='gold' else c['blue_bg']
    body += [rect(142,23,104,27,badge_bg,radius=7),glyph(p['icon'],157,36,badge_color,.56),text(172,40,p['award'],11,badge_color,500)]
    body += [text(18,83,p['name'],18,c['fg'],600)]
    body += [text(18,109,p['lines'][0],13,c['fg']),text(18,128,p['lines'][1],13,c['fg'])]
    body += [text(18,154,p['event'],10.5,c['muted']),line(18,167,246,167,c['line']),text(18,186,p['stack'],11,c['muted'])]
    return svg(body,w,h,p['name'],' '.join(p['lines'])+' '+p['event']+'. '+p['award']+'. '+p['stack']+'. Opens the project repository.')


def top_languages():
    rows = [dict(item) for item in DATA['languages'][:5]]
    other = sum(item['bytes'] for item in DATA['languages'][5:])
    total = DATA['metrics']['language_bytes']
    if other:
        rows.append(dict(name='Other',bytes=other,color='#93A2B4'))
    for row in rows:
        row['share'] = row['bytes']/total if total else 0
    return rows


def activity_plot(c, x, y, w, h):
    rows = DATA['activity']['weekly_last_16']
    values = [r['contributions'] for r in rows]
    max_value = max(values, default=0)
    top = max(20, math.ceil(max_value/20)*20)
    plot_h = h-25
    out = []
    for ratio in (0,.5,1):
        yy = y+plot_h*(1-ratio)
        out += [line(x,yy,x+w,yy,c['line']),text(x-8,yy+4,f'{int(top*ratio)}',10,c['muted'],anchor='end')]
    step = w/max(len(values),1)
    for i, (row,value) in enumerate(zip(rows,values)):
        bar_h = value/top*plot_h
        out += [rect(x+i*step+step*.2,y+plot_h-bar_h,step*.6,max(bar_h,1),c['accent'],radius=2)]
        if row['partial']:
            out += [f'<circle cx="{x+i*step+step*.5}" cy="{y+plot_h+6}" r="2" fill="{c["accent"]}"/>']
        if i in (0,5,10,len(rows)-1):
            label = row['week_start'][5:].replace('-', '/')
            out += [text(x+i*step+step*.5,y+plot_h+22,label,10,c['muted'],anchor='middle')]
    return out


def language_plot(c, x, y):
    rows = top_languages()
    radius = 39
    circumference = 2*math.pi*radius
    body = [f'<circle cx="{x+47}" cy="{y+51}" r="{radius}" fill="none" stroke="{c["line"]}" stroke-width="13"/>']
    offset=0
    for row in rows:
        length=row['share']*circumference
        color=row.get('color') or c['accent']
        body += [f'<circle cx="{x+47}" cy="{y+51}" r="{radius}" fill="none" stroke="{color}" stroke-width="13" stroke-dasharray="{length} {circumference-length}" stroke-dashoffset="{-offset}" transform="rotate(-90 {x+47} {y+51})"/>']
        offset += length
    body += [text(x+47,y+48,str(len(DATA['languages'])),22,c['fg'],600,'middle'),text(x+47,y+65,'languages',9.5,c['muted'],anchor='middle')]
    for i,row in enumerate(rows):
        yy=y+7+i*19
        body += [rect(x+115,yy-8,7,7,row.get('color') or c['accent'],radius=2),text(x+129,yy,row['name'],11.5,c['fg']),text(x+277,yy,f'{row["share"]*100:.1f}%',11.5,c['muted'],anchor='end')]
    return body


def dashboard(c, mobile=False):
    w,h=(330,372) if mobile else (830,195)
    body=[rect(.5,.5,w-1,h-1,c['surface'],c['line'],12)]
    body += [text(24,31,'Contribution activity',15,c['fg'],600),text(24,50,'Last 16 weeks · current week is partial',11,c['muted'])]
    body += activity_plot(c,48,68,257 if mobile else 407,93)
    if mobile:
        body += [line(24,182,w-24,182,c['line']),text(24,213,'Repository languages',15,c['fg'],600)]
        body += language_plot(c,27,235)
        body += [text(24,356,'Share of code bytes in public non-fork repositories',10,c['muted'])]
    else:
        body += [line(490,24,490,173,c['line']),text(514,31,'Repository languages',15,c['fg'],600)]
        body += language_plot(c,514,56)
        body += [text(514,177,'Code bytes · public non-fork repositories',10.5,c['muted'])]
    weekly = '. '.join(f'{row["week_start"]}: {row["contributions"]} contributions' for row in DATA['activity']['weekly_last_16'])
    langs = ', '.join(f'{row["name"]} {row["share"]*100:.1f} percent' for row in top_languages())
    return svg(body,w,h,'GitHub contribution activity and repository languages',weekly+'. Languages are measured by GitHub Linguist code bytes across owned public non-fork repositories, including archived repositories; they do not measure proficiency. '+langs+'. Snapshot '+DATA['fetched_at'])


for mode,c in THEMES.items():
    for mobile in (False,True):
        screen='-mobile' if mobile else ''
        (ASSETS/f'identity{screen}-{mode}.svg').write_text(header(c,mobile))
        (ASSETS/f'stats{screen}-{mode}.svg').write_text(dashboard(c,mobile))
    for p in PROJECTS:
        (ASSETS/f'{p["slug"]}-{mode}.svg').write_text(project(p,c))
        # Cards wrap naturally on phones; both sources use readable 264px artwork.
        (ASSETS/f'{p["slug"]}-mobile-{mode}.svg').write_text(project(p,c))
readme = ROOT / 'README.md'
source = readme.read_text()
source = re.sub(r'<!-- snapshot-date -->.*?<!-- /snapshot-date -->', '<!-- snapshot-date -->Updated '+DATA['fetched_at'][:10]+'<!-- /snapshot-date -->', source)
readme.write_text(source)
print('Generated English horizontal profile artwork.')
