# GitHub Analyzer

A web tool that pulls any GitHub user's public activity and renders a clean visual dashboard — commit frequency, language breakdown, top repositories, and contributor stats.

## Features
- Language breakdown (doughnut chart)
- Commit activity over the last 30 days (bar chart)
- Top repositories by stars
- Follower/following/star counts

## Stack
- **Backend:** Python 3, Flask, GitHub REST API v3
- **Frontend:** Vanilla JS, Chart.js, Space Grotesk + JetBrains Mono

## Setup
```bash
git clone https://github.com/djareddirdjad/github-analyzer
cd github-analyzer
pip install -r requirements.txt
python app.py
```
Open `http://localhost:5000` in your browser.

Built by [djareddirdjad](https://github.com/djareddirdjad)
