import os
import time
import json
import requests
from typing import Optional
from dotenv import load_dotenv

load_dotenv()

KIE_API_KEY = os.getenv("KIE_API_KEY")
BASE_URL = "https://api.kie.ai/api/v1"

def create_task(prompt, image_urls=None, resolution="1K"):
    payload = {
        "model": "nano-banana-pro",
        "input": {
            "prompt": prompt,
            "image_input": image_urls or [],
            "aspect_ratio": "3:4",
            "resolution": resolution,
            "output_format": "png",
        },
    }
    headers = {
        "Authorization": f"Bearer {KIE_API_KEY}",
        "Content-Type": "application/json",
    }
    r = requests.post(f"{BASE_URL}/jobs/createTask", json=payload, headers=headers, timeout=60)
    print("createTask:", r.status_code, r.text[:200])
    r.raise_for_status()
    data = r.json()
    if data.get("code") != 200:
        raise RuntimeError(f"Kie error: {data}")
    return data["data"]["taskId"]

def poll(task_id, timeout=90):
    headers = {"Authorization": f"Bearer {KIE_API_KEY}"}
    start = time.time()
    while True:
        r = requests.get(f"{BASE_URL}/jobs/recordInfo", headers=headers,
                         params={"taskId": task_id}, timeout=30)
        r.raise_for_status()
        data = r.json()["data"]
        state = data["state"]
        print("state:", state)
        if state == "success":
            return data
        if state == "fail":
            raise RuntimeError(f"fail: {data.get('failMsg')}")
        if time.time() - start > timeout:
            raise RuntimeError("timeout")
        time.sleep(3)

def extract_url(task_data: dict) -> Optional[str]:
    raw = task_data.get("resultJson")
    if not raw:
        return None
    obj = json.loads(raw)
    urls = obj.get("resultUrls") or obj.get("resulturls") or []
    return urls[0] if urls else None

if __name__ == "__main__":
    prompt = "studio shot of a mannequin wearing a red vintage coat, ecommerce background"
    image_urls = []  # ou ["https://..."] pour les tests d'édition
    task_id = create_task(prompt, image_urls=image_urls)
    task_data = poll(task_id)
    url = extract_url(task_data)
    print("Generated URL:", url)
