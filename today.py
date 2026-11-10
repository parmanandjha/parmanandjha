import os
import re
import json
import datetime
import urllib.request

USER_NAME = os.environ.get("USER_NAME", "parmanandjha")
ACCESS_TOKEN = os.environ.get("ACCESS_TOKEN", os.environ.get("GITHUB_TOKEN", ""))

def calculate_uptime(birth_date=datetime.date(2008, 1, 15)):
    today = datetime.date.today()
    years = today.year - birth_date.year
    months = today.month - birth_date.month
    days = today.day - birth_date.day
    if days < 0:
        months -= 1
        prev_month = today.month - 1 or 12
        prev_year = today.year if prev_month != 12 else today.year - 1
        # Days in previous month
        days_in_prev = (datetime.date(today.year, today.month, 1) - datetime.date(prev_year, prev_month, 1)).days
        days += days_in_prev
    if months < 0:
        years -= 1
        months += 12
    return f"{years} years, {months} months, {days} days"

def http_get(url):
    req = urllib.request.Request(url)
    req.add_header("User-Agent", "GitHub-Profile-Updater")
    if ACCESS_TOKEN:
        req.add_header("Authorization", f"Bearer {ACCESS_TOKEN}")
    with urllib.request.urlopen(req, timeout=10) as resp:
        return json.loads(resp.read().decode("utf-8"))

def get_stats():
    stats = {
        "repos": 3,
        "stars": 0,
        "commits": 9,
        "followers": 0,
        "loc_total": 24850,
        "loc_add": 28420,
        "loc_del": 3570
    }
    
    try:
        u_data = http_get(f"https://api.github.com/users/{USER_NAME}")
        stats["repos"] = u_data.get("public_repos", stats["repos"])
        stats["followers"] = u_data.get("followers", stats["followers"])
        
        repos = http_get(f"https://api.github.com/users/{USER_NAME}/repos?per_page=100")
        stats["stars"] = sum(r.get("stargazers_count", 0) for r in repos)
        
        total_commits = 0
        for r in repos:
            repo_name = r.get("name")
            try:
                commits = http_get(f"https://api.github.com/repos/{USER_NAME}/{repo_name}/commits?per_page=100")
                total_commits += len(commits)
            except Exception:
                pass
        if total_commits > 0:
            stats["commits"] = total_commits
    except Exception as e:
        print("Note: Using baseline stats or cached values (API request skipped/failed):", e)
        
    return stats

def update_svg(filepath, uptime_str, stats):
    if not os.path.exists(filepath):
        return
        
    with open(filepath, "r", encoding="utf-8") as f:
        content = f.read()
        
    # Update Uptime
    content = re.sub(r'id="age_data">[^<]+<', f'id="age_data">{uptime_str}<', content)
    # Update Repos
    content = re.sub(r'id="repo_data">[^<]+<', f'id="repo_data">{stats["repos"]}<', content)
    # Update Stars
    content = re.sub(r'id="star_data">[^<]+<', f'id="star_data">{stats["stars"]}<', content)
    # Update Commits
    content = re.sub(r'id="commit_data">[^<]+<', f'id="commit_data">{stats["commits"]:,}<', content)
    # Update Followers
    content = re.sub(r'id="follower_data">[^<]+<', f'id="follower_data">{stats["followers"]}<', content)
    
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(content)
    print(f"Updated {filepath} successfully.")

def main():
    uptime = calculate_uptime()
    stats = get_stats()
    print("Calculated Uptime:", uptime)
    print("Collected Stats:", stats)
    
    script_dir = os.path.dirname(os.path.abspath(__file__))
    update_svg(os.path.join(script_dir, "dark_mode.svg"), uptime, stats)
    update_svg(os.path.join(script_dir, "light_mode.svg"), uptime, stats)

if __name__ == "__main__":
    main()
