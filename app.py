from flask import Flask, request, jsonify, render_template
import re
import requests
from urllib.parse import urljoin, urlparse
from bs4 import BeautifulSoup

visited = set()

EMAIL_RE = re.compile(r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}")

def extract_emails(text):
    return EMAIL_RE.findall(text)

def find_emails_and_stop(url, base_domain):
    stack = [url]
    while stack:
        current = stack.pop()
        if current in visited or not current.startswith(base_domain):
            continue
        visited.add(current)
        try:
            resp = requests.get(current, timeout=10, headers={"User-Agent": "Mozilla/5.0"})
            resp.raise_for_status()
        except requests.RequestException:
            continue
        soup = BeautifulSoup(resp.text, "html.parser")
        text = soup.get_text(separator=" ", strip=True)
        emails = extract_emails(text)
        if emails:
            return list(set(emails))
        for a in soup.find_all("a", href=True):
            nxt = urljoin(current, a["href"])
            parsed = urlparse(nxt)
            clean = f"{parsed.scheme}://{parsed.netloc}{parsed.path}"
            stack.append(clean)
    return []

app = Flask(__name__, template_folder=".")

@app.route("/")
def home():
    return render_template("index.html")

@app.route("/extract")
def extract():
    url = request.args.get("url", "").strip()
    if not url:
        return jsonify({"error": "no url provided"}), 400
    if not url.startswith(("http://", "https://")):
        url = "http://" + url
    parsed = urlparse(url)
    base_domain = f"{parsed.scheme}://{parsed.netloc}"
    emails = find_emails_and_stop(url, base_domain)
    return jsonify({"emails": emails})

if __name__ == "__main__":
    app.run(debug=True)