"""Backend d'exécution des tests fonctionnels — déployable sur Railway.

Endpoints :
  GET  /health           -> état du service
  POST /api/test/web     -> tests fonctionnels d'une page web (statut, titre, temps, liens)
  POST /api/test/api     -> test d'un endpoint d'API REST avec assertions
  POST /api/chat         -> discussion avec l'agent Abacus.AI
  POST /api/analyse      -> exécute les tests puis les fait analyser par l'agent Abacus.AI

Variables d'environnement : ABACUS_API_KEY (requis pour /api/chat et /api/analyse),
ABACUS_DEPLOYMENT_ID, ALLOWED_ORIGINS, REQUEST_TIMEOUT.
"""
import json
import os
import time
from typing import Any, Optional
from urllib.parse import urljoin, urlparse

import httpx
from bs4 import BeautifulSoup
from fastapi import FastAPI, HTTPException
from fastapi.concurrency import run_in_threadpool
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

AGENT_URL = "https://apps.abacus.ai/chatllm/?appId=5b4213162"
ABACUS_DEPLOYMENT_ID = os.getenv("ABACUS_DEPLOYMENT_ID", "46d530766")
TIMEOUT = float(os.getenv("REQUEST_TIMEOUT", "15"))
USER_AGENT = "AgentTesteurLogiciels/1.0"

app = FastAPI(title="Agent IA Testeur de Logiciels — API", version="1.0.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=[o.strip() for o in os.getenv("ALLOWED_ORIGINS", "*").split(",")],
    allow_methods=["*"],
    allow_headers=["*"],
)


def _check_url(url: str) -> None:
    if urlparse(url).scheme not in ("http", "https"):
        raise HTTPException(400, "L'URL doit commencer par http:// ou https://")


def _case(cid: str, desc: str, expected: str, actual: str, ok: bool) -> dict:
    return {"id": cid, "description": desc, "attendu": expected, "obtenu": actual,
            "statut": "PASS" if ok else "FAIL"}


def _summary(cases: list) -> dict:
    passed = sum(c["statut"] == "PASS" for c in cases)
    return {"total": len(cases), "pass": passed, "fail": len(cases) - passed,
            "taux_reussite": round(100 * passed / len(cases), 1) if cases else 0.0}


class WebTestRequest(BaseModel):
    url: str
    max_links: int = Field(20, ge=0, le=100)
    max_response_ms: int = Field(3000, ge=1)


class ApiTestRequest(BaseModel):
    url: str
    method: str = "GET"
    headers: dict[str, str] = {}
    body: Optional[Any] = None
    expected_status: int = 200
    expected_keys: list[str] = []
    max_response_ms: int = Field(3000, ge=1)


class ChatMessage(BaseModel):
    is_user: bool
    text: str


class ChatRequest(BaseModel):
    messages: list[ChatMessage] = Field(..., min_length=1)


class AnalyseRequest(BaseModel):
    web: Optional[WebTestRequest] = None
    api: Optional[ApiTestRequest] = None


def _ask_agent_sync(messages: list[dict]) -> str:
    """Appelle l'agent Abacus.AI (ChatLLM) via le SDK officiel."""
    if not os.getenv("ABACUS_API_KEY"):
        raise HTTPException(503, "ABACUS_API_KEY n'est pas configurée sur le serveur.")
    import abacusai  # import paresseux : le SDK est lourd

    client = abacusai.ApiClient(api_key=os.environ["ABACUS_API_KEY"])
    try:
        resp = client.get_chat_response(deployment_token=None,
                                        deployment_id=ABACUS_DEPLOYMENT_ID, messages=messages)
    except Exception as e:  # erreurs réseau / auth du SDK
        raise HTTPException(502, f"Erreur de l'agent Abacus.AI : {e}") from e
    replies = [m["text"] for m in resp.get("messages", []) if not m.get("is_user")]
    return replies[-1] if replies else ""


async def ask_agent(messages: list[dict]) -> str:
    return await run_in_threadpool(_ask_agent_sync, messages)


@app.get("/")
def root():
    return {"service": "Agent IA Testeur de Logiciels", "agent": AGENT_URL,
            "endpoints": ["/health", "/api/test/web", "/api/test/api",
                          "/api/chat", "/api/analyse", "/docs"]}


@app.get("/health")
def health():
    return {"status": "ok", "abacus_configure": bool(os.getenv("ABACUS_API_KEY"))}


@app.post("/api/chat")
async def chat(req: ChatRequest):
    """Discussion avec l'agent Abacus.AI (historique complet passé à chaque appel)."""
    reply = await ask_agent([m.model_dump() for m in req.messages])
    return {"reponse": reply}


@app.post("/api/analyse")
async def analyse(req: AnalyseRequest):
    """Exécute les tests puis demande à l'agent Abacus.AI d'analyser le rapport."""
    if not req.web and not req.api:
        raise HTTPException(400, "Fournissez « web » et/ou « api ».")
    rapports = {}
    if req.web:
        rapports["web"] = await test_web(req.web)
    if req.api:
        rapports["api"] = await test_api(req.api)
    prompt = (
        "Voici les résultats bruts de tests fonctionnels exécutés automatiquement "
        "(format JSON). Analyse-les : résume les résultats, explique chaque FAIL, "
        "évalue la gravité et donne des recommandations concrètes, puis propose "
        "des cas de test complémentaires.\n\n"
        + json.dumps(rapports, ensure_ascii=False, default=str)[:20000]
    )
    analyse_ia = await ask_agent([{"is_user": True, "text": prompt}])
    return {"rapports": rapports, "analyse_ia": analyse_ia}


@app.post("/api/test/web")
async def test_web(req: WebTestRequest):
    _check_url(req.url)
    cases = []
    async with httpx.AsyncClient(timeout=TIMEOUT, follow_redirects=True,
                                 headers={"User-Agent": USER_AGENT}) as client:
        t0 = time.perf_counter()
        try:
            r = await client.get(req.url)
        except httpx.HTTPError as e:
            cases.append(_case("WEB-01", "La page est accessible", "Réponse HTTP",
                               f"Erreur : {type(e).__name__}", False))
            return {"url": req.url, "cas": cases, "resume": _summary(cases)}
        ms = round((time.perf_counter() - t0) * 1000)

        cases.append(_case("WEB-01", "La page est accessible", "HTTP 2xx",
                           f"HTTP {r.status_code}", r.is_success))
        cases.append(_case("WEB-02", "Temps de réponse acceptable",
                           f"< {req.max_response_ms} ms", f"{ms} ms", ms < req.max_response_ms))
        cases.append(_case("WEB-03", "Connexion sécurisée (HTTPS)", "https",
                           r.url.scheme, r.url.scheme == "https"))

        soup = BeautifulSoup(r.text, "html.parser")
        title = (soup.title.string or "").strip() if soup.title else ""
        cases.append(_case("WEB-04", "La page possède un titre", "<title> non vide",
                           title or "(absent)", bool(title)))
        h1 = soup.find("h1")
        cases.append(_case("WEB-05", "La page possède un titre principal", "<h1> présent",
                           "présent" if h1 else "absent", h1 is not None))
        imgs = soup.find_all("img")
        no_alt = [i for i in imgs if not i.get("alt")]
        cases.append(_case("WEB-06", "Images avec texte alternatif (accessibilité)",
                           "0 image sans alt", f"{len(no_alt)}/{len(imgs)} sans alt", not no_alt))
        lang = soup.html.get("lang") if soup.html else None
        cases.append(_case("WEB-07", "Langue du document déclarée", "attribut lang",
                           lang or "(absent)", bool(lang)))

        links = []
        for a in soup.find_all("a", href=True):
            href = urljoin(str(r.url), a["href"])
            if urlparse(href).scheme in ("http", "https") and href not in links:
                links.append(href.split("#")[0])
        broken = []
        for link in links[: req.max_links]:
            try:
                lr = await client.head(link)
                if lr.status_code in (403, 405):
                    lr = await client.get(link)
                if lr.status_code >= 400:
                    broken.append({"url": link, "statut": lr.status_code})
            except httpx.HTTPError as e:
                broken.append({"url": link, "statut": type(e).__name__})
        checked = min(len(links), req.max_links)
        cases.append(_case("WEB-08", "Aucun lien brisé", "0 lien en erreur",
                           f"{len(broken)} en erreur sur {checked} vérifiés", not broken))

    return {"url": req.url, "cas": cases, "liens_brises": broken, "resume": _summary(cases)}


@app.post("/api/test/api")
async def test_api(req: ApiTestRequest):
    _check_url(req.url)
    method = req.method.upper()
    cases = []
    async with httpx.AsyncClient(timeout=TIMEOUT, headers={"User-Agent": USER_AGENT}) as client:
        t0 = time.perf_counter()
        try:
            r = await client.request(method, req.url, headers=req.headers,
                                     json=req.body if req.body is not None else None)
        except httpx.HTTPError as e:
            cases.append(_case("API-01", f"{method} répond", "Réponse HTTP",
                               f"Erreur : {type(e).__name__}", False))
            return {"requete": {"method": method, "url": req.url}, "cas": cases,
                    "resume": _summary(cases)}
        ms = round((time.perf_counter() - t0) * 1000)

    cases.append(_case("API-01", "Code de statut HTTP", str(req.expected_status),
                       str(r.status_code), r.status_code == req.expected_status))
    cases.append(_case("API-02", "Temps de réponse", f"< {req.max_response_ms} ms",
                       f"{ms} ms", ms < req.max_response_ms))
    data, is_json = None, False
    try:
        data, is_json = r.json(), True
    except ValueError:
        pass
    if req.expected_keys:
        cases.append(_case("API-03", "Réponse au format JSON", "JSON valide",
                           "JSON" if is_json else r.headers.get("content-type", "inconnu"), is_json))
        target = data[0] if isinstance(data, list) and data else data
        for i, key in enumerate(req.expected_keys, start=4):
            present = isinstance(target, dict) and key in target
            cases.append(_case(f"API-{i:02d}", f"Champ « {key} » présent", "présent",
                               "présent" if present else "absent", present))

    preview = data if is_json else r.text[:500]
    return {"requete": {"method": method, "url": req.url}, "statut_http": r.status_code,
            "temps_ms": ms, "apercu_reponse": preview, "cas": cases, "resume": _summary(cases)}
