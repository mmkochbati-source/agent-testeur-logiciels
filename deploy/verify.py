#!/usr/bin/env python3
"""Vérification post-déploiement (tests fonctionnels de fumée sur la production).

1. Attend que Railway serve le bon commit (/health -> version == EXPECTED_SHA), délai max WAIT_SECONDS.
2. Vérifie /health, un test web réel, le frontend Vercel (HTTP 200 + config.js -> backend) et le CORS.
Variables : EXPECTED_SHA (optionnel), WAIT_SECONDS (défaut 600). Code retour 1 si un contrôle échoue.
"""
import json
import os
import sys
import time
from pathlib import Path

import httpx

cfg = json.loads(Path(__file__).with_name("config.json").read_text(encoding="utf-8"))["verification"]
BACKEND, FRONTEND = cfg["backend_url"].rstrip("/"), cfg["frontend_url"].rstrip("/")
results: list[tuple[str, bool, str]] = []


def check(name: str, ok: bool, detail: str = "") -> None:
    results.append((name, ok, detail))
    print(f"  {'PASS' if ok else 'FAIL'}  {name}  {detail}", flush=True)


def wait_for_version(client: httpx.Client) -> dict:
    expected = os.environ.get("EXPECTED_SHA", "")
    deadline = time.time() + int(os.environ.get("WAIT_SECONDS", "600"))
    health: dict = {}
    while True:
        try:
            health = client.get(f"{BACKEND}/health").json()
        except Exception as e:  # service en cours de redémarrage
            health = {"erreur": str(e)}
        if not expected or health.get("version") == expected or time.time() > deadline:
            break
        print(f"  … version servie {str(health.get('version'))[:7]}, attendue {expected[:7]}", flush=True)
        time.sleep(20)
    if expected:
        check("Railway sert le commit fusionné", health.get("version") == expected,
              f"{str(health.get('version'))[:7]} / {expected[:7]}")
    return health


def main() -> int:
    with httpx.Client(timeout=60, follow_redirects=True) as c:
        health = wait_for_version(c)
        check("Backend /health", health.get("status") == "ok", json.dumps(health))
        check("Clé Abacus configurée", bool(health.get("abacus_configure")))
        r = c.post(f"{BACKEND}/api/test/web", json={"url": "https://example.com", "max_links": 3})
        ok = r.status_code == 200 and r.json().get("resume", r.json().get("summary", {})) is not None
        check("Test web fonctionnel (example.com)", ok, f"HTTP {r.status_code}")
        r = c.get(FRONTEND)
        check("Frontend Vercel HTTP 200", r.status_code == 200, f"HTTP {r.status_code}")
        r = c.get(f"{FRONTEND}/config.js")
        check("config.js pointe vers Railway", BACKEND in r.text)
        r = c.options(f"{BACKEND}/api/chat", headers={"Origin": FRONTEND,
                                                       "Access-Control-Request-Method": "POST"})
        check("CORS autorise Vercel", r.headers.get("access-control-allow-origin") == FRONTEND)
    failed = [n for n, ok, _ in results if not ok]
    print(f"\n{len(results) - len(failed)}/{len(results)} contrôles OK", flush=True)
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
