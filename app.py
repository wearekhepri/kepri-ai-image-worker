"""
Khepri AI Image Generation Worker
Phase 2: Modal deployment with FastAPI endpoint
"""
import os
import json
import time
import uuid
from typing import Optional, List
import modal

# Déclaration de l'application Modal
app = modal.App("khepri-kie-image-gen")

# Définition de l'image personnalisée
image = (
    modal.Image.debian_slim()
    .pip_install(
        "requests==2.31.0",
        "supabase==2.10.0",
        "python-dotenv==1.0.0",
    )
)

# Secrets Modal (à créer via modal secret create)
kie_secret = modal.Secret.from_name("kie-api-key")  # KIE_API_KEY
supabase_secret = modal.Secret.from_name("supabase-credentials")  # SUPABASE_URL, SUPABASE_ANON_KEY

BASE_URL = "https://api.kie.ai/api/v1"


@app.function(image=image, secrets=[kie_secret, supabase_secret], timeout=180)
@modal.fastapi_endpoint(method="POST", docs=True)
def generate(
    prompt: str,
    image_urls: Optional[List[str]] = None,
    aspect_ratio: str = "3:4",
    resolution: str = "2K",
    output_format: str = "png",
):
    """
    Generate an image with Kie.ai Nano Banana Pro.
    
    Args:
        prompt: Text description for image generation
        image_urls: Optional list of public image URLs (0-8 images) for image-to-image
        aspect_ratio: Output aspect ratio (default: 3:4)
        resolution: Image resolution - 1K, 2K, or 4K (default: 2K)
        output_format: Output format - png or jpg (default: png)
    
    Returns:
        JSON with status, task_id, and image_url
    """
    import requests
    
    kie_api_key = os.environ["KIE_API_KEY"]
    image_urls = image_urls or []
    
    # Validation
    if len(image_urls) > 8:
        return {
            "status": "error",
            "error": "Maximum 8 images allowed"
        }
    
    # Création de la tâche Kie.ai
    def create_task() -> str:
        payload = {
            "model": "nano-banana-pro",
            "input": {
                "prompt": prompt,
                "image_input": image_urls,
                "aspect_ratio": aspect_ratio,
                "resolution": resolution,
                "output_format": output_format,
            },
        }
        headers = {
            "Authorization": f"Bearer {kie_api_key}",
            "Content-Type": "application/json",
        }
        r = requests.post(
            f"{BASE_URL}/jobs/createTask",
            json=payload,
            headers=headers,
            timeout=60
        )
        try:
            data = r.json()
        except ValueError:
            raise Exception(f"Kie createTask returned non-JSON: {r.text[:200]}")
        
        if r.status_code != 200 or data.get("code") != 200:
            raise Exception(f"Kie createTask failed: {data}")
        
        return data["data"]["taskId"]
    
    # Polling du résultat
    def poll(task_id: str, timeout_seconds: int = 120) -> dict:
        headers = {"Authorization": f"Bearer {kie_api_key}"}
        start = time.time()
        
        while True:
            r = requests.get(
                f"{BASE_URL}/jobs/recordInfo",
                headers=headers,
                params={"taskId": task_id},
                timeout=30
            )
            try:
                data = r.json()
            except ValueError:
                raise Exception(f"Kie recordInfo non-JSON: {r.text[:200]}")
            
            if r.status_code != 200 or data.get("code") != 200:
                raise Exception(f"Kie recordInfo failed: {data}")
            
            task_data = data["data"]
            state = task_data.get("state")
            
            if state == "success":
                return task_data
            if state == "fail":
                raise Exception(f"Kie generation failed: {task_data.get('failMsg')}")
            if time.time() - start > timeout_seconds:
                raise Exception(f"Timeout after {timeout_seconds}s, last_state={state}")
            
            time.sleep(3)
    
    # Extraction de l'URL
    def extract_url(task_data: dict) -> Optional[str]:
        raw = task_data.get("resultJson")
        if not raw:
            return None
        obj = json.loads(raw)
        urls = obj.get("resultUrls") or obj.get("resulturls") or []
        return urls[0] if urls else None
    
    # Exécution
    try:
        task_id = create_task()
        task_data = poll(task_id)
        url = extract_url(task_data)
        
        if not url:
            return {
                "status": "error",
                "task_id": task_id,
                "error": "No URL in resultJson",
            }
        
        return {
            "status": "success",
            "task_id": task_id,
            "image_url": url,
        }
    except Exception as e:
        return {
            "status": "error",
            "task_id": None,
            "error": str(e),
        }


@app.function(image=image, secrets=[kie_secret, supabase_secret])
@modal.fastapi_endpoint(route="/", docs=True)
def home():
    """Health check endpoint"""
    return {
        "message": "Khepri AI Image Generation API",
        "status": "running",
        "version": "2.0.0",
        "endpoints": {
            "generate": "POST /generate - Generate images with Kie.ai",
            "docs": "GET /docs - API documentation"
        }
    }
