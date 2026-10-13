# Exemples de cas de test fonctionnels — API REST

Ces exemples illustrent les cas de test que l'agent peut concevoir et exécuter sur une API REST.
URL de base fictive : `https://api.exemple.com`

## 1. GET /users

| ID | Description | Requête | Résultat attendu |
|---|---|---|---|
| API-USR-01 | Liste des utilisateurs (authentifié) | `GET /users` + `Authorization: Bearer <token>` | **200 OK**, tableau JSON d'utilisateurs |
| API-USR-02 | Sans authentification | `GET /users` sans en-tête | **401 Unauthorized** |
| API-USR-03 | Utilisateur existant | `GET /users/1` | **200 OK**, objet utilisateur avec `id = 1` |
| API-USR-04 | Utilisateur inexistant | `GET /users/999999` | **404 Not Found** |
| API-USR-05 | Identifiant invalide | `GET /users/abc` | **400 Bad Request** |
| API-USR-06 | Pagination | `GET /users?page=2&limit=10` | **200 OK**, 10 éléments max, métadonnées de pagination |
| API-USR-07 | Temps de réponse | `GET /users` | Réponse en moins de 1 seconde (indicatif) |

**Structure JSON attendue (`GET /users/1`) :**

```json
{
  "id": 1,
  "nom": "Dupont",
  "prenom": "Marie",
  "email": "marie.dupont@exemple.com",
  "role": "utilisateur",
  "date_creation": "2026-01-15T09:30:00Z"
}
```

Vérifications :
- `Content-Type: application/json`
- Champs obligatoires présents : `id`, `nom`, `prenom`, `email`
- Types : `id` entier, `email` chaîne au format e-mail, `date_creation` au format ISO 8601
- Aucune donnée sensible exposée (ex. : `mot_de_passe`, `hash`)

## 2. POST /login

| ID | Description | Corps de la requête | Résultat attendu |
|---|---|---|---|
| API-LOG-01 | Identifiants valides | `{"email": "test@exemple.com", "password": "MotDePasse123!"}` | **200 OK**, jeton retourné |
| API-LOG-02 | Mot de passe incorrect | `{"email": "test@exemple.com", "password": "faux"}` | **401 Unauthorized**, message d'erreur |
| API-LOG-03 | Champ manquant | `{"email": "test@exemple.com"}` | **400 Bad Request** (ou 422), champ manquant indiqué |
| API-LOG-04 | Corps vide | `{}` | **400 Bad Request** |
| API-LOG-05 | JSON mal formé | `{"email": ` | **400 Bad Request** |
| API-LOG-06 | Mauvaise méthode | `GET /login` | **405 Method Not Allowed** |
| API-LOG-07 | Tentatives répétées | 10 échecs consécutifs | **429 Too Many Requests** ou blocage temporaire |

**Structure JSON attendue (succès) :**

```json
{
  "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "type": "Bearer",
  "expire_dans": 3600,
  "utilisateur": {
    "id": 1,
    "email": "test@exemple.com"
  }
}
```

**Structure JSON attendue (erreur) :**

```json
{
  "erreur": "identifiants_invalides",
  "message": "E-mail ou mot de passe incorrect."
}
```

## 3. Codes HTTP de référence

| Code | Signification | Cas typique |
|---|---|---|
| 200 | OK | Lecture ou action réussie |
| 201 | Created | Ressource créée (POST) |
| 204 | No Content | Suppression réussie |
| 400 | Bad Request | Données invalides ou mal formées |
| 401 | Unauthorized | Authentification absente ou invalide |
| 403 | Forbidden | Authentifié mais droits insuffisants |
| 404 | Not Found | Ressource inexistante |
| 405 | Method Not Allowed | Méthode HTTP non supportée |
| 409 | Conflict | Doublon (ex. : e-mail déjà utilisé) |
| 422 | Unprocessable Entity | Validation métier échouée |
| 429 | Too Many Requests | Limite de requêtes atteinte |
| 500 | Internal Server Error | Erreur côté serveur (toujours un FAIL) |

## Prompt d'exemple

```text
Teste POST /login sur https://api.exemple.com avec les cas API-LOG-01 à API-LOG-05,
vérifie les codes HTTP et la structure JSON, puis donne-moi un rapport PASS/FAIL.
```
