import os
import time
import json
import requests
from typing import Optional, List
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

KIE_API_KEY = os.getenv("KIE_API_KEY")
BASE_URL = "https://api.kie.ai/api/v1"

def upload_image(image_path: str) -> str:
    """Upload une image locale et retourne l'URL"""
    headers = {"Authorization": f"Bearer {KIE_API_KEY}"}
    
    with open(image_path, 'rb') as f:
        files = {'file': f}
        r = requests.post(f"{BASE_URL}/files/upload", headers=headers, files=files, timeout=60)
    
    print(f"Upload {Path(image_path).name}: {r.status_code}")
    r.raise_for_status()
    data = r.json()
    
    if data.get("code") != 200:
        raise RuntimeError(f"Upload error: {data}")
    
    url = data["data"]["url"]
    print(f"  → URL: {url}")
    return url

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
    # Cherche les images dans le dossier inputs/
    inputs_dir = Path(__file__).parent / "inputs"
    image_files = list(inputs_dir.glob("*.jpg")) + list(inputs_dir.glob("*.png")) + list(inputs_dir.glob("*.jpeg")) + list(inputs_dir.glob("*.webp"))
    
    if not image_files:
        print(f"❌ Aucune image trouvée dans {inputs_dir}")
        print("   Place une ou plusieurs images (jpg/png/webp) dans le dossier 'inputs/'")
        exit(1)
    
    print(f"✅ {len(image_files)} image(s) trouvée(s)")
    
    # Limite : max 8 images pour Nano Banana Pro (doc officielle)
    max_images = 8
    if len(image_files) > max_images:
        print(f"⚠️  Limite de {max_images} images, seules les {max_images} premières seront utilisées\n")
        image_files = image_files[:max_images]
    else:
        print()
    
    # Validation de taille (max 30MB)
    for img_path in image_files:
        size_mb = img_path.stat().st_size / (1024 * 1024)
        if size_mb > 30:
            print(f"❌ {img_path.name} est trop grande ({size_mb:.1f}MB), max 30MB")
            exit(1)
    
    # Upload les images
    uploaded_urls = []
    for img_path in image_files:
        url = upload_image(str(img_path))
        uploaded_urls.append(url)
    
    print(f"\n=== TEST: Génération avec {len(uploaded_urls)} image(s) en input ===")
    
    # Prompt pour éditer/transformer l'image
    prompt = "studio shot of a mannequin wearing the clothing item, professional ecommerce background, 3:4 aspect ratio"
    
    print(f"Prompt: {prompt}")
    print(f"Images input: {len(uploaded_urls)}")
    
    task_id = create_task(prompt, image_urls=uploaded_urls)
    task_data = poll(task_id)
    url = extract_url(task_data)
    print(f"\n✅ Generated URL: {url}\n")
