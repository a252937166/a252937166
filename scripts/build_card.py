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
UI = ASSETS / 'ui-v3'
UI.mkdir(exist_ok=True)
DATA = json.loads((ROOT / 'data/profile.json').read_text())
FONT = '-apple-system, BlinkMacSystemFont, Segoe UI, Arial, sans-serif'
ET.register_namespace('', 'http://www.w3.org/2000/svg')
THEMES = {
    'light': dict(bg='#FFFFFF', surface='#FFFFFF', fg='#1F2328', muted='#656D76', line='#D1D9E0', accent='#0969DA', soft='#F6F8FA', gold='#8C651D', gold_bg='#FFF4D8', blue_bg='#DDF4FF'),
    'dark': dict(bg='#0D1117', surface='#0D1117', fg='#E6EDF3', muted='#8B949E', line='#30363D', accent='#58A6FF', soft='#161B22', gold='#E3B95B', gold_bg='#342C1B', blue_bg='#152A3F'),
}
PROJECTS = [
    dict(slug='faktura', name='Faktura-Casper', brand='casper', award='Champion', icon='trophy', color='gold', lines=['AI invoice financing on Casper with', 'contract-enforced risk limits.'], event='Casper Agentic Buildathon 2026', stack='Rust / Odra · TypeScript · React'),
    dict(slug='croocred', name='CrooCred', brand='croo', award='8th place', icon='medal', color='accent', lines=['Tests paid AI agents and publishes reports', 'with transaction receipts.'], event='CROO Agent Hackathon', stack='TypeScript · CROO CAP · Base'),
    dict(slug='video', name='claude-video-studio', brand='claude', award='Open source', icon='video', color='accent', lines=['A Claude Code skill for animations and', 'short videos, rendered with HyperFrames.'], event='Claude Code skill', stack='Python · HyperFrames · FFmpeg'),
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
        return rect(x, y, 72, 32, '#FFF7F5', radius=6) + vector('casper', x+14, y+4, 44, 24)
    if name == 'croo':
        return rect(x, y, 92, 32, '#171B22', radius=6) + raster(ASSETS/'brands/croo.png', x+7, y+6, 78, 20)
    return rect(x, y, 84, 32, '#F5EBDD', radius=6) + vector('claude', x+7, y+6, 20, 20) + text(x+34, y+21, 'Claude', 13, '#6B4D3A', 500)


def metric_items():
    m = DATA['metrics']
    return [(m['public_repositories'], 'Public repositories'), (m['received_stars'], 'Repository stars'), (m['followers'], 'Followers'), (m['public_contributions_last_year'], 'Past-year contributions')]


def project(p, c):
    w,h = 410,164
    brand_width = {'casper':72,'croo':92,'claude':84}[p['brand']]
    body = [rect(.5,4.5,w-1,155,c['surface'],c['line'],6),brand(p['brand'],w-brand_width-18,16)]
    body += [f'<g transform="translate(18 21)" fill="none" stroke="{c["muted"]}" stroke-width="1.2"><rect width="12" height="14" rx="2"/><path d="M3 0V14M6 4H9M6 7H9"/></g>']
    body += [text(39,32,p['name'],16,c['accent'],600)]
    body += [text(18,63,p['lines'][0],14,c['muted']),text(18,83,p['lines'][1],14,c['muted'])]
    badge_color = c[p['color']]
    badge_bg = c['gold_bg'] if p['color']=='gold' else c['blue_bg']
    body += [rect(18,101,108,22,badge_bg,radius=5),glyph(p['icon'],32,112,badge_color,.5),text(47,116,p['award'],11.5,badge_color,500)]
    body += [text(138,116,p['event'],11.5,c['muted']),text(18,147,p['stack'],12.5,c['muted'])]
    return svg(body,w,h,p['name'],' '.join(p['lines'])+' '+p['event']+'. '+p['award']+'. '+p['stack']+'. Opens the project repository.')


def overview(c):
    w,h=410,164
    body=[rect(.5,4.5,w-1,155,c['surface'],c['line'],6),text(18,32,'GitHub overview',16,c['fg'],600)]
    for i,(value,label) in enumerate(metric_items()):
        x=18+(i%2)*196
        y=69+(i//2)*58
        body += [text(x,y,f'{value:,}',20,c['fg'],600),text(x,y+18,label,12,c['muted'])]
    return svg(body,w,h,'GitHub overview','. '.join(f'{v:,} {label}' for v,label in metric_items())+'. Repository stars count owned public non-fork repositories. Contributions cover the rolling year, with private activity excluded. Snapshot '+DATA['fetched_at'])


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
        out += [line(x,yy,x+w,yy,c['line']),text(x-8,yy+4,f'{int(top*ratio)}',11,c['muted'],anchor='end')]
    step = w/max(len(values),1)
    for i, (row,value) in enumerate(zip(rows,values)):
        bar_h = value/top*plot_h
        out += [rect(x+i*step+step*.2,y+plot_h-bar_h,step*.6,max(bar_h,1),c['accent'],radius=2)]
        if row['partial']:
            out += [f'<circle cx="{x+i*step+step*.5}" cy="{y+plot_h+6}" r="2" fill="{c["accent"]}"/>']
        if i in (0,5,10,len(rows)-1):
            label = row['week_start'][5:].replace('-', '/')
            out += [text(x+i*step+step*.5,y+plot_h+22,label,11,c['muted'],anchor='middle')]
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
    body += [text(x+47,y+48,str(len(DATA['languages'])),20,c['fg'],600,'middle'),text(x+47,y+65,'languages',11,c['muted'],anchor='middle')]
    for i,row in enumerate(rows):
        yy=y+7+i*19
        body += [rect(x+115,yy-8,7,7,row.get('color') or c['accent'],radius=2),text(x+129,yy,row['name'],12.5,c['fg']),text(x+343,yy,f'{row["share"]*100:.1f}%',12.5,c['muted'],anchor='end')]
    return body


def activity_card(c):
    w,h=410,206
    body=[rect(.5,4.5,w-1,197,c['surface'],c['line'],6),text(18,32,'Contribution activity',16,c['fg'],600),text(18,54,'Last 16 weeks · current week is partial',12,c['muted'])]
    body += activity_plot(c,46,74,340,106)
    weekly='. '.join(f'{row["week_start"]}: {row["contributions"]} contributions' for row in DATA['activity']['weekly_last_16'])
    return svg(body,w,h,'Public GitHub contribution activity',weekly+'. Snapshot '+DATA['fetched_at'])


def language_card(c):
    w,h=410,206
    body=[rect(.5,4.5,w-1,197,c['surface'],c['line'],6),text(18,32,'Repository languages',16,c['fg'],600)]
    body += language_plot(c,18,60)
    body += [text(18,189,'Code bytes in public non-fork repositories',11.5,c['muted'])]
    langs=', '.join(f'{row["name"]} {row["share"]*100:.1f} percent' for row in top_languages())
    return svg(body,w,h,'Repository language composition','GitHub Linguist code bytes across owned public non-fork repositories, including archived projects. '+langs+'. Snapshot '+DATA['fetched_at'])


for mode,c in THEMES.items():
    (UI/f'overview-{mode}.svg').write_text(overview(c))
    (UI/f'activity-{mode}.svg').write_text(activity_card(c))
    (UI/f'languages-{mode}.svg').write_text(language_card(c))
    for p in PROJECTS:
        (UI/f'{p["slug"]}-{mode}.svg').write_text(project(p,c))
readme=ROOT/'README.md'
source=readme.read_text()
source=re.sub(r'<!-- snapshot-date -->.*?<!-- /snapshot-date -->','<!-- snapshot-date -->Updated '+DATA['fetched_at'][:10]+'<!-- /snapshot-date -->',source)
readme.write_text(source)
print('Generated GitHub-sized English dashboard assets.')
