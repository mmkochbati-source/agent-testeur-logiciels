# Rapport de test — [Nom du projet / de la fonctionnalité]

## Informations générales

| Champ | Valeur |
|---|---|
| **Projet / Application** | |
| **Version testée** | |
| **Environnement** | (ex. : recette, préproduction, URL) |
| **Type de test** | Fonctionnel / Régression / Intégration / Performance / Sécurité |
| **Date d'exécution** | AAAA-MM-JJ |
| **Testeur** | Agent IA Testeur de Logiciels |

## Résultats détaillés

| ID | Description | Données de test | Résultat attendu | Résultat obtenu | Statut (PASS/FAIL) | Observations |
|---|---|---|---|---|---|---|
| TC-01 | | | | | | |
| TC-02 | | | | | | |
| TC-03 | | | | | | |

### Exemple rempli

| ID | Description | Données de test | Résultat attendu | Résultat obtenu | Statut (PASS/FAIL) | Observations |
|---|---|---|---|---|---|---|
| WEB-LOG-01 | Connexion avec identifiants valides | `test@exemple.com` / `MotDePasse123!` | Redirection vers le tableau de bord | Redirection vers le tableau de bord | ✅ PASS | — |
| WEB-LOG-02 | Mot de passe incorrect | `test@exemple.com` / `faux` | Message « Identifiants invalides » | Message affiché | ✅ PASS | — |
| WEB-LOG-04 | Champs vides | (vide) | Messages « Champ obligatoire » | Aucun message, le bouton ne réagit pas | ❌ FAIL | Validation côté client absente |
| API-USR-04 | Utilisateur inexistant | `GET /users/999999` | 404 Not Found | 500 Internal Server Error | ❌ FAIL | Exception non gérée côté serveur |

## Synthèse

| Indicateur | Valeur |
|---|---|
| Cas exécutés | |
| ✅ PASS | |
| ❌ FAIL | |
| ⏭️ Non exécutés / bloqués | |
| Taux de réussite | % |

## Anomalies détectées

| N° | ID du cas | Gravité (Bloquante / Majeure / Mineure) | Description | Étapes de reproduction |
|---|---|---|---|---|
| 1 | | | | |

## Recommandations

- 
- 

## Conclusion

> Verdict global : **Validé** / **Validé avec réserves** / **Non validé**
