from flask import Flask, render_template, request, jsonify
import requests
from collections import Counter
import os

app = Flask(__name__)
GITHUB_API = "https://api.github.com"

def headers():
    token = os.environ.get("GITHUB_TOKEN")
    h = {"Accept": "application/vnd.github+json"}
    if token:
        h["Authorization"] = f"Bearer {token}"
    return h

def get_user(username):
    r = requests.get(f"{GITHUB_API}/users/{username}", headers=headers())
    return r.json() if r.status_code == 200 else None

def get_repos(username):
    repos, page = [], 1
    while True:
        r = requests.get(f"{GITHUB_API}/users/{username}/repos", headers=headers(), params={"per_page": 100, "page": page, "sort": "updated"})
        if r.status_code != 200: break
        data = r.json()
        if not data: break
        repos.extend(data)
        page += 1
    return repos

def get_events(username):
    r = requests.get(f"{GITHUB_API}/users/{username}/events/public", headers=headers(), params={"per_page": 100})
    return r.json() if r.status_code == 200 else []

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/analyze", methods=["POST"])
def analyze():
    username = request.json.get("username", "").strip()
    if not username:
        return jsonify({"error": "No username provided"}), 400
    user = get_user(username)
    if not user or "login" not in user:
        return jsonify({"error": "User not found"}), 404
    repos = get_repos(username)
    events = get_events(username)

    lang_counter = Counter()
    stars = 0
    for repo in repos:
        if repo.get("language"):
            lang_counter[repo["language"]] += 1
        stars += repo.get("stargazers_count", 0)

    commit_days = Counter()
    hour_counter = Counter()
    day_counter = Counter()
    DAYS = ["Mon","Tue","Wed","Thu","Fri","Sat","Sun"]
    for event in events:
        if event.get("type") == "PushEvent":
            ts = event["created_at"]
            day = ts[:10]
            commits = len(event.get("payload", {}).get("commits", []))
            commit_days[day] += commits
            from datetime import datetime
            dt = datetime.strptime(ts, "%Y-%m-%dT%H:%M:%SZ")
            hour_counter[dt.hour] += commits
            day_counter[DAYS[dt.weekday()]] += commits

    top_repos = sorted(repos, key=lambda r: r.get("stargazers_count", 0), reverse=True)[:6]
    peak_hour = max(hour_counter, key=hour_counter.get) if hour_counter else None
    peak_day = max(day_counter, key=day_counter.get) if day_counter else None

    return jsonify({
        "user": {
            "login": user["login"],
            "name": user.get("name") or user["login"],
            "bio": user.get("bio") or "",
            "avatar": user.get("avatar_url"),
            "followers": user.get("followers", 0),
            "following": user.get("following", 0),
            "public_repos": user.get("public_repos", 0),
            "location": user.get("location") or "",
            "created_at": user.get("created_at", "")[:10],
            "blog": user.get("blog") or "",
        },
        "stats": {
            "total_stars": stars,
            "languages": dict(lang_counter.most_common(8)),
            "commit_activity": dict(sorted(commit_days.items())[-30:]),
            "hour_activity": {str(h): hour_counter.get(h, 0) for h in range(24)},
            "day_activity": {d: day_counter.get(d, 0) for d in DAYS},
            "peak_hour": peak_hour,
            "peak_day": peak_day,
            "top_repos": [
                {
                    "name": r["name"],
                    "description": r.get("description") or "",
                    "stars": r.get("stargazers_count", 0),
                    "forks": r.get("forks_count", 0),
                    "language": r.get("language") or "—",
                    "url": r.get("html_url"),
                    "updated": r.get("updated_at", "")[:10],
                    "topics": r.get("topics", [])[:4],
                }
                for r in top_repos
            ],
        }
    })

# Public API endpoint
@app.route("/api/user/<username>")
def api_user(username):
    user = get_user(username)
    if not user or "login" not in user:
        return jsonify({"error": "User not found"}), 404
    repos = get_repos(username)
    stars = sum(r.get("stargazers_count", 0) for r in repos)
    lang_counter = Counter(r["language"] for r in repos if r.get("language"))
    return jsonify({
        "login": user["login"],
        "name": user.get("name"),
        "bio": user.get("bio"),
        "public_repos": user.get("public_repos", 0),
        "followers": user.get("followers", 0),
        "total_stars": stars,
        "top_languages": dict(lang_counter.most_common(5)),
        "location": user.get("location"),
    })

if __name__ == "__main__":
    app.run(debug=True)
