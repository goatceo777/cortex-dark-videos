"""
Appelle l'API locale MoneyPrinterTurbo pour transformer chaque post
(deja ecrit par Claude/OpenAI dans n8n) en video verticale MP4,
avec voix off arabe (edge-tts, gratuit) et sous-titres synchronises.
"""
import json
import os
import time
import urllib.request

BASE = "http://127.0.0.1:8080/api/v1"
OUT_DIR = "output"
os.makedirs(OUT_DIR, exist_ok=True)

VOICE = "ar-SA-HamedNeural"


def call(method, path, body=None):
    req = urllib.request.Request(
        f"{BASE}{path}",
        data=json.dumps(body).encode() if body else None,
        headers={"Content-Type": "application/json"},
        method=method,
    )
    with urllib.request.urlopen(req, timeout=60) as r:
        return json.loads(r.read())


def render_one(post: dict, index: int):
    narration = " ".join(
        filter(None, [post.get("hook"), post.get("script"), post.get("caption")])
    )
    body = {
        "video_subject": post.get("title") or f"post-{index}",
        "video_script": narration,
        "video_terms": "calm cinematic slow motion silhouette",
        "video_aspect": "9:16",
        "video_language": "ar",
        "voice_name": VOICE,
        "subtitle_enabled": True,
        "video_source": "pexels",
    }
    task_id = call("POST", "/videos", body)["data"]["task_id"]

    for _ in range(60):
        time.sleep(10)
        task = call("GET", f"/tasks/{task_id}")["data"]
        if task.get("state") == 1:
            video_url = task["videos"][0]
            local_path = f"{OUT_DIR}/post-{index}.mp4"
            urllib.request.urlretrieve(video_url, local_path)
            print(f"OK: {local_path}")
            return
        if task.get("state") == -1:
            raise RuntimeError(f"Rendu echoue pour le post {index}: {task}")

    raise TimeoutError(f"Rendu trop long pour le post {index}")


if __name__ == "__main__":
    posts = json.loads(os.environ["POSTS_JSON"])
    for i, post in enumerate(posts):
        render_one(post, i)
