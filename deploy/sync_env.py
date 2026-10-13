#!/usr/bin/env python3
"""Synchronise la configuration (deploy/config.json + secrets GitHub) vers Railway et Vercel.

Appelé par le workflow GitHub Actions « Déploiement » après chaque fusion sur main.
Un fournisseur dont les identifiants sont absents est ignoré (avec un avertissement).

Variables d'environnement :
  Railway : RAILWAY_TOKEN, RAILWAY_PROJECT_ID, RAILWAY_ENVIRONMENT_ID, RAILWAY_SERVICE_ID
  Vercel  : VERCEL_TOKEN, VERCEL_PROJECT_ID, [VERCEL_TEAM_ID], [VERCEL_DEPLOY_HOOK]
  Secrets : ceux référencés dans config.json["railway_secrets"]
Options : --dry-run (n'envoie rien, affiche seulement les clés), --config CHEMIN
"""
import argparse
import json
import os
import sys
from pathlib import Path

import httpx

RAILWAY_API = "https://backboard.railway.com/graphql/v2"
VERCEL_API = "https://api.vercel.com"


def log(msg: str) -> None:
    print(msg, flush=True)


def load_config(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def clean(d: dict) -> dict:
    return {k: v for k, v in d.items() if not k.startswith("_")}


def railway_variables(cfg: dict) -> tuple[dict, list]:
    variables = {k: str(v) for k, v in clean(cfg.get("railway", {})).items()}
    missing = []
    for var, secret in clean(cfg.get("railway_secrets", {})).items():
        value = os.environ.get(secret)
        if value:
            variables[var] = value
        else:
            missing.append(secret)
    return variables, missing


def sync_railway(cfg: dict, dry_run: bool) -> bool:
    needed = ["RAILWAY_TOKEN", "RAILWAY_PROJECT_ID", "RAILWAY_ENVIRONMENT_ID", "RAILWAY_SERVICE_ID"]
    absent = [n for n in needed if not os.environ.get(n)]
    variables, missing = railway_variables(cfg)
    if missing:
        log(f"  [Railway] secrets non définis (non envoyés) : {', '.join(missing)}")
    log(f"  [Railway] variables : {', '.join(sorted(variables))}")
    if dry_run:
        return True
    if absent:
        log(f"  [Railway] IGNORÉ — identifiants manquants : {', '.join(absent)}")
        return True
    query = """mutation($input: VariableCollectionUpsertInput!) { variableCollectionUpsert(input: $input) }"""
    payload = {"query": query, "variables": {"input": {
        "projectId": os.environ["RAILWAY_PROJECT_ID"],
        "environmentId": os.environ["RAILWAY_ENVIRONMENT_ID"],
        "serviceId": os.environ["RAILWAY_SERVICE_ID"],
        "variables": variables,
    }}}
    r = httpx.post(RAILWAY_API, json=payload, timeout=30,
                   headers={"Authorization": f"Bearer {os.environ['RAILWAY_TOKEN']}"})
    data = r.json() if r.headers.get("content-type", "").startswith("application/json") else {}
    if r.status_code != 200 or data.get("errors"):
        log(f"  [Railway] ÉCHEC HTTP {r.status_code} : {data.get('errors') or r.text[:300]}")
        return False
    log("  [Railway] OK — variables mises à jour (redéploiement déclenché par Railway)")
    return True


def sync_vercel(cfg: dict, dry_run: bool) -> bool:
    variables = {k: str(v) for k, v in clean(cfg.get("vercel", {})).items()}
    log(f"  [Vercel] variables : {', '.join(sorted(variables))}")
    if dry_run:
        return True
    token, project = os.environ.get("VERCEL_TOKEN"), os.environ.get("VERCEL_PROJECT_ID")
    if not token or not project:
        log("  [Vercel] IGNORÉ — VERCEL_TOKEN / VERCEL_PROJECT_ID manquants")
        return True
    params = {"upsert": "true"}
    if os.environ.get("VERCEL_TEAM_ID"):
        params["teamId"] = os.environ["VERCEL_TEAM_ID"]
    headers = {"Authorization": f"Bearer {token}"}
    body = [{"key": k, "value": v, "type": "encrypted", "target": ["production", "preview"]}
            for k, v in variables.items()]
    r = httpx.post(f"{VERCEL_API}/v10/projects/{project}/env", params=params, json=body,
                   headers=headers, timeout=30)
    if r.status_code >= 300:
        log(f"  [Vercel] ÉCHEC variables HTTP {r.status_code} : {r.text[:300]}")
        return False
    log("  [Vercel] OK — variables mises à jour")

    hook = os.environ.get("VERCEL_DEPLOY_HOOK")
    if hook:
        r = httpx.post(hook, timeout=30)
        ok = r.status_code < 300
        log(f"  [Vercel] redéploiement via Deploy Hook : {'OK' if ok else 'ÉCHEC HTTP %s' % r.status_code}")
        return ok
    log("  [Vercel] pas de VERCEL_DEPLOY_HOOK : le déploiement Git automatique de Vercel s'en charge")
    return True


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--config", default=str(Path(__file__).with_name("config.json")))
    args = ap.parse_args()
    cfg = load_config(Path(args.config))
    log("Synchronisation Railway…")
    ok_r = sync_railway(cfg, args.dry_run)
    log("Synchronisation Vercel…")
    ok_v = sync_vercel(cfg, args.dry_run)
    return 0 if ok_r and ok_v else 1


if __name__ == "__main__":
    sys.exit(main())
