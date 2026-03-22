from flask import Flask, request, jsonify, Request
from flask_cors import CORS
from bs4 import BeautifulSoup
import re
import os
from dotenv import load_dotenv
load_dotenv()


class LargeRequest(Request):
    max_form_memory_size = 200 * 1024 * 1024


app = Flask(__name__)
app.request_class = LargeRequest
app.config["MAX_CONTENT_LENGTH"] = 200 * 1024 * 1024

# Allow requests from Vite frontend
frontend_url = os.getenv("FRONTEND_URL", "http://localhost:5173")

CORS(app, resources={r"/api/*": {"origins": frontend_url}})


def clean_text(text):
    if not text:
        return ""
    return " ".join(text.split()).strip()


def strip_degree(text):
    return clean_text(
        re.sub(r"\s*[•·]\s*(1st|2nd|3rd\+?)\s*$", "", text, flags=re.IGNORECASE)
    )


def is_noise(text):
    lower = text.lower()
    bad_phrases = [
        "mutual connection",
        "current:",
        "past:",
        "connect",
        "message",
        "follow",
        "try premium",
        "actively hiring",
        "search more efficiently",
        "free trial",
        "we’ll remind you",
        "we'll remind you",
    ]
    return any(x in lower for x in bad_phrases)


def shorten_role(role):
    if not role:
        return ""

    short_role = role.split("|")[0].strip()
    short_role = re.sub(r"\s+", " ", short_role).strip()
    short_role = short_role.replace("FedEx Dataworks", "FedEx")

    return short_role


def get_cards(soup):
    cards = soup.find_all("div", attrs={"role": "listitem"})
    if not cards:
        cards = soup.select("li.reusable-search__result-container")
    if not cards:
        cards = [soup]
    return cards


def extract_name_role_location(card):
    name = ""
    role = ""
    location = ""

    profile_link = card.find("a", href=lambda href: href and "/in/" in href)
    if profile_link:
        name = strip_degree(profile_link.get_text(" ", strip=True))

    all_ps = card.find_all("p", recursive=True)

    cleaned_lines = []
    seen = set()

    for p in all_ps:
        text = clean_text(p.get_text(" ", strip=True))
        text = strip_degree(text)

        if not text:
            continue
        if is_noise(text):
            continue
        if text.lower() in seen:
            continue

        seen.add(text.lower())
        cleaned_lines.append(text)

    if not name and cleaned_lines:
        name = cleaned_lines[0]

    remaining = [x for x in cleaned_lines if x.lower() != name.lower()]

    if len(remaining) >= 1:
        role = remaining[0]
    if len(remaining) >= 2:
        location = remaining[1]

    if not role or not location:
        raw_lines = [
            clean_text(x)
            for x in card.get_text("\n", strip=True).split("\n")
            if clean_text(x)
        ]

        filtered = []
        seen = set()
        for line in raw_lines:
            line = strip_degree(line)
            if not line or is_noise(line):
                continue
            if line.lower() in seen:
                continue
            seen.add(line.lower())
            filtered.append(line)

        filtered_wo_name = [x for x in filtered if x.lower() != name.lower()]

        if not role and len(filtered_wo_name) >= 1:
            role = filtered_wo_name[0]
        if not location and len(filtered_wo_name) >= 2:
            location = filtered_wo_name[1]

    if not name and not role and not location:
        return None

    return {
        "name": clean_text(name),
        "role": shorten_role(clean_text(role)),
        "location": clean_text(location),
    }


def parse_linkedin_results(html_content):
    soup = BeautifulSoup(html_content, "html.parser")
    cards = get_cards(soup)

    results = []
    seen = set()

    for card in cards:
        parsed = extract_name_role_location(card)
        if not parsed:
            continue

        if not parsed["name"]:
            continue
        if "premium" in parsed["name"].lower():
            continue

        key = (
            parsed["name"].lower(),
            parsed["role"].lower(),
            parsed["location"].lower(),
        )
        if key in seen:
            continue
        seen.add(key)

        results.append(parsed)

    return results


@app.errorhandler(413)
def too_large(_e):
    return jsonify({
        "error": "Upload too large",
        "message": "Your pasted/uploaded LinkedIn HTML is too large for the current limit."
    }), 413


@app.route("/api/health", methods=["GET"])
def health():
    return jsonify({"status": "ok"})


@app.route("/api/collect", methods=["POST"])
def collect():
    html_content = ""

    if request.content_type and "application/json" in request.content_type:
        data = request.get_json(silent=True) or {}
        html_content = data.get("html_content", "")
    else:
        html_content = request.form.get("html_content", "")
        uploaded_file = request.files.get("html_file")
        if uploaded_file and uploaded_file.filename:
            file_bytes = uploaded_file.read()
            html_content = file_bytes.decode("utf-8", errors="ignore")

    if not html_content.strip():
        return jsonify({
            "error": "Missing HTML content",
            "message": "Please paste LinkedIn HTML or upload an HTML file."
        }), 400

    results = parse_linkedin_results(html_content)

    return jsonify({
        "count": len(results),
        "results": results
    })


if __name__ == "__main__":
    app.run(debug=True, port=5000)