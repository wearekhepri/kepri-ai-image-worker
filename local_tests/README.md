# Tests Locaux Phase 1

Scripts de test pour valider l'API Kie.ai en local avant déploiement Modal.

## Configuration

Créer un fichier `.env` à la racine du projet :

```bash
KIE_API_KEY=ta_cle_kie
SUPABASE_URL=https://auth.wearekepri.com
SUPABASE_ANON_KEY=ta_cle_supabase
```

## Scripts disponibles

### test_direct.py (Recommandé)
Test direct sans interaction utilisateur.

```bash
cd /Users/barbaramileo/Projects/Kepri-kie-local-test
python3 local_tests/test_direct.py
```

### test_kie.py
Script interactif complet qui demande :
- Le prompt
- Les chemins d'images (0-2)
- La résolution (1K/2K/4K)

```bash
python3 local_tests/test_kie.py
```

### kie_client.py
Client basique pour test rapide sans images.

```bash
python3 local_tests/kie_client.py
```

## Résultats Phase 1

✅ Upload Supabase Storage fonctionnel
✅ Génération Kie.ai Nano Banana Pro validée
✅ Tests avec prompt complexe + images réussis
✅ Temps de génération : ~45-50s en 2K

## Passage à Phase 2

Une fois les tests locaux validés, passer à `app.py` pour déploiement Modal.
