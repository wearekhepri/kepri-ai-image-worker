# Khepri AI Image Generation Worker

Worker Modal pour génération d'images via Kie.ai Nano Banana Pro.

## Structure du Projet

```
khepri-kie-local-test/
├── app.py                 # Application Modal principale (FastAPI)
├── requirements.txt       # Dépendances Python
├── .env                   # Variables d'environnement (local only)
├── local_tests/           # Scripts de test Phase 1
├── inputs/                # Images de test
├── docs/                  # Documentation
└── README.md
```

## Phase 1: Tests Locaux (Complet ✅)

Les scripts de test locaux sont dans `local_tests/` :
- `test_direct.py` - Test direct sans interaction
- `test_kie.py` - Script interactif complet
- `kie_client.py` - Client basique Kie.ai

Voir `local_tests/README.md` pour les instructions.

## Phase 2: Déploiement Modal

### Prérequis

1. **Installer Modal CLI:**
```bash
pip install modal
modal setup
```

2. **Créer les secrets Modal:**

```bash
# Secret Kie.ai
modal secret create kie-api-key KIE_API_KEY=<ta_cle_kie>

# Secret Supabase
modal secret create supabase-credentials \
  SUPABASE_URL=https://auth.wearekepri.com \
  SUPABASE_ANON_KEY=<ta_cle_supabase>
```

### Développement avec modal serve

```bash
modal serve app.py
```

Modal va :
- Créer une image Docker avec les dépendances
- Lancer un serveur FastAPI dans le cloud
- Exposer 2 endpoints HTTP publics :
  - `GET /` - Health check
  - `POST /generate` - Génération d'images
- Afficher les URLs dev :
  ```
  https://wearekhepri--khepri-kie-image-gen-home-dev.modal.run
  https://wearekhepri--khepri-kie-image-gen-generate-dev.modal.run
  ```

### Test de l'API

**Health check:**
```bash
curl https://wearekhepri--khepri-kie-image-gen-home-dev.modal.run
```

**Génération d'image:**
```bash
curl -X POST "https://wearekhepri--khepri-kie-image-gen-generate-dev.modal.run" \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "studio shot of a mannequin wearing a red coat",
    "image_urls": [],
    "resolution": "2K"
  }'
```

**Avec image en input:**
```bash
curl -X POST "https://wearekhepri--khepri-kie-image-gen-generate-dev.modal.run" \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "replace mannequin with woman",
    "image_urls": ["https://auth.wearekepri.com/storage/v1/object/public/ai-test-images/xxx.png"],
    "resolution": "2K"
  }'
```

**Documentation Swagger:**
```
https://wearekhepri--khepri-kie-image-gen-generate-dev.modal.run/docs
```

### Déploiement en production

```bash
modal deploy app.py
```

Les URLs deviennent permanentes (sans `-dev`) :
```
https://wearekhepri--khepri-kie-image-gen-generate.modal.run
```

## Paramètres de l'API

### POST /generate

| Paramètre | Type | Défaut | Description |
|-----------|------|--------|-------------|
| `prompt` | string | **required** | Description texte pour la génération |
| `image_urls` | string[] | `[]` | URLs publiques d'images (0-8 max) |
| `aspect_ratio` | string | `"3:4"` | Ratio de l'image |
| `resolution` | string | `"2K"` | Résolution : `1K`, `2K`, `4K` |
| `output_format` | string | `"png"` | Format : `png`, `jpg` |

### Réponse

```json
{
  "status": "success",
  "task_id": "abc123...",
  "image_url": "https://tempfile.aiquickdraw.com/..."
}
```

## Phase 3: Intégration React Native

Voir `docs/integration-react-native.md`

## Phase 4: Système de Jobs

Voir `docs/job-queue.md`

## Documentation

- `docs/modal-guide.pdf` - Guide complet Modal
- Architecture Modal : `@app.function()` + `@modal.fastapi_endpoint()`
- Secrets gestion : Modal Dashboard

## Support

- Kie.ai API : https://docs.kie.ai/
- Modal Docs : https://modal.com/docs
- Supabase Storage : https://supabase.com/docs/guides/storage
