# Déploiement sur Railway et Vercel

```
┌──────────────────────┐   fetch()   ┌──────────────────────────┐
│  web/  →  Vercel     │ ──────────▶ │  server/  →  Railway     │
│  Interface (HTML/JS) │             │  API FastAPI (tests)     │
└──────────────────────┘             └──────────────────────────┘
                                                  │ SDK abacusai (ABACUS_API_KEY)
                                                  ▼
                                   Agent Abacus.AI (déploiement 46d530766)
```

## 1. Backend sur Railway (`server/`)

1. Allez sur [railway.com/new](https://railway.com/new) → **Deploy from GitHub repo**.
2. Sélectionnez `mmkochbati-source/agent-testeur-logiciels`.
3. Dans **Settings → Source → Root Directory**, indiquez `server`.
4. Railway détecte Python et utilise `railway.json` (démarrage : `uvicorn main:app --host 0.0.0.0 --port $PORT`, healthcheck `/health`).
5. **Settings → Networking → Generate Domain** pour obtenir l'URL publique
   (ex. `https://agent-testeur-production.up.railway.app`).
6. Vérifiez : `https://<votre-domaine>/health` doit renvoyer `{"status":"ok"}` ; la doc interactive est sur `/docs`.

Variables d'environnement (optionnelles) :

| Variable | Défaut | Rôle |
|---|---|---|
| `ABACUS_API_KEY` | — | **Requis** pour `/api/chat` et `/api/analyse` : clé API Abacus.AI (à créer sur [abacus.ai/app/profile/apikey](https://abacus.ai/app/profile/apikey)) |
| `ABACUS_DEPLOYMENT_ID` | `46d530766` | Déploiement de l'agent Abacus.AI appelé par le backend |
| `ALLOWED_ORIGINS` | `*` | Domaines autorisés (CORS), ex. `https://agent-testeur.vercel.app` |
| `REQUEST_TIMEOUT` | `15` | Délai max (s) des requêtes de test |

## 2. Interface sur Vercel (`web/`)

1. Dans `web/config.js`, remplacez `BACKEND_URL` par l'URL Railway obtenue ci-dessus, puis commitez.
2. Allez sur [vercel.com/new](https://vercel.com/new) → importez le dépôt.
3. **Root Directory** : `web` — **Framework Preset** : `Other` — aucune commande de build.
4. Cliquez sur **Deploy**.
5. (Recommandé) Dans Railway, définissez `ALLOWED_ORIGINS` sur l'URL Vercel.

Chaque `git push` sur `main` redéploie automatiquement les deux services.

## 3. Test en local

```bash
cd server && pip install -r requirements.txt && uvicorn main:app --port 8000
cd web && python3 -m http.server 3000   # puis http://localhost:3000
```

## API

| Méthode | Route | Description |
|---|---|---|
| GET | `/health` | État du service (`abacus_configure` indique si la clé Abacus est présente) |
| POST | `/api/chat` | `{ "messages": [{ "is_user": true, "text": "..." }] }` → `{ "reponse": "..." }` (agent Abacus.AI) |
| POST | `/api/analyse` | `{ "web": {...} }` et/ou `{ "api": {...} }` → exécute les tests puis renvoie `rapports` + `analyse_ia` rédigée par l'agent |
| POST | `/api/test/web` | `{ "url": "...", "max_links": 20 }` → 8 cas (accessibilité HTTP, temps, HTTPS, titre, h1, alt des images, lang, liens brisés) |
| POST | `/api/test/api` | `{ "url", "method", "headers", "body", "expected_status", "expected_keys" }` → statut, temps, JSON, champs attendus |

Chaque réponse contient `cas` (ID, description, attendu, obtenu, PASS/FAIL) et `resume` (total, pass, fail, taux).
