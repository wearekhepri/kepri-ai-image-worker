import os
import sys
import time
import json
import uuid
import requests
from typing import Optional, List
from pathlib import Path
from dotenv import load_dotenv
from supabase import create_client, Client

load_dotenv()

KIE_API_KEY = os.getenv("KIE_API_KEY")
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_ANON_KEY")
BASE_URL = "https://api.kie.ai/api/v1"

# Init Supabase client
supabase: Client = None
if SUPABASE_URL and SUPABASE_KEY:
    supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

def upload_image(image_path: str) -> str:
    """
    Upload une image locale vers Supabase Storage et retourne l'URL publique.
    Nano Banana Pro nécessite des URLs publiques, pas de binaires.
    """
    # Validation de taille
    size_mb = Path(image_path).stat().st_size / (1024 * 1024)
    if size_mb > 30:
        raise ValueError(f"{Path(image_path).name} est trop grande ({size_mb:.1f}MB), max 30MB")
    
    if not supabase:
        raise ValueError(
            "Supabase non configuré. Ajoute dans .env:\n"
            "SUPABASE_URL=https://auth.wearekepri.com\n"
            "SUPABASE_ANON_KEY=ta_cle"
        )
    
    # Générer un nom de fichier unique
    import uuid
    file_ext = Path(image_path).suffix
    file_name = f"{uuid.uuid4()}{file_ext}"
    bucket_name = "ai-test-images"
    
    # Upload vers Supabase Storage
    with open(image_path, 'rb') as f:
        response = supabase.storage.from_(bucket_name).upload(
            file_name,
            f,
            file_options={"content-type": f"image/{file_ext[1:]}"}
        )
    
    # Obtenir l'URL publique
    public_url = supabase.storage.from_(bucket_name).get_public_url(file_name)
    
    print(f"  Upload {Path(image_path).name}: OK")
    print(f"    → {public_url}")
    return public_url

def generate_image(prompt: str, image_paths: List[str] = None, resolution: str = "1K") -> str:
    """
    Génère une image avec Nano Banana Pro
    
    Args:
        prompt: Le prompt de génération
        image_paths: Liste de 0 à 2 chemins d'images locales (max 8 selon doc, mais on limite à 2 pour les tests)
        resolution: 1K, 2K ou 4K
    
    Returns:
        URL de l'image générée
    """
    image_paths = image_paths or []
    
    # Validation
    if len(image_paths) > 2:
        raise ValueError("Maximum 2 images pour ce test (extensible à 8)")
    
    # Upload des images si nécessaire
    image_urls = []
    if image_paths:
        print(f"\n📤 Upload de {len(image_paths)} image(s)...")
        for path in image_paths:
            # Convertir en chemin absolu si relatif
            full_path = Path(path).resolve()
            if not full_path.exists():
                raise FileNotFoundError(f"Image non trouvée: {path} (résolu vers: {full_path})")
            url = upload_image(str(full_path))
            image_urls.append(url)
    
    # Création de la tâche
    print(f"\n🎨 Génération avec prompt: \"{prompt}\"")
    print(f"   Images input: {len(image_urls)}")
    print(f"   Resolution: {resolution}")
    
    payload = {
        "model": "nano-banana-pro",
        "input": {
            "prompt": prompt,
            "image_input": image_urls,
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
    r.raise_for_status()
    data = r.json()
    
    if data.get("code") != 200:
        raise RuntimeError(f"Kie error: {data}")
    
    task_id = data["data"]["taskId"]
    print(f"   Task ID: {task_id}")
    
    # Polling
    print(f"\n⏳ En attente de génération...")
    headers = {"Authorization": f"Bearer {KIE_API_KEY}"}
    start = time.time()
    timeout = 120  # 2 minutes
    
    while True:
        r = requests.get(f"{BASE_URL}/jobs/recordInfo", headers=headers,
                         params={"taskId": task_id}, timeout=30)
        r.raise_for_status()
        task_data = r.json()["data"]
        state = task_data["state"]
        
        if state == "success":
            # Extraction de l'URL
            raw = task_data.get("resultJson")
            if raw:
                obj = json.loads(raw)
                urls = obj.get("resultUrls") or obj.get("resulturls") or []
                if urls:
                    elapsed = time.time() - start
                    print(f"✅ Succès en {elapsed:.1f}s")
                    return urls[0]
            raise RuntimeError("No URL in resultJson")
        
        if state == "fail":
            raise RuntimeError(f"Generation failed: {task_data.get('failMsg')}")
        
        if time.time() - start > timeout:
            raise RuntimeError(f"Timeout après {timeout}s")
        
        print(f"   state: {state}")
        time.sleep(3)

def main():
    print("=" * 60)
    print("🎨 Kie.ai Nano Banana Pro - Test Phase 1")
    print("=" * 60)
    
    # Demander le prompt
    print("\n📝 Entrez votre prompt:")
    prompt = input("> ").strip()
    
    if not prompt:
        print("❌ Prompt vide, abandon")
        sys.exit(1)
    
    # Demander les images
    print("\n🖼️  Images à utiliser (0-2 images):")
    print("   Entrez les chemins séparés par des espaces (ou vide pour génération pure)")
    print("   Exemple: inputs/photo1.jpg inputs/photo2.jpg")
    image_input = input("> ").strip()
    
    image_paths = []
    if image_input:
        image_paths = image_input.split()
        if len(image_paths) > 2:
            print(f"⚠️  Maximum 2 images, seules les 2 premières seront utilisées")
            image_paths = image_paths[:2]
    
    # Résolution
    print("\n⚙️  Résolution (1K/2K/4K, défaut: 2K):")
    resolution_input = input("> ").strip().upper()
    resolution = resolution_input if resolution_input in ["1K", "2K", "4K"] else "2K"
    
    print("\n" + "=" * 60)
    
    try:
        result_url = generate_image(prompt, image_paths, resolution=resolution)
        print(f"\n🖼️  Image générée: {result_url}\n")
    except Exception as e:
        print(f"\n❌ Erreur: {e}\n")
        sys.exit(1)

if __name__ == "__main__":
    main()
