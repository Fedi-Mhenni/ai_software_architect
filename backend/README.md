# Backend

Petit backend FastAPI minimal pour exposer le point d'entrée de l'orchestrateur.

## Endpoints

- `GET /health` pour vérifier que le service répond
- `POST /analyze-project` pour recevoir une idée projet et démarrer l'analyse

## Fonctionnement actuel

Le backend valide l'entrée avec Pydantic et renvoie une réponse structurée temporaire:

```json
{
  "status": "analysis_started"
}
```

La vraie logique d'orchestration sera ajoutée ensuite par étapes.

Installation & exécution:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python run.py
```

Tester l'endpoint:

```bash
curl -s -X POST -H "Content-Type: application/json" \
  -d '{"idea":"Je veux créer un SaaS IA."}' \
  http://localhost:5001/analyze-project
```

Réponse temporaire:

```json
{
  "status": "analysis_started"
}
```

Health check:

```bash
curl -s http://localhost:5001/health
```

Si vous voulez changer le port sans taper d'options, modifiez seulement `APP_PORT` avant le lancement:

```bash
APP_PORT=5001 python run.py
```

Docs interactives FastAPI:

- `http://localhost:5001/docs`
- `http://localhost:5001/openapi.json`

But: cette réponse est volontairement factice pour démarrer le pipeline d'architecture et de workflow (architecture, stabilité, pipeline, etc.).
