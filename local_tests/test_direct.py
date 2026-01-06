#!/usr/bin/env python3
"""Test direct sans input interactif"""
from test_kie import generate_image

prompt = "Use the dress from Image exactly as it is — same color, same fabric texture.Replace the mannequin with a beautiful woman.Do NOT change:– the color, shape, length, or design of the outfit– lighting direction, shadows on the fabric, or overall silhouetteKeep the background clean studio white, high-end e-commerce style.Output a photorealistic full-body image of the woman naturally wearing the dress from Image, with seamless blending and no artifacts."

image_paths = ["inputs/photo2.png"]
resolution = "2K"

print("=" * 60)
print("🎨 Kie.ai Nano Banana Pro - Test Phase 1 (Direct)")
print("=" * 60)
print(f"\n📝 Prompt: {prompt[:100]}...")
print(f"🖼️  Images: {image_paths}")
print(f"⚙️  Resolution: {resolution}")
print("=" * 60)

try:
    result_url = generate_image(prompt, image_paths, resolution=resolution)
    print(f"\n✅ Image générée: {result_url}\n")
except Exception as e:
    print(f"\n❌ Erreur: {e}\n")
    import traceback
    traceback.print_exc()
