# Exemples de cas de test fonctionnels — Site web

Ces exemples illustrent les cas de test que l'agent peut concevoir et exécuter sur un site web.

## 1. Formulaire de connexion

| ID | Description | Données de test | Résultat attendu |
|---|---|---|---|
| WEB-LOG-01 | Connexion avec identifiants valides | e-mail : `test@exemple.com` / mdp : `MotDePasse123!` | Redirection vers le tableau de bord, message de bienvenue |
| WEB-LOG-02 | Mot de passe incorrect | e-mail valide / mdp : `mauvais` | Message « Identifiants invalides », aucune redirection |
| WEB-LOG-03 | E-mail inexistant | `inconnu@exemple.com` / mdp quelconque | Message d'erreur générique (ne révèle pas si le compte existe) |
| WEB-LOG-04 | Champs vides | e-mail et mdp vides | Messages « Champ obligatoire » sur les deux champs |
| WEB-LOG-05 | Mot de passe masqué | Saisie d'un mdp | Caractères masqués (`type="password"`) |
| WEB-LOG-06 | Lien « Mot de passe oublié » | Clic sur le lien | Ouverture de la page de réinitialisation |
| WEB-LOG-07 | Déconnexion | Clic sur « Se déconnecter » | Retour à la page de connexion, session invalidée |

## 2. Navigation

| ID | Description | Données de test | Résultat attendu |
|---|---|---|---|
| WEB-NAV-01 | Menu principal | Clic sur chaque entrée du menu | Chaque page correspondante s'affiche (HTTP 200) |
| WEB-NAV-02 | Logo | Clic sur le logo depuis une page interne | Retour à la page d'accueil |
| WEB-NAV-03 | Fil d'Ariane | Navigation vers une page de niveau 3 | Fil d'Ariane correct et cliquable |
| WEB-NAV-04 | Bouton « Retour » du navigateur | Retour arrière après navigation | Page précédente affichée sans erreur |
| WEB-NAV-05 | Page inexistante | URL `/page-qui-n-existe-pas` | Page 404 personnalisée avec lien vers l'accueil |
| WEB-NAV-06 | Affichage mobile | Largeur d'écran 375 px | Menu « burger » fonctionnel, contenu lisible |

## 3. Liens brisés

| ID | Description | Données de test | Résultat attendu |
|---|---|---|---|
| WEB-LNK-01 | Liens internes de la page d'accueil | Tous les `<a href>` internes | Tous répondent avec un code HTTP 2xx ou 3xx |
| WEB-LNK-02 | Liens externes | Tous les liens sortants | Aucun code 4xx/5xx ; ouverture dans un nouvel onglet si prévu |
| WEB-LNK-03 | Images | Toutes les balises `<img>` | Toutes les images se chargent (pas de 404) |
| WEB-LNK-04 | Liens du pied de page | Mentions légales, contact, CGU | Pages accessibles et à jour |
| WEB-LNK-05 | Ancres | Liens `#section` | Défilement vers la bonne section |

## 4. Validation de champs (formulaire d'inscription)

| ID | Description | Données de test | Résultat attendu |
|---|---|---|---|
| WEB-VAL-01 | Format d'e-mail invalide | `utilisateur@` | Message « Adresse e-mail invalide » |
| WEB-VAL-02 | Mot de passe trop court | `abc` | Message « 8 caractères minimum » |
| WEB-VAL-03 | Confirmation différente | mdp `Test1234!` / confirmation `Test1235!` | Message « Les mots de passe ne correspondent pas » |
| WEB-VAL-04 | Longueur maximale | Nom de 256 caractères | Saisie limitée ou message d'erreur explicite |
| WEB-VAL-05 | Caractères spéciaux | Nom : `Éloïse O'Brien-Müller` | Valeur acceptée et correctement affichée |
| WEB-VAL-06 | Injection de script | `<script>alert(1)</script>` | Valeur échappée, aucun script exécuté |
| WEB-VAL-07 | Champ numérique | Téléphone : `abcd` | Message « Numéro invalide » |
| WEB-VAL-08 | E-mail déjà utilisé | E-mail d'un compte existant | Message « Cette adresse est déjà utilisée » |

## Prompt d'exemple

```text
Exécute les cas WEB-LOG-01 à WEB-LOG-04 sur https://exemple.com/login
et produis un rapport PASS/FAIL selon le modèle rapport-test-template.md.
```
