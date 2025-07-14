import praw
import openai
import re
import os
from typing import List, Dict

# --- CONFIGURATION ---
REDDIT_CLIENT_ID = "YOUR_CLIENT_ID"
REDDIT_CLIENT_SECRET = "YOUR_CLIENT_SECRET"
REDDIT_USER_AGENT = "userpersona-script by /u/YOUR_USERNAME"
OPENAI_API_KEY = "YOUR_OPENAI_API_KEY"

# --- INITIALIZE API CLIENTS ---
openai.api_key = OPENAI_API_KEY
reddit = praw.Reddit(
    client_id=REDDIT_CLIENT_ID,
    client_secret=REDDIT_CLIENT_SECRET,
    user_agent=REDDIT_USER_AGENT,
    check_for_async=False
)

def extract_username(profile_url: str) -> str:
    match = re.search(r'reddit\.com/user/([^/]+)/?', profile_url)
    if match:
        return match.group(1)
    raise ValueError("Invalid Reddit profile URL.")

def fetch_user_content(username: str, limit=100) -> List[Dict]:
    user = reddit.redditor(username)
    content = []
    for post in user.submissions.new(limit=limit):
        content.append({
            "type": "post",
            "id": post.id,
            "title": post.title,
            "body": post.selftext,
            "permalink": f"https://www.reddit.com{post.permalink}"
        })
    for comment in user.comments.new(limit=limit):
        content.append({
            "type": "comment",
            "id": comment.id,
            "body": comment.body,
            "permalink": f"https://www.reddit.com{comment.permalink}"
        })
    return content

def build_persona_with_citations(content: List[Dict]) -> str:
    context = ""
    for idx, item in enumerate(content):
        if item['type'] == "post":
            context += f"[{idx}] POST: {item['title']} - {item['body']}\nURL: {item['permalink']}\n"
        else:
            context += f"[{idx}] COMMENT: {item['body']}\nURL: {item['permalink']}\n"
    prompt = (
        "Given the following Reddit posts and comments, build a detailed user persona. "
        "For each characteristic (e.g., interests, personality traits, values, writing style, demographics), "
        "cite the specific post or comment (by index) that supports your inference. "
        "Format your output as:\n\n"
        "Characteristic: Value (Cited from: [index])\n"
        "Example:\n"
        "Interests: Technology, Gaming (Cited from: [2], [7])\n"
        "Personality Traits: Curious, Helpful (Cited from: [5])\n"
        "...\n\n"
        "Reddit Data:\n"
        f"{context}"
    )
    response = openai.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[{"role": "user", "content": prompt}],
        max_tokens=800
    )
    return response.choices[0].message.content

def save_persona_to_file(persona: str, username: str):
    filename = f"sample_output_{username}.txt"
    with open(filename, "w", encoding="utf-8") as f:
        f.write(persona)
    print(f"Persona saved to {filename}")

def main():
    profile_url = input("Enter Reddit profile URL: ").strip()
    username = extract_username(profile_url)
    print(f"Fetching data for user: {username}")
    content = fetch_user_content(username)
    print(f"Fetched {len(content)} items. Building persona...")
    persona = build_persona_with_citations(content)
    save_persona_to_file(persona, username)
    print("Done.")

if __name__ == "__main__":
    main()
