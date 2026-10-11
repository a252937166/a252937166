#!/usr/bin/env python3
"""Fetch public profile statistics. Authentication is never printed or saved."""
import argparse
import collections
import datetime as dt
import json
import pathlib
import subprocess
import time

LOGIN = "a252937166"
RESOLVE_IP = None
AUTH_TOKEN = None


def api(endpoint, query=None, variables=None):
    global AUTH_TOKEN
    args = ["gh", "api", endpoint]
    payload = None
    if query is not None:
        args += ["--input", "-"]
        payload = json.dumps({"query": query, "variables": variables or {}})
    if RESOLVE_IP:
        if AUTH_TOKEN is None:
            token_result = subprocess.run(["gh", "auth", "token"], text=True, capture_output=True, check=True)
            AUTH_TOKEN = token_result.stdout.strip()
        config = [
            'url = ' + json.dumps("https://api.github.com/" + endpoint),
            'resolve = ' + json.dumps("api.github.com:443:" + RESOLVE_IP),
            'header = ' + json.dumps("Authorization: Bearer " + AUTH_TOKEN),
            'header = ' + json.dumps("Accept: application/vnd.github+json"),
            'silent', 'show-error', 'fail', 'connect-timeout = 8', 'max-time = 30',
        ]
        if payload is not None:
            config += ['header = "Content-Type: application/json"', 'request = "POST"',
                       'data-binary = ' + json.dumps(payload)]
        args = ["curl", "--config", "-"]
        payload = "\n".join(config) + "\n"
    for attempt in range(4):
        result = subprocess.run(args, input=payload, text=True, capture_output=True, timeout=35)
        if result.returncode == 0:
            break
        if attempt == 3:
            raise RuntimeError(f"GitHub request failed with exit code {result.returncode}")
        time.sleep(0.5 * (2 ** attempt))
    data = json.loads(result.stdout)
    if data.get("errors"):
        raise RuntimeError(json.dumps(data["errors"]))
    return data


REPOS_QUERY = """
query($login:String!,$cursor:String){
  user(login:$login){
    repositories(first:100,after:$cursor,privacy:PUBLIC,isFork:false,ownerAffiliations:OWNER){
      totalCount pageInfo{hasNextPage endCursor}
      nodes{
        name nameWithOwner url isPrivate isFork isArchived stargazerCount forkCount
        languages(first:8,orderBy:{field:SIZE,direction:DESC}){
          totalSize pageInfo{hasNextPage endCursor} edges{size node{name color}}
        }
      }
    }
  }
}
"""

LANGUAGES_QUERY = """
query($owner:String!,$name:String!,$cursor:String!){
  repository(owner:$owner,name:$name){
    isPrivate languages(first:100,after:$cursor,orderBy:{field:SIZE,direction:DESC}){
      totalSize pageInfo{hasNextPage endCursor} edges{size node{name color}}
    }
  }
}
"""

ACTIVITY_QUERY = """
query($login:String!){
  user(login:$login){
    contributionsCollection{
      startedAt endedAt hasAnyRestrictedContributions restrictedContributionsCount
      totalCommitContributions totalIssueContributions totalPullRequestContributions
      totalPullRequestReviewContributions totalRepositoryContributions
      contributionCalendar{totalContributions weeks{firstDay contributionDays{date contributionCount}}}
      commitContributionsByRepository(maxRepositories:100){repository{isPrivate}}
      issueContributions(first:100){totalCount nodes{issue{repository{isPrivate}}}}
      pullRequestContributions(first:100){totalCount nodes{pullRequest{repository{isPrivate}}}}
      pullRequestReviewContributions(first:100){totalCount nodes{pullRequestReview{repository{isPrivate}}}}
      repositoryContributions(first:100){totalCount nodes{repository{isPrivate}}}
    }
  }
}
"""


def main(output):
    started = dt.datetime.now(dt.timezone.utc)
    user = api(f"users/{LOGIN}")
    profile = {key: user.get(key) for key in (
        "login", "name", "html_url", "avatar_url", "public_repos", "followers",
        "following", "created_at", "updated_at",
    )}
    repos = []
    cursor = None
    page_count = 0
    extra_language_queries = 0
    while True:
        data = api("graphql", REPOS_QUERY, {"login": LOGIN, "cursor": cursor})
        connection = data["data"]["user"]["repositories"]
        page_count += 1
        for repo in connection["nodes"]:
            if repo["isPrivate"] or repo["isFork"]:
                raise RuntimeError("Public non-fork repository query returned an out-of-scope repository")
            language_connection = repo["languages"]
            language_edges = list(language_connection["edges"])
            while language_connection["pageInfo"]["hasNextPage"]:
                extra = api("graphql", LANGUAGES_QUERY, {
                    "owner": LOGIN, "name": repo["name"],
                    "cursor": language_connection["pageInfo"]["endCursor"],
                })["data"]["repository"]
                extra_language_queries += 1
                if extra["isPrivate"]:
                    raise RuntimeError("A repository became private during language pagination")
                language_connection = extra["languages"]
                language_edges += language_connection["edges"]
            language_bytes = sum(edge["size"] for edge in language_edges)
            if language_bytes != language_connection["totalSize"]:
                raise RuntimeError(f"Incomplete language pagination for public repository {repo['name']}")
            repos.append({
                "name": repo["name"], "full_name": repo["nameWithOwner"], "url": repo["url"],
                "archived": repo["isArchived"], "stars": repo["stargazerCount"],
                "forks": repo["forkCount"], "language_bytes": language_bytes,
                "languages": [
                    {"name": edge["node"]["name"], "color": edge["node"]["color"], "bytes": edge["size"]}
                    for edge in language_edges
                ],
            })
        if not connection["pageInfo"]["hasNextPage"]:
            break
        cursor = connection["pageInfo"]["endCursor"]
    if len(repos) != connection["totalCount"]:
        raise RuntimeError("Repository pagination is incomplete")
    languages = collections.Counter()
    colors = {}
    for repo in repos:
        for language in repo["languages"]:
            languages[language["name"]] += language["bytes"]
            colors[language["name"]] = language["color"]
    total_bytes = sum(languages.values())
    activity = api("graphql", ACTIVITY_QUERY, {"login": LOGIN})["data"]["user"]["contributionsCollection"]
    calendar = activity["contributionCalendar"]
    private_commit_repos = sum(int(item["repository"]["isPrivate"]) for item in activity["commitContributionsByRepository"])
    privacy_counts = {"private_commit_repositories": private_commit_repos}
    for key, entity in (
        ("issueContributions", "issue"), ("pullRequestContributions", "pullRequest"),
        ("pullRequestReviewContributions", "pullRequestReview"), ("repositoryContributions", None),
    ):
        connection = activity[key]
        if connection["totalCount"] != len(connection["nodes"]):
            raise RuntimeError("Contribution privacy check needs more pagination")
        privacy_counts["private_" + key] = sum(
            int((node[entity]["repository"] if entity else node["repository"])["isPrivate"])
            for node in connection["nodes"]
        )
    if len(activity["commitContributionsByRepository"]) == 100:
        raise RuntimeError("Commit privacy check may exceed maxRepositories")
    if any(privacy_counts.values()) or activity["restrictedContributionsCount"] or activity["hasAnyRestrictedContributions"]:
        raise RuntimeError("Calendar includes restricted/private activity; refusing to label it public")
    contribution_type_total = sum(activity[key] for key in (
        "totalCommitContributions", "totalIssueContributions", "totalPullRequestContributions",
        "totalPullRequestReviewContributions", "totalRepositoryContributions",
    ))
    day_total = sum(day["contributionCount"] for week in calendar["weeks"] for day in week["contributionDays"])
    if contribution_type_total != calendar["totalContributions"] or day_total != calendar["totalContributions"]:
        raise RuntimeError("Contribution totals do not reconcile")
    today = dt.datetime.now(dt.timezone.utc).date()
    weeks = []
    for week in calendar["weeks"][-16:]:
        start = dt.date.fromisoformat(week["firstDay"])
        end = start + dt.timedelta(days=6)
        weeks.append({
            "week_start": start.isoformat(), "week_end": end.isoformat(),
            "contributions": sum(day["contributionCount"] for day in week["contributionDays"]),
            "days_in_range": len(week["contributionDays"]), "partial": end >= today,
        })
    completed = dt.datetime.now(dt.timezone.utc)
    result = {
        "fetched_at": completed.isoformat(timespec="seconds").replace("+00:00", "Z"),
        "fetch_started_at": started.isoformat(timespec="seconds").replace("+00:00", "Z"),
        "profile": profile,
        "metrics": {
            "public_repositories": profile["public_repos"],
            "owned_public_nonfork_repositories": len(repos),
            "archived_in_scope": sum(int(repo["archived"]) for repo in repos),
            "received_stars": sum(repo["stars"] for repo in repos),
            "received_forks": sum(repo["forks"] for repo in repos),
            "followers": profile["followers"],
            "public_contributions_last_year": calendar["totalContributions"],
            "language_bytes": total_bytes,
        },
        "languages": [
            {"name": name, "bytes": count, "percent": round(count / total_bytes * 100, 4) if total_bytes else 0,
             "color": colors[name]}
            for name, count in languages.most_common()
        ],
        "activity": {
            "started_at": activity["startedAt"], "ended_at": activity["endedAt"],
            "public_only_verified": True,
            "restricted_contributions": activity["restrictedContributionsCount"],
            "privacy_counts": privacy_counts,
            "contribution_types": {key: activity[key] for key in (
                "totalCommitContributions", "totalIssueContributions", "totalPullRequestContributions",
                "totalPullRequestReviewContributions", "totalRepositoryContributions",
            )},
            "weekly_last_16": weeks,
            "calendar": calendar,
        },
        "scope": {
            "profile_counts": "GET /users/a252937166 public profile counts. public_repos includes owned public forks.",
            "repositories": "All repositories owned by a252937166 with privacy=PUBLIC and isFork=false; archived repositories included.",
            "stars": "Sum of stargazerCount over owned public non-fork repositories, including archived repositories.",
            "forks": "Sum of forkCount over owned public non-fork repositories, including archived repositories.",
            "languages": "Sum of repository GitHub Linguist language bytes, with all language pages fetched, over the same repository scope. This measures repository composition, not personal proficiency or authored lines.",
            "contributions": "GitHub contributionsCollection default rolling one-year window. Calendar counts are used only after verifying zero restricted contributions and zero private repository flags across all contribution types. Includes public work outside owned repositories.",
            "weekly": "Sunday-to-Saturday contributionCalendar weeks, last 16 including current partial week; current week is marked partial.",
            "endpoints": ["https://api.github.com/users/a252937166", "https://api.github.com/graphql"],
            "repo_pages_fetched": page_count, "extra_language_pages_fetched": extra_language_queries,
        },
        "repositories": repos,
    }
    path = pathlib.Path(output)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps({"output": str(path), "fetched_at": result["fetched_at"], "metrics": result["metrics"],
                      "top_languages": result["languages"][:8], "weekly_last_16": weeks}, indent=2))


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", default=str(pathlib.Path(__file__).with_name("profile-stats-live.json")))
    parser.add_argument("--resolve-ip", help="Process-only API address obtained from a trusted resolver; normal TLS validation remains enabled")
    parsed = parser.parse_args()
    RESOLVE_IP = parsed.resolve_ip
    main(parsed.output)
