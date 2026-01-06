# Modal Autoscaling

Modal scale automatiquement les containers en fonction du trafic. C'est un des avantages majeurs de la plateforme.

## Configuration actuelle

```python
@app.function(
    max_containers=10,        # Maximum 10 containers en parallèle
    min_containers=0,         # Scale to zero quand inactif (pas de coûts)
    buffer_containers=1,      # 1 container buffer pour éviter cold starts
    timeout=180,              # 3 minutes max par requête
)
```

## Comment ça fonctionne

### Autoscaling automatique

Modal surveille continuellement le nombre de requêtes et ajuste les containers :

1. **Trafic faible** → 0-1 container (coût minimal)
2. **Trafic moyen** → 2-5 containers
3. **Pic de trafic** → jusqu'à 10 containers

### Exemple concret

```
Minute 0: 0 requête  → 0 container (pas de coût)
Minute 1: 1 requête  → 1 container se lance (cold start ~3-5s)
Minute 2: 5 requêtes → 5 containers actifs
Minute 3: 20 requêtes → 10 containers (max atteint)
Minute 4: 2 requêtes  → containers se réduisent progressivement
Minute 5: 0 requête  → scale to zero après quelques minutes
```

## Paramètres de scaling

### max_containers
- **Valeur actuelle** : 10
- **Par défaut Modal** : Illimité
- **Usage** : Limite les coûts et évite de surcharger l'API Kie.ai

**Augmenter si** :
- Tu as beaucoup de requêtes simultanées (>10)
- Tu vois des requêtes en attente (queued)

```python
max_containers=50  # Pour gros volume
```

### min_containers
- **Valeur actuelle** : 0 (scale to zero)
- **Par défaut Modal** : 0
- **Usage** : Garde des containers warm pour éviter cold starts

**Augmenter si** :
- Tu veux éviter complètement les cold starts
- Tu as du trafic constant

```python
min_containers=2  # 2 containers toujours actifs (coûte plus cher)
```

### buffer_containers
- **Valeur actuelle** : 1
- **Par défaut Modal** : 0
- **Usage** : Garde des containers prêts quand l'app est active

Quand il y a du trafic, Modal garde 1 container supplémentaire prêt à recevoir des requêtes instantanément.

## Monitoring

### Via Modal Dashboard
```
https://modal.com/apps
```

Tu peux voir :
- Nombre de containers actifs
- Temps de réponse
- Requêtes en queue
- Coûts en temps réel

### Limites de concurrence

Modal impose des limites par défaut :
- **200 requêtes/seconde** pour les nouveaux comptes
- Burst de 5x (1000 requêtes/seconde en pic)

Si tu dépasses, tu peux demander une augmentation à Modal.

## Cold Starts

**Cold start** = Temps pour lancer un nouveau container (~3-10s)

### Stratégies pour les réduire :

1. **buffer_containers=1** (déjà actif)
2. **min_containers=1** pour garder toujours 1 container warm
3. **Optimiser l'image Docker** (dépendances légères)

## Coûts

Modal facture à la seconde :
- **CPU** : $0.000059/seconde/container
- **Mémoire** : Basé sur l'usage
- **Pas de coût quand scale to zero** ✅

**Estimation** :
- 1 génération (50s) ≈ $0.003
- 100 générations/jour ≈ $0.30
- 10,000 générations/mois ≈ $30

## Scaling avancé

### Concurrency par container

Si tu veux traiter plusieurs requêtes par container (pour du I/O-bound) :

```python
@modal.concurrent(max_inputs=5)  # 5 requêtes par container
@app.function(max_containers=10)
def generate(...):
    ...
```

Attention : Kie.ai prend 40-50s par génération, donc concurrency n'est pas utile ici.

### Scaling dynamique

Tu peux ajuster les paramètres sans redéployer :

```python
from modal import Function

f = Function.from_name("kepri-kie-image-gen", "generate")
f.update_autoscaler(max_containers=50)  # Augmente la limite temporairement
```

## Références

- [Modal Scaling Guide](https://modal.com/docs/guide/scale)
- [Modal Concurrency](https://modal.com/docs/guide/concurrent-inputs)
- [Cold Start Performance](https://modal.com/docs/guide/cold-start)
