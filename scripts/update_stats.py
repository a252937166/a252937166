#!/usr/bin/env python3
"""Refresh a GitHub profile's public, self-hosted SVG statistics.

Uses the Python standard library. In Actions, GH_TOKEN authenticates HTTPS
requests; locally, an authenticated `gh` CLI is the fallback. No repository
names, private repository details, or credentials are written to the snapshot.
Fetching or validation failures leave the existing cards untouched.
"""

from __future__ import annotations

import argparse
import datetime as dt
import html
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import tempfile
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen
import xml.etree.ElementTree as ET


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_USERNAME = "a252937166"
API_ROOT = "https://api.github.com/"
FONT = "-apple-system,BlinkMacSystemFont,Segoe UI,Arial,sans-serif"
QUERY = """query ProfileCalendar($login: String!) {
  user(login: $login) {
    contributionsCollection {
      contributionCalendar {
        totalContributions
        weeks {
          firstDay
          contributionDays { date contributionCount }
        }
      }
    }
  }
}"""

THEMES = {
    "dark": {
        "bg": "#111629", "panel": "#192039", "text": "#F3F5FF",
        "muted": "#A8B4D1", "border": "#2D3654",
        "accents": ["#AFA4FF", "#75D1F5", "#82D5B6", "#E8BF83", "#DD9FB6", "#8995B9"],
    },
    "light": {
        "bg": "#F3F5FF", "panel": "#FFFFFF", "text": "#222943",
        "muted": "#5E6886", "border": "#DDE3F3",
        "accents": ["#7162C9", "#247EAA", "#287E67", "#956021", "#A45272", "#6D789C"],
    },
}


class StatsError(Exception):
    """A safe, public-facing error that never includes an API response body."""


def api(endpoint: str, payload: dict | None = None) -> object:
    token = os.environ.get("GH_TOKEN")
    body = None if payload is None else json.dumps(payload).encode("utf-8")
    method = "GET" if payload is None else "POST"
    if token:
        request = Request(
            API_ROOT + endpoint,
            data=body,
            method=method,
            headers={
                "Authorization": "Bearer " + token,
                "Accept": "application/vnd.github+json",
                "Content-Type": "application/json",
                "X-GitHub-Api-Version": "2022-11-28",
                "User-Agent": "public-profile-stats",
            },
        )
        try:
            with urlopen(request, timeout=30) as response:
                result = response.read()
        except HTTPError as error:
            raise StatsError(f"GitHub {method} request failed (HTTP {error.code}).") from None
        except (URLError, TimeoutError, OSError):
            raise StatsError("GitHub request failed or timed out.") from None
    else:
        command = ["gh", "api", endpoint, "--method", method]
        if body is not None:
            command.extend(["--input", "-"])
        try:
            process = subprocess.run(
                command, input=body, capture_output=True, timeout=45, check=False,
            )
        except FileNotFoundError:
            raise StatsError("Set GH_TOKEN or sign in with the GitHub CLI (`gh auth login`).") from None
        except (subprocess.TimeoutExpired, OSError):
            raise StatsError("GitHub CLI request failed or timed out.") from None
        if process.returncode:
            raise StatsError(f"GitHub CLI request failed (exit {process.returncode}).")
        result = process.stdout
    try:
        return json.loads(result)
    except (UnicodeDecodeError, json.JSONDecodeError):
        raise StatsError("GitHub returned an invalid JSON response.") from None


def count(value: object, label: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        raise StatsError(f"GitHub returned an invalid {label} count.")
    return value


def date(value: object) -> dt.date:
    if not isinstance(value, str):
        raise StatsError("GitHub returned an invalid calendar date.")
    try:
        return dt.date.fromisoformat(value)
    except ValueError:
        raise StatsError("GitHub returned an invalid calendar date.") from None


def fetch_snapshot(username: str, now: dt.datetime) -> dict:
    profile = api(f"users/{username}")
    if not isinstance(profile, dict) or str(profile.get("login", "")).lower() != username.lower():
        raise StatsError("GitHub returned an unexpected public profile.")
    followers = count(profile.get("followers"), "follower")
    public_repos = []
    seen_ids = set()
    page = 1
    while True:
        repos = api(f"users/{username}/repos?type=owner&sort=full_name&direction=asc&per_page=100&page={page}")
        if not isinstance(repos, list):
            raise StatsError("GitHub returned an invalid public repository list.")
        for repo in repos:
            if not isinstance(repo, dict):
                raise StatsError("GitHub returned an invalid repository record.")
            # The public users/{login}/repos endpoint is used exclusively. Keep
            # this explicit filter as a second boundary even when authenticated.
            if repo.get("private") is not False:
                continue
            owner = repo.get("owner", {})
            if not isinstance(owner, dict) or str(owner.get("login", "")).lower() != username.lower():
                continue
            repo_id = repo.get("id")
            if not isinstance(repo_id, int):
                raise StatsError("GitHub returned an invalid repository identifier.")
            if repo_id not in seen_ids:
                seen_ids.add(repo_id)
                public_repos.append(repo)
        if len(repos) < 100:
            break
        page += 1
        if page > 100:
            raise StatsError("Public repository pagination exceeded its safety limit.")

    non_forks = [
        repo for repo in public_repos
        if repo.get("fork") is False and str(repo.get("name", "")).lower() != username.lower()
    ]
    languages: dict[str, int] = {}
    for repo in non_forks:
        language = repo.get("language")
        if language is None:
            language = "Unspecified"
        if not isinstance(language, str) or not language.strip() or len(language) > 80:
            raise StatsError("GitHub returned an invalid primary language.")
        languages[language] = languages.get(language, 0) + 1

    response = api("graphql", {"query": QUERY, "variables": {"login": username}})
    if not isinstance(response, dict) or response.get("errors"):
        raise StatsError("GitHub contribution calendar query failed.")
    try:
        calendar = response["data"]["user"]["contributionsCollection"]["contributionCalendar"]
        total = count(calendar["totalContributions"], "contribution")
        weeks = calendar["weeks"]
    except (KeyError, TypeError):
        raise StatsError("GitHub returned an incomplete contribution calendar.") from None
    if not isinstance(weeks, list) or len(weeks) < 12:
        raise StatsError("GitHub returned too few contribution calendar weeks.")

    daily: dict[dt.date, int] = {}
    for week in weeks:
        if not isinstance(week, dict) or not isinstance(week.get("contributionDays"), list):
            raise StatsError("GitHub returned an invalid contribution calendar week.")
        for day in week["contributionDays"]:
            if not isinstance(day, dict):
                raise StatsError("GitHub returned an invalid contribution calendar day.")
            daily[date(day.get("date"))] = count(day.get("contributionCount"), "daily contribution")

    today = now.date()
    sunday = today - dt.timedelta(days=(today.weekday() + 1) % 7)
    recent = []
    for offset in range(11, -1, -1):
        start = sunday - dt.timedelta(weeks=offset)
        end = min(start + dt.timedelta(days=6), today)
        dates = [start + dt.timedelta(days=day) for day in range((end - start).days + 1)]
        if any(day not in daily for day in dates):
            raise StatsError("GitHub returned an incomplete recent contribution calendar.")
        recent.append({
            "week_start": start.isoformat(),
            "contributions": sum(daily[day] for day in dates),
            "partial": offset == 0,
        })

    return {
        "schema_version": 1,
        "account": username,
        "snapshot_date": today.isoformat(),
        "fetched_at_utc": now.isoformat(timespec="seconds").replace("+00:00", "Z"),
        "metrics": {
            "public_repositories": len(public_repos),
            "non_fork_repositories": len(non_forks),
            "followers": followers,
            "contributions_last_year": total,
        },
        "languages": [
            {"language": language, "repositories": number}
            for language, number in sorted(languages.items(), key=lambda item: (-item[1], item[0].lower()))
        ],
        "weekly_contributions": recent,
    }


def esc(value: object) -> str:
    return html.escape(str(value), quote=True)


def language_groups(snapshot: dict) -> list[tuple[str, int]]:
    named = [item for item in snapshot["languages"] if item["language"] != "Unspecified"]
    groups = [(item["language"], item["repositories"]) for item in named[:4]]
    if len(named) > 4:
        groups.append(("Other languages", sum(item["repositories"] for item in named[4:])))
    unspecified = sum(item["repositories"] for item in snapshot["languages"] if item["language"] == "Unspecified")
    if unspecified:
        groups.append(("Unspecified", unspecified))
    return groups


def render_svg(snapshot: dict, mode: str) -> str:
    theme = THEMES[mode]
    svg = [
        '<svg xmlns="http://www.w3.org/2000/svg" width="1200" height="380" viewBox="0 0 1200 380" role="img" aria-labelledby="title description">',
        f'<title id="title">Public GitHub activity for {esc(snapshot["account"])}</title>',
        '<desc id="description">Public repository and follower counts, last-year GitHub contributions, the most recent twelve weeks including the current partial week, and primary language counts for non-fork repositories excluding the profile repository.</desc>',
        f'<rect width="1200" height="380" rx="22" fill="{theme["bg"]}"/>',
        f'<g font-family="{FONT}">',
    ]

    def text(x: float, y: float, content: object, size: int = 16, color: str | None = None, weight: str = "400", anchor: str = "start") -> None:
        svg.append(f'<text x="{x:g}" y="{y:g}" font-size="{size}" fill="{color or theme["text"]}" font-weight="{weight}" text-anchor="{anchor}">{esc(content)}</text>')

    def panel(x: int, y: int, width: int, height: int) -> None:
        svg.append(f'<rect x="{x}" y="{y}" width="{width}" height="{height}" rx="22" fill="{theme["panel"]}" stroke="{theme["border"]}"/>')

    text(32, 44, "GitHub snapshot", 22, weight="650")
    text(230, 43, "GitHub / " + snapshot["account"], 16, theme["muted"])
    text(1168, 43, "Updated " + snapshot["snapshot_date"] + " UTC", 15, theme["muted"], anchor="end")

    metrics = snapshot["metrics"]
    metric_items = [
        ("Public repos", metrics["public_repositories"]),
        ("Non-fork repos", metrics["non_fork_repositories"]),
        ("Followers", metrics["followers"]),
        ("Last-year contributions", metrics["contributions_last_year"]),
    ]
    for index, (label, number) in enumerate(metric_items):
        x = 32 + index * 288
        panel(x, 76, 272, 100)
        svg.append(f'<rect x="{x + 24}" y="98" width="4" height="32" rx="2" fill="{theme["accents"][index % 3]}"/>')
        text(x + 42, 129, f"{number:,}", 40, weight="650")
        text(x + 24, 154, label, 17, theme["muted"])

    panel(32, 192, 704, 156)
    text(56, 226, "Weekly contributions", 22, weight="600")
    text(712, 226, "12 weeks · current week partial", 14, theme["muted"], anchor="end")
    recent = snapshot["weekly_contributions"]
    maximum = max(1, *(week["contributions"] for week in recent))
    # A linear scale preserves the relationship between every weekly count.
    for index, week in enumerate(recent):
        center = 82 + index * 55
        height = max(2, 58 * week["contributions"] / maximum)
        fill = theme["accents"][0] if index < 11 else theme["accents"][1]
        opacity = "0.74" if index < 11 else "1"
        svg.append(f'<rect x="{center - 16}" y="{311 - height:.2f}" width="32" height="{height:.2f}" rx="5" fill="{fill}" opacity="{opacity}"><title>{esc(week["week_start"])}: {week["contributions"]} contributions{" (partial week)" if week["partial"] else ""}</title></rect>')
        text(center, 303 - height, week["contributions"], 16, theme["muted"], anchor="middle")
        start = date(week["week_start"])
        text(center, 333, f"{start.month:02d}/{start.day:02d}", 16, theme["muted"], anchor="middle")

    panel(752, 192, 416, 156)
    text(776, 226, "Primary language", 22, weight="600")
    text(776, 249, "Non-fork repos · repository count", 16, theme["muted"])
    groups = language_groups(snapshot)
    total = metrics["non_fork_repositories"]
    cursor = 776.0
    for index, (label, number) in enumerate(groups):
        width = 368 * number / max(1, total)
        svg.append(f'<rect x="{cursor:.2f}" y="262" width="{width:.2f}" height="7" fill="{theme["accents"][index]}"><title>{esc(label)}: {number} repositories</title></rect>')
        cursor += width
    for index, (label, number) in enumerate(groups):
        x = 776 + (index % 2) * 184
        y = 293 + (index // 2) * 23
        svg.append(f'<circle cx="{x + 4}" cy="{y - 5}" r="4" fill="{theme["accents"][index]}"/>')
        short_label = label if len(label) <= 16 else label[:15] + "…"
        text(x + 15, y, f"{short_label} {number}", 16, theme["muted"])
    if not groups:
        text(776, 300, "No non-fork repositories", 16, theme["muted"])

    text(32, 370, "Source: GitHub API · Non-fork counts and languages exclude the profile repository.", 13, theme["muted"])
    svg.extend(["</g>", "</svg>"])
    result = "\n".join(svg) + "\n"
    ET.fromstring(result)
    return result


def render_mobile_svg(snapshot: dict, mode: str) -> str:
    theme = THEMES[mode]
    svg = [
        '<svg xmlns="http://www.w3.org/2000/svg" width="600" height="900" viewBox="0 0 600 900" role="img" aria-labelledby="title description">',
        f'<title id="title">Public GitHub activity for {esc(snapshot["account"])}</title>',
        '<desc id="description">Public repository and follower counts, last-year GitHub contributions, the most recent twelve weeks including the current partial week, and primary language counts for non-fork repositories excluding the profile repository.</desc>',
        f'<rect width="600" height="900" rx="22" fill="{theme["bg"]}"/>',
        f'<g font-family="{FONT}">',
    ]

    def text(x: float, y: float, content: object, size: int = 28, color: str | None = None, weight: str = "400", anchor: str = "start") -> None:
        svg.append(f'<text x="{x:g}" y="{y:g}" font-size="{size}" fill="{color or theme["text"]}" font-weight="{weight}" text-anchor="{anchor}">{esc(content)}</text>')

    def panel(x: int, y: int, width: int, height: int) -> None:
        svg.append(f'<rect x="{x}" y="{y}" width="{width}" height="{height}" rx="22" fill="{theme["panel"]}" stroke="{theme["border"]}"/>')

    text(28, 44, "GitHub snapshot", 32, weight="650")
    text(28, 79, "GitHub / " + snapshot["account"], 28, theme["muted"])
    metrics = snapshot["metrics"]
    metric_items = [
        ("Public repos", metrics["public_repositories"]),
        ("Non-fork repos", metrics["non_fork_repositories"]),
        ("Followers", metrics["followers"]),
        ("Contributions", metrics["contributions_last_year"]),
    ]
    for index, (label, number) in enumerate(metric_items):
        x = 28 + (index % 2) * 284
        y = 108 + (index // 2) * 148
        panel(x, y, 260, 132)
        svg.append(f'<rect x="{x + 22}" y="{y + 22}" width="4" height="35" rx="2" fill="{theme["accents"][index % 3]}"/>')
        text(x + 39, y + 59, f"{number:,}", 52, weight="650")
        if index == 3:
            text(x + 22, y + 95, label, 28, theme["muted"])
            text(x + 22, y + 124, "last year", 28, theme["muted"])
        else:
            text(x + 22, y + 107, label, 28, theme["muted"])

    panel(28, 408, 544, 214)
    text(52, 451, "Weekly contributions", 32, weight="600")
    text(52, 484, "12 weeks · current week in blue", 28, theme["muted"])
    recent = snapshot["weekly_contributions"]
    maximum = max(1, *(week["contributions"] for week in recent))
    peak = max(range(len(recent)), key=lambda index: recent[index]["contributions"])
    for index, week in enumerate(recent):
        center = 70 + index * 42
        height = max(2, 52 * week["contributions"] / maximum)
        fill = theme["accents"][0] if index < 11 else theme["accents"][1]
        svg.append(f'<rect x="{center - 13}" y="{578 - height:.2f}" width="26" height="{height:.2f}" rx="5" fill="{fill}"><title>{esc(week["week_start"])}: {week["contributions"]} contributions{" (partial week)" if week["partial"] else ""}</title></rect>')
        # Peak/current labels keep numbers readable at phone width. Every bar
        # also retains its exact date and count in a native SVG title.
        if index in {peak, 11}:
            text(center, 569 - height, week["contributions"], 28, theme["muted"], anchor="middle")
        if index in {0, 5, 11}:
            start = date(week["week_start"])
            text(center, 609, f"{start.month:02d}/{start.day:02d}", 28, theme["muted"], anchor="middle")

    panel(28, 642, 544, 224)
    text(52, 684, "Primary language", 32, weight="600")
    text(52, 718, "Non-fork repos · repository count", 28, theme["muted"])
    groups = language_groups(snapshot)
    total = metrics["non_fork_repositories"]
    cursor = 52.0
    for index, (label, number) in enumerate(groups):
        width = 496 * number / max(1, total)
        svg.append(f'<rect x="{cursor:.2f}" y="735" width="{width:.2f}" height="9" fill="{theme["accents"][index]}"><title>{esc(label)}: {number} repositories</title></rect>')
        cursor += width
    for index, (label, number) in enumerate(groups):
        x = 52 + (index % 2) * 248
        y = 779 + (index // 2) * 35
        svg.append(f'<circle cx="{x + 5}" cy="{y - 8}" r="5" fill="{theme["accents"][index]}"/>')
        mobile_label = "Other" if label == "Other languages" else label
        short_label = mobile_label if len(mobile_label) <= 12 else mobile_label[:11] + "…"
        text(x + 20, y, f"{short_label} {number}", 28, theme["muted"])
    if not groups:
        text(52, 800, "No non-fork repositories", 28, theme["muted"])
    text(28, 894, "Updated " + snapshot["snapshot_date"] + " UTC", 28, theme["muted"])
    svg.extend(["</g>", "</svg>"])
    result = "\n".join(svg) + "\n"
    ET.fromstring(result)
    return result


def preserve_fetch_time(snapshot: dict, previous_path: Path) -> None:
    try:
        previous = json.loads(previous_path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError):
        return
    if not isinstance(previous, dict):
        return
    comparison = {key: value for key, value in previous.items() if key != "fetched_at_utc"}
    current = {key: value for key, value in snapshot.items() if key != "fetched_at_utc"}
    fetched = previous.get("fetched_at_utc")
    if comparison == current and isinstance(fetched, str) and re.fullmatch(r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z", fetched):
        snapshot["fetched_at_utc"] = fetched


def write_outputs(outputs: dict[Path, str]) -> int:
    """Stage complete valid cards before replacing any existing output."""
    changed: dict[Path, bytes] = {}
    previous: dict[Path, bytes | None] = {}
    for path, content in outputs.items():
        target = content.encode("utf-8")
        try:
            old = path.read_bytes()
        except FileNotFoundError:
            old = None
        if old != target:
            changed[path] = target
            previous[path] = old
    if not changed:
        return 0
    with tempfile.TemporaryDirectory(prefix=".profile-stats-", dir=ROOT) as temp:
        staging = Path(temp)
        paths = list(changed)
        for index, path in enumerate(paths):
            path.parent.mkdir(parents=True, exist_ok=True)
            (staging / str(index)).write_bytes(changed[path])
            if previous[path] is not None:
                (staging / f"backup-{index}").write_bytes(previous[path])
        replaced: list[tuple[int, Path]] = []
        try:
            for index, path in enumerate(paths):
                os.replace(staging / str(index), path)
                replaced.append((index, path))
        except OSError:
            for index, path in reversed(replaced):
                if previous[path] is None:
                    path.unlink(missing_ok=True)
                else:
                    os.replace(staging / f"backup-{index}", path)
            raise
    return len(changed)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--username", default=DEFAULT_USERNAME, help="GitHub profile login")
    args = parser.parse_args()
    if not re.fullmatch(r"[A-Za-z0-9](?:[A-Za-z0-9-]{0,37}[A-Za-z0-9])?", args.username):
        parser.error("--username must be a valid GitHub login")
    try:
        snapshot = fetch_snapshot(args.username, dt.datetime.now(dt.timezone.utc))
        data_path = ROOT / "data/public-stats.json"
        preserve_fetch_time(snapshot, data_path)
        outputs = {
            ROOT / "assets/activity-dark.svg": render_svg(snapshot, "dark"),
            ROOT / "assets/activity-light.svg": render_svg(snapshot, "light"),
            ROOT / "assets/activity-mobile-dark.svg": render_mobile_svg(snapshot, "dark"),
            ROOT / "assets/activity-mobile-light.svg": render_mobile_svg(snapshot, "light"),
            data_path: json.dumps(snapshot, ensure_ascii=False, separators=(",", ":")) + "\n",
        }
        changed = write_outputs(outputs)
    except (StatsError, OSError, ET.ParseError) as error:
        message = str(error) if isinstance(error, StatsError) else "Could not safely write profile statistics."
        print(message + " Existing cards retained.", file=sys.stderr)
        return 1
    print(f"Public statistics for {args.username}: {changed} file(s) updated.")
    print(json.dumps(snapshot["metrics"], sort_keys=True))
    return 0


if __name__ == "__main__":
    sys.exit(main())
