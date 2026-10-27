"""
=============================================================================
LLM Diagnostic Test — Tests all configured LLM providers
=============================================================================
Run from: ai_engine/
  python test_llm.py
=============================================================================
"""
import sys, os, time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / "src"))

# Load .env
def load_env():
    env_file = Path(__file__).parent / ".env"
    if env_file.exists():
        for line in env_file.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, _, v = line.partition("=")
                os.environ.setdefault(k.strip(), v.strip())
load_env()

PROVIDER        = os.environ.get("LLM_PROVIDER", "none")
GROQ_KEY        = os.environ.get("GROQ_API_KEY", "")
GROQ_MODEL      = os.environ.get("GROQ_MODEL", "llama-3.3-70b-versatile")
GROQ_FAST       = os.environ.get("GROQ_FAST_MODEL", "llama-3.1-8b-instant")
GEMINI_KEY      = os.environ.get("GEMINI_API_KEY", "")
GEMINI_MODEL    = os.environ.get("GEMINI_MODEL", "gemini-2.0-flash")
OLLAMA_URL      = os.environ.get("OLLAMA_BASE_URL", "http://localhost:11434")
OLLAMA_MODEL    = os.environ.get("OLLAMA_MODEL", "llama3.2:3b")
INTERNAL_KEY    = os.environ.get("INTERNAL_API_KEY", "")

SEP   = "=" * 65
SSEP  = "-" * 65
OK    = "[PASS]"
FAIL  = "[FAIL]"
WARN  = "[WARN]"
INFO  = "[INFO]"

TEST_PROMPT = (
    "You are a legal AI. In 2 sentences, explain what Section 438 of "
    "the Indian Code of Criminal Procedure (anticipatory bail) means."
)

results = {"pass": 0, "fail": 0, "warn": 0}

def check(label, ok, detail=""):
    tag = OK if ok else FAIL
    if ok: results["pass"] += 1
    else:  results["fail"] += 1
    print(f"  {tag}  {label}")
    if detail: print(f"        {detail}")

def warn_msg(label, detail=""):
    results["warn"] += 1
    print(f"  {WARN}  {label}")
    if detail: print(f"        {detail}")

def section(title):
    print(f"\n{SEP}\n  {title}\n{SEP}")


# ── Header ────────────────────────────────────────────────────────────────────
print(f"\n{SEP}")
print("  Legal Research Assistant — LLM Diagnostic Test")
print(SEP)
print(f"  Configured LLM_PROVIDER : {PROVIDER}")
print(f"  Groq key present        : {'YES (' + GROQ_KEY[:8] + '...)' if GROQ_KEY else 'NO'}")
print(f"  Groq model              : {GROQ_MODEL}")
print(f"  Gemini key present      : {'YES (' + GEMINI_KEY[:8] + '...)' if GEMINI_KEY else 'NO'}")
print(f"  Gemini model            : {GEMINI_MODEL}")
print(f"  Ollama URL              : {OLLAMA_URL}")
print(f"  Ollama model            : {OLLAMA_MODEL}")
print(SEP)


# ─────────────────────────────────────────────────────────────────────────────
# TEST 1 — Environment / Configuration
# ─────────────────────────────────────────────────────────────────────────────
section("TEST 1 — Environment & Configuration")

check(".env loaded correctly",         PROVIDER != "", f"LLM_PROVIDER={PROVIDER}")
check("GROQ_API_KEY is set",           bool(GROQ_KEY),   f"Key: {GROQ_KEY[:12]}..." if GROQ_KEY else "MISSING")
check("GEMINI_API_KEY is set",         bool(GEMINI_KEY), f"Key: {GEMINI_KEY[:12]}..." if GEMINI_KEY else "MISSING")
check("INTERNAL_API_KEY is set",       bool(INTERNAL_KEY))
check("Active provider is groq/gemini",
      PROVIDER in ("groq", "gemini", "ollama", "openai"),
      f"Provider: {PROVIDER}")


# ─────────────────────────────────────────────────────────────────────────────
# TEST 2 — Package availability
# ─────────────────────────────────────────────────────────────────────────────
section("TEST 2 — Required Packages")

for pkg, import_name in [
    ("groq",        "groq"),
    ("google-genai","google.genai"),
    ("requests",    "requests"),
]:
    try:
        __import__(import_name)
        check(f"Package '{pkg}' installed", True)
    except ImportError:
        check(f"Package '{pkg}' installed", False, f"pip install {pkg}")


# ─────────────────────────────────────────────────────────────────────────────
# TEST 3 — Groq LLM (primary provider)
# ─────────────────────────────────────────────────────────────────────────────
section("TEST 3 — Groq LLM (Primary: llama-3.3-70b-versatile)")

if not GROQ_KEY:
    warn_msg("Skipping Groq tests — GROQ_API_KEY not set")
else:
    # 3a: SDK connection
    try:
        from groq import Groq
        client = Groq(api_key=GROQ_KEY)
        check("Groq SDK initialized", True)
    except Exception as e:
        check("Groq SDK initialized", False, str(e))
        client = None

    # 3b: Main model generation
    if client:
        try:
            t0 = time.time()
            resp = client.chat.completions.create(
                model=GROQ_MODEL,
                messages=[{"role": "user", "content": TEST_PROMPT}],
                max_tokens=300,
                temperature=0.3,
            )
            elapsed = (time.time() - t0) * 1000
            text = resp.choices[0].message.content.strip()
            tokens_in  = resp.usage.prompt_tokens
            tokens_out = resp.usage.completion_tokens
            check(
                f"Groq main model ({GROQ_MODEL}) — LIVE generation",
                len(text) > 50,
                f"Response ({elapsed:.0f}ms, in={tokens_in} out={tokens_out} tokens):\n"
                f"        \"{text[:200]}...\""
            )
        except Exception as e:
            check(f"Groq main model ({GROQ_MODEL})", False, str(e))

    # 3c: Fast model generation
    if client:
        try:
            t0 = time.time()
            resp = client.chat.completions.create(
                model=GROQ_FAST,
                messages=[{"role": "user", "content": "In one sentence, what is bail?"}],
                max_tokens=100,
                temperature=0.3,
            )
            elapsed = (time.time() - t0) * 1000
            text = resp.choices[0].message.content.strip()
            check(
                f"Groq fast model ({GROQ_FAST})",
                len(text) > 10,
                f"Response ({elapsed:.0f}ms): \"{text[:150]}\""
            )
        except Exception as e:
            check(f"Groq fast model ({GROQ_FAST})", False, str(e))

    # 3d: Legal-domain prompt
    if client:
        try:
            t0 = time.time()
            legal_prompt = (
                "You are an Indian legal expert. List 3 key conditions for "
                "granting anticipatory bail under Section 438 CrPC. Be concise."
            )
            resp = client.chat.completions.create(
                model=GROQ_MODEL,
                messages=[{"role": "user", "content": legal_prompt}],
                max_tokens=300,
                temperature=0.3,
            )
            elapsed = (time.time() - t0) * 1000
            text = resp.choices[0].message.content.strip()
            check(
                "Groq legal domain prompt",
                "bail" in text.lower() or "438" in text or "condition" in text.lower(),
                f"({elapsed:.0f}ms): \"{text[:200]}...\""
            )
        except Exception as e:
            check("Groq legal domain prompt", False, str(e))


# ─────────────────────────────────────────────────────────────────────────────
# TEST 4 — Gemini LLM (fallback)
# ─────────────────────────────────────────────────────────────────────────────
section("TEST 4 — Gemini LLM (Fallback: gemini-2.0-flash)")

if not GEMINI_KEY:
    warn_msg("Skipping Gemini tests — GEMINI_API_KEY not set")
else:
    try:
        from google import genai
        from google.genai import types
        client_g = genai.Client(api_key=GEMINI_KEY)
        check("Gemini SDK initialized (google-genai)", True)

        t0 = time.time()
        response = client_g.models.generate_content(
            model=GEMINI_MODEL,
            contents=TEST_PROMPT,
            config=types.GenerateContentConfig(
                max_output_tokens=300,
                temperature=0.3,
            ),
        )
        elapsed = (time.time() - t0) * 1000
        text = response.text.strip() if response and response.text else ""
        check(
            f"Gemini ({GEMINI_MODEL}) — LIVE generation",
            len(text) > 50,
            f"Response ({elapsed:.0f}ms): \"{text[:200]}...\""
        )
    except Exception as e:
        check("Gemini SDK / generation", False, str(e))


# ─────────────────────────────────────────────────────────────────────────────
# TEST 5 — Ollama LLM (local fallback)
# ─────────────────────────────────────────────────────────────────────────────
section("TEST 5 — Ollama LLM (Local Fallback)")

try:
    import requests as _req
    r = _req.get(f"{OLLAMA_URL}/api/tags", timeout=3)
    ollama_up = r.status_code == 200
    check(f"Ollama server reachable at {OLLAMA_URL}", ollama_up,
          f"Status: {r.status_code}" if ollama_up else "Not reachable (optional)")
    if ollama_up:
        models = [m["name"] for m in r.json().get("models", [])]
        check(f"Model '{OLLAMA_MODEL}' available",
              any(OLLAMA_MODEL in m for m in models),
              f"Available models: {models or 'none'}")
except Exception as e:
    warn_msg(f"Ollama not running (optional): {e}")


# ─────────────────────────────────────────────────────────────────────────────
# TEST 6 — LLM factory (get_llm from llm/base.py)
# ─────────────────────────────────────────────────────────────────────────────
section("TEST 6 — AI Engine LLM Factory (llm/base.py get_llm)")

try:
    from llm.base import get_llm
    llm = get_llm(force_new=True)
    llm_type = type(llm).__name__
    check(f"get_llm() returns valid instance: {llm_type}", llm_type != "NoLLM",
          f"Provider: {PROVIDER} → {llm_type}")

    available = llm.is_available()
    check(f"llm.is_available() = {available}", available)

    if available and llm_type != "NoLLM":
        try:
            t0 = time.time()
            response = llm.generate(TEST_PROMPT, max_tokens=300)
            elapsed  = (time.time() - t0) * 1000
            check(
                f"llm.generate() via {llm_type} — end-to-end",
                len(response) > 50,
                f"({elapsed:.0f}ms): \"{response[:200]}...\""
            )
        except Exception as e:
            check(f"llm.generate() via {llm_type}", False, str(e))

except Exception as e:
    check("LLM factory import / init", False, str(e))


# ─────────────────────────────────────────────────────────────────────────────
# TEST 7 — Live API with LLM enabled (use_llm=true)
# ─────────────────────────────────────────────────────────────────────────────
section("TEST 7 — Live AI Engine API with use_llm=true")

import urllib.request, json as _json

test_queries_llm = [
    "What is anticipatory bail under Section 438 of CrPC?",
    "What is the punishment for murder under IPC Section 302?",
]

for q in test_queries_llm:
    payload = _json.dumps({"question": q, "use_llm": True}).encode()
    req = urllib.request.Request(
        "http://localhost:5000/api/query",
        data=payload,
        headers={
            "Content-Type": "application/json",
            "X-Internal-API-Key": INTERNAL_KEY,
        },
        method="POST"
    )
    try:
        t0 = time.time()
        with urllib.request.urlopen(req, timeout=60) as resp:
            data    = _json.loads(resp.read())
            elapsed = (time.time() - t0) * 1000
            answer  = data.get("answer", "")
            sources = len(data.get("sources", []))
            graphs  = len(data.get("graph_references") or [])
            conf    = data.get("confidence", 0)
            intent  = data.get("intent", "?")
            check(
                f"API use_llm=true: '{q[:50]}'",
                len(answer) > 100,
                f"answer={len(answer)}chars | sources={sources} | graph={graphs} | conf={conf:.2f} | intent={intent} | {elapsed:.0f}ms\n"
                f"        Answer preview: \"{answer[:250]}...\""
            )
    except Exception as e:
        check(f"API use_llm=true: '{q[:50]}'", False, str(e))


# ─────────────────────────────────────────────────────────────────────────────
# FINAL SUMMARY
# ─────────────────────────────────────────────────────────────────────────────
total = results["pass"] + results["fail"]
print(f"\n{SEP}")
print("  FINAL LLM DIAGNOSTIC RESULTS")
print(SEP)
print(f"  [PASS] PASSED  : {results['pass']}")
print(f"  [FAIL] FAILED  : {results['fail']}")
print(f"  [WARN] WARNINGS: {results['warn']}")
print(f"  TOTAL          : {total} tests")

if results["fail"] == 0:
    print(f"\n  ALL TESTS PASSED! LLM is fully operational.")
    print(f"  Active provider: {PROVIDER.upper()} — {GROQ_MODEL if PROVIDER == 'groq' else GEMINI_MODEL if PROVIDER == 'gemini' else OLLAMA_MODEL}")
else:
    print(f"\n  {results['fail']} test(s) failed — see above for details.")
print(SEP + "\n")
sys.exit(0 if results["fail"] == 0 else 1)
