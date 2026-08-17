import os
import json
import urllib.request
import urllib.error
import math

USERNAME = "teja0604"

# Fallback data if API rate-limited
FALLBACK_REPOS = {
    "Java": 35.0,
    "JavaScript": 25.0,
    "TypeScript": 15.0,
    "HTML": 10.0,
    "Python": 10.0,
    "CSS": 5.0,
}

FALLBACK_COMMITS = {
    "Java": 40.0,
    "JavaScript": 20.0,
    "TypeScript": 15.0,
    "HTML": 15.0,
    "Python": 5.0,
    "CSS": 5.0,
}

COLORS = {
    "Java": "#b07219",
    "JavaScript": "#f1e05a",
    "TypeScript": "#3178c6",
    "HTML": "#e34c26",
    "CSS": "#563d7c",
    "Python": "#3572A5",
    "Other": "#8b949e"
}

def fetch_data():
    try:
        req = urllib.request.Request(
            f"https://api.github.com/users/{USERNAME}/repos?per_page=100",
            headers={"User-Agent": "Mozilla/5.0"}
        )
        with urllib.request.urlopen(req, timeout=10) as response:
            repos = json.loads(response.read().decode())
        
        lang_bytes = {}
        for repo in repos:
            if repo["fork"]:
                continue
            lang_url = repo["languages_url"]
            try:
                l_req = urllib.request.Request(lang_url, headers={"User-Agent": "Mozilla/5.0"})
                with urllib.request.urlopen(l_req, timeout=5) as l_resp:
                    langs = json.loads(l_resp.read().decode())
                    for l, b in langs.items():
                        lang_bytes[l] = lang_bytes.get(l, 0) + b
            except:
                pass
                
        if not lang_bytes:
            return FALLBACK_REPOS, FALLBACK_COMMITS
            
        total = sum(lang_bytes.values())
        repo_langs = {k: (v/total)*100 for k, v in lang_bytes.items()}
        
        # We use repo_langs for both to approximate since commits are too heavy to fetch
        return repo_langs, repo_langs

    except Exception as e:
        print(f"API Error: {e}")
        return FALLBACK_REPOS, FALLBACK_COMMITS

def generate_donut_svg(title, data, filename):
    # Sort and take top 5, rest in Other
    sorted_data = sorted(data.items(), key=lambda x: x[1], reverse=True)
    top_5 = sorted_data[:5]
    other = sum(v for k, v in sorted_data[5:])
    if other > 0:
        top_5.append(("Other", other))
        
    total = sum(v for k, v in top_5)
    
    W, H = 400, 200
    CX, CY, R, STROKE = 280, 100, 60, 25
    
    svg = [
        f'<svg width="{W}" height="{H}" viewBox="0 0 {W} {H}" xmlns="http://www.w3.org/2000/svg">',
        f'<rect width="{W}" height="{H}" fill="#0d1117" rx="8" stroke="#30363d" stroke-width="1"/>',
        f'<text x="25" y="30" fill="#58a6ff" font-family="system-ui, sans-serif" font-size="16" font-weight="bold">{title}</text>'
    ]
    
    start_angle = -90
    legend_y = 60
    
    for lang, val in top_5:
        pct = (val / total) * 100
        angle = (pct / 100) * 360
        
        color = COLORS.get(lang, "#8b949e")
        
        # Donut segment
        if pct > 0:
            # SVG arc
            x1 = CX + R * math.cos(math.radians(start_angle))
            y1 = CY + R * math.sin(math.radians(start_angle))
            
            end_angle = start_angle + angle
            # Handle full circle case
            if pct > 99.9:
                end_angle -= 0.1
                
            x2 = CX + R * math.cos(math.radians(end_angle))
            y2 = CY + R * math.sin(math.radians(end_angle))
            
            large_arc = 1 if angle > 180 else 0
            
            path = f"M {x1} {y1} A {R} {R} 0 {large_arc} 1 {x2} {y2}"
            
            svg.append(f'<path d="{path}" fill="none" stroke="{color}" stroke-width="{STROKE}" />')
            start_angle = end_angle
            
        # Legend
        svg.append(f'<circle cx="25" cy="{legend_y-4}" r="5" fill="{color}"/>')
        svg.append(f'<text x="40" y="{legend_y}" fill="#c9d1d9" font-family="system-ui, sans-serif" font-size="13">{lang} ({pct:.1f}%)</text>')
        legend_y += 22

    svg.append('</svg>')
    
    os.makedirs(os.path.dirname(filename), exist_ok=True)
    with open(filename, 'w', encoding='utf-8') as f:
        f.write('\n'.join(svg))

def main():
    print("Fetching data...")
    repo_data, commit_data = fetch_data()
    print("Generating SVGs...")
    generate_donut_svg("Top Languages by Repo", repo_data, "assets/top-languages-repo.svg")
    generate_donut_svg("Top Languages by Commit", commit_data, "assets/top-languages-commit.svg")
    print("Done!")

if __name__ == "__main__":
    main()
