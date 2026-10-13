import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fastapi.testclient import TestClient  # noqa: E402

import main  # noqa: E402
from pipeline import extract_files, safe_path  # noqa: E402

client = TestClient(main.app)

REPONSE_AGENT = """Voici le code :

```python server/outils.py
def addition(a, b):
    return a + b
```

```javascript
// fichier: web/extra.js
console.log("ok");
```

```bash
pip install x
```

```yaml .github/workflows/pirate.yml
on: push
```
"""


def test_extract_files_header_and_comment():
    files, rejected = extract_files(REPONSE_AGENT)
    assert set(files) == {"server/outils.py", "web/extra.js"}
    assert files["server/outils.py"].startswith("def addition")
    assert "fichier:" not in files["web/extra.js"]  # ligne de chemin retirée
    assert rejected == [".github/workflows/pirate.yml"]


def test_extract_files_without_path_is_ignored():
    assert extract_files("```python\nprint(1)\n```") == ({}, [])


def test_safe_path():
    assert safe_path("./server/a.py") == "server/a.py"
    for bad in ["/etc/passwd", "../x.py", "a/../b.py", ".github/x.yml", ".env", "server/.env.prod",
                "a\\b.py", ""]:
        assert safe_path(bad) is None, bad


def test_health():
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json()["status"] == "ok"


def test_pipeline_dry_run():
    r = client.post("/api/pipeline/pr", json={"texte": REPONSE_AGENT, "dry_run": True})
    assert r.status_code == 200
    assert set(r.json()["fichiers"]) == {"server/outils.py", "web/extra.js"}


def test_pipeline_no_files():
    r = client.post("/api/pipeline/pr", json={"texte": "pas de code", "dry_run": True})
    assert r.status_code == 400


def test_pipeline_requires_configuration(monkeypatch):
    monkeypatch.delenv("GITHUB_TOKEN", raising=False)
    monkeypatch.delenv("PIPELINE_SECRET", raising=False)
    r = client.post("/api/pipeline/pr", json={"texte": REPONSE_AGENT})
    assert r.status_code == 503


def test_pipeline_rejects_bad_secret(monkeypatch):
    monkeypatch.setenv("GITHUB_TOKEN", "x")
    monkeypatch.setenv("PIPELINE_SECRET", "bon-secret")
    r = client.post("/api/pipeline/pr", json={"texte": REPONSE_AGENT},
                    headers={"X-Pipeline-Secret": "mauvais"})
    assert r.status_code == 401


def test_invalid_url_rejected():
    r = client.post("/api/test/web", json={"url": "ftp://exemple.com"})
    assert r.status_code == 400
