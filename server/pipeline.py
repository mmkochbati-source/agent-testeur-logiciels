"""Pipeline Abacus -> GitHub : extraction des fichiers d'une réponse de l'agent et création de PR.

Convention attendue dans la réponse de l'agent (l'une ou l'autre) :
    ```python server/exemple.py          <- chemin dans l'en-tête du bloc
    ```python
    # fichier: server/exemple.py         <- ou en commentaire sur la 1re ligne
"""
import re
import time
from typing import Optional

import httpx

FENCE_RE = re.compile(r"```([^\n`]*)\n(.*?)```", re.S)
COMMENT_RE = re.compile(
    r"^\s*(?:#|//|--|/\*|<!--)\s*(?:fichier|file|chemin|path)\s*:\s*([^\s*>]+)", re.I)
SPECIAL_NAMES = {"Dockerfile", "Procfile", "Makefile"}
# Chemins interdits : workflows CI (accès aux secrets), git, fichiers d'environnement.
FORBIDDEN_PREFIXES = (".github/", ".git/")
FORBIDDEN_NAMES = (".env",)

DEV_INSTRUCTION = (
    "[Mode développeur] Si tu fournis du code destiné au dépôt, donne chaque fichier COMPLET "
    "dans un bloc de code séparé et indique son chemin relatif dans l'en-tête du bloc, "
    "par exemple ```python server/exemple.py. N'utilise pas de chemins sous .github/."
)


def _looks_like_path(token: str) -> bool:
    token = token.split("=", 1)[-1]  # accepte path=... / fichier=...
    return token in SPECIAL_NAMES or bool(re.fullmatch(r"[\w.\-]+(/[\w.\-]+)*\.\w+", token)) \
        or bool(re.fullmatch(r"[\w.\-]+(/[\w.\-]+)+", token))


def safe_path(path: str) -> Optional[str]:
    """Normalise un chemin et renvoie None s'il est dangereux ou invalide."""
    path = path.strip().strip("`'\"").removeprefix("./")
    if not path or path.startswith("/") or "\\" in path:
        return None
    parts = path.split("/")
    if any(p in ("", ".", "..") for p in parts):
        return None
    if path.startswith(FORBIDDEN_PREFIXES) or parts[-1].startswith(FORBIDDEN_NAMES):
        return None
    return path


def extract_files(text: str) -> tuple[dict[str, str], list[str]]:
    """Renvoie ({chemin: contenu}, [chemins refusés])."""
    files: dict[str, str] = {}
    rejected: list[str] = []
    for info, body in FENCE_RE.findall(text or ""):
        candidate = None
        for token in info.split():
            if _looks_like_path(token):
                candidate = token.split("=", 1)[-1]
                break
        if candidate is None:
            first, _, rest = body.partition("\n")
            m = COMMENT_RE.match(first)
            if not m:
                continue  # bloc sans chemin : simple exemple, ignoré
            candidate, body = m.group(1), rest
        path = safe_path(candidate)
        if path is None:
            rejected.append(candidate)
            continue
        files[path] = body if body.endswith("\n") else body + "\n"
    return files, rejected


def _slug(text: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")[:40] or "modification"


def create_pull_request(token: str, repo: str, files: dict[str, str], title: str,
                        description: str = "") -> dict:
    """Crée une branche, un commit contenant `files`, puis une PR vers la branche par défaut."""
    api = f"https://api.github.com/repos/{repo}"
    headers = {"Authorization": f"Bearer {token}", "Accept": "application/vnd.github+json",
               "X-GitHub-Api-Version": "2022-11-28"}
    with httpx.Client(headers=headers, timeout=30) as gh:
        def call(method: str, url: str, **kw) -> dict:
            r = gh.request(method, url, **kw)
            if r.status_code >= 400:
                raise RuntimeError(f"GitHub {method} {url.removeprefix(api)} -> "
                                   f"{r.status_code} : {r.text[:300]}")
            return r.json()

        base = call("GET", api)["default_branch"]
        base_sha = call("GET", f"{api}/git/ref/heads/{base}")["object"]["sha"]
        base_tree = call("GET", f"{api}/git/commits/{base_sha}")["tree"]["sha"]
        tree = call("POST", f"{api}/git/trees", json={
            "base_tree": base_tree,
            "tree": [{"path": p, "mode": "100644", "type": "blob", "content": c}
                     for p, c in files.items()],
        })["sha"]
        commit = call("POST", f"{api}/git/commits", json={
            "message": f"{title}\n\nCode généré par l'agent Abacus.AI.",
            "tree": tree, "parents": [base_sha]})["sha"]
        branch = f"abacus/{_slug(title)}-{int(time.time())}"
        call("POST", f"{api}/git/refs", json={"ref": f"refs/heads/{branch}", "sha": commit})
        body = (
            "## 🤖 PR générée automatiquement depuis l'agent Abacus.AI\n\n"
            + (f"{description}\n\n" if description else "")
            + "### Fichiers\n" + "\n".join(f"- `{p}`" for p in files)
            + "\n\n### Étapes automatiques\n"
              "- [ ] CI GitHub Actions (tests backend + frontend)\n"
              "- [ ] Prévisualisation Vercel (lien ajouté par Vercel sur cette PR)\n"
              "- [ ] Après fusion : synchronisation des variables Railway/Vercel et vérification "
              "du déploiement (workflow « Déploiement »)\n\n"
              "⚠️ Relisez le code avant de fusionner : il n'est jamais fusionné automatiquement."
        )
        pr = call("POST", f"{api}/pulls", json={"title": title, "head": branch, "base": base,
                                                 "body": body})
    return {"numero": pr["number"], "url": pr["html_url"], "branche": branch, "base": base,
            "fichiers": list(files)}
