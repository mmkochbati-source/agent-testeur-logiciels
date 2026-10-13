# 🧪 Agent IA Testeur de Logiciels

Agent IA **conversationnel** spécialisé dans les **tests fonctionnels** de logiciels : sites et applications web, APIs REST et code source. Il joue le rôle d'un expert QA (Assurance Qualité) : il vous aide à concevoir des cas de test, à les exécuter et à produire des rapports clairs au format **PASS/FAIL**.

## 🔗 Accès au chatbot

👉 **[Ouvrir l'agent sur Abacus.AI ChatLLM](https://apps.abacus.ai/chatllm/?appId=5b4213162)**

`https://apps.abacus.ai/chatllm/?appId=5b4213162`

## ⚙️ Capacités

| Capacité | Description |
|---|---|
| **Tests fonctionnels** | Vérifie que chaque fonctionnalité se comporte conformément aux exigences. |
| **Navigation web** | Parcourt un site, teste les formulaires, les liens et les parcours utilisateur. |
| **Appels API** | Envoie des requêtes HTTP (GET, POST, PUT, DELETE) et valide les codes de statut et la structure JSON des réponses. |
| **Analyse de code** | Relit le code source, repère les anomalies probables et propose des tests unitaires. |
| **Rapports PASS/FAIL** | Génère des rapports de test structurés (ID, description, données, résultat attendu/obtenu, statut, observations). |

## 🧩 Types de tests couverts

- **Fonctionnel** *(priorité principale)* : conformité des fonctionnalités aux spécifications.
- **Régression** : vérifie qu'une modification n'a pas cassé l'existant.
- **Intégration** : valide les échanges entre modules, services et APIs.
- **Performance** : temps de réponse et comportement de base sous charge (indicatif).
- **Sécurité** : contrôles de base (validation des entrées, authentification, exposition de données).

## 💬 Comment utiliser l'agent

Ouvrez le chatbot et décrivez ce que vous souhaitez tester. Exemples de prompts :

```text
Teste le formulaire de connexion de https://exemple.com : identifiants valides,
mot de passe incorrect et champs vides. Donne-moi un rapport PASS/FAIL.
```

```text
Voici mon API : https://api.exemple.com. Vérifie GET /users et POST /login,
contrôle les codes HTTP et la structure JSON des réponses.
```

```text
Analyse ce code Python et propose des cas de test fonctionnels et des tests unitaires :
<collez votre code ici>
```

```text
Vérifie s'il y a des liens brisés sur la page d'accueil de https://exemple.com.
```

```text
Rédige un plan de tests fonctionnels pour une page d'inscription
(nom, e-mail, mot de passe, confirmation).
```

**Conseils :**
- Fournissez l'URL, l'endpoint ou le code concerné.
- Précisez les exigences ou le comportement attendu.
- Indiquez les données de test à utiliser (n'utilisez jamais de vrais identifiants de production).

## 📁 Contenu du dépôt

```
.
├── README.md                          # Cette documentation
├── agent-config.json                  # Configuration de l'agent
└── examples/
    ├── cas-de-test-web.md             # Exemples de cas de test pour un site web
    ├── cas-de-test-api.md             # Exemples de cas de test pour une API REST
    └── rapport-test-template.md       # Modèle de rapport de test
```

## 🛠️ Stack

- **Plateforme :** [Abacus.AI ChatLLM](https://apps.abacus.ai/chatllm/)
- **Langue :** Français
- **Rôle :** Expert QA / Assurance Qualité logicielle
