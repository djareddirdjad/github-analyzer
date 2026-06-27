from flask import Flask, render_template, request, jsonify
import requests
from collections import Counter

app = Flask(__name__)
GITHUB_API = "https://api.github.com"

def get_user(username):
    r = requests.get(f"{GITHUB_API}/users/{username}")
    return r.json() if r.status_code == 200 else None

def get_repos(username):
    repos = []
    page = 1
    while True:
        r = requests.get(f"{GITHUB_API}/users/{username}/repos", params={"per_page": 100, "page": page, "sort": "updated"})
        if r.status_code != 200: break
        data = r.json()
        if not data: break
        repos.extend(data)
        page += 1
    return repos

def get_events(username):
    r = requests.get(f"{GITHUB_API}/users/{username}/events/public", params={"per_page": 100})
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
    for event in events:
        if event.get("type") == "PushEvent":
            day = event["created_at"][:10]
            commits = len(event.get("payload", {}).get("commits", []))
            commit_days[day] += commits
    top_repos = sorted(repos, key=lambda r: r.get("stargazers_count", 0), reverse=True)[:5]
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
        },
        "stats": {
            "total_stars": stars,
            "languages": dict(lang_counter.most_common(8)),
            "commit_activity": dict(sorted(commit_days.items())[-30:]),
            "top_repos": [{"name": r["name"], "description": r.get("description") or "", "stars": r.get("stargazers_count", 0), "forks": r.get("forks_count", 0), "language": r.get("language") or "—", "url": r.get("html_url"), "updated": r.get("updated_at", "")[:10]} for r in top_repos],
        }
    })

if __name__ == "__main__":
    app.run(debug=True)
