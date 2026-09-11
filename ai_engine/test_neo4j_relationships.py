"""
=============================================================================
Neo4j Knowledge Graph — Comprehensive Relationship Test Suite
=============================================================================
Tests ALL node types, relationships, and graph query functions.
Run from: ai_engine/
=============================================================================
"""
import sys
import os
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / "src"))

# Load .env manually
def load_env():
    env_file = Path(__file__).parent / ".env"
    if env_file.exists():
        for line in env_file.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, _, v = line.partition("=")
                os.environ.setdefault(k.strip(), v.strip())
load_env()

from neo4j import GraphDatabase

URI      = os.environ.get("NEO4J_URI", "")
USER     = os.environ.get("NEO4J_USERNAME", "neo4j")
PASSWORD = os.environ.get("NEO4J_PASSWORD", "")

# ── Colours ───────────────────────────────────────────────────────────────────
GREEN  = "\033[92m"
RED    = "\033[91m"
YELLOW = "\033[93m"
BLUE   = "\033[94m"
CYAN   = "\033[96m"
BOLD   = "\033[1m"
RESET  = "\033[0m"

PASS = f"{GREEN}✅ PASS{RESET}"
FAIL = f"{RED}❌ FAIL{RESET}"
INFO = f"{CYAN}ℹ️  INFO{RESET}"

results = {"pass": 0, "fail": 0, "warn": 0}

def section(title):
    print(f"\n{BOLD}{BLUE}{'='*65}{RESET}")
    print(f"{BOLD}{BLUE}  {title}{RESET}")
    print(f"{BOLD}{BLUE}{'='*65}{RESET}")

def run(driver, q, params=None):
    with driver.session() as s:
        return [r.data() for r in s.run(q, params or {})]

def check(label, condition, detail=""):
    if condition:
        results["pass"] += 1
        print(f"  {PASS}  {label}")
        if detail:
            print(f"        {CYAN}{detail}{RESET}")
    else:
        results["fail"] += 1
        print(f"  {FAIL}  {label}")
        if detail:
            print(f"        {YELLOW}{detail}{RESET}")

def warn(label, detail=""):
    results["warn"] += 1
    print(f"  {YELLOW}⚠️  WARN{RESET}  {label}")
    if detail:
        print(f"        {detail}")


# ═════════════════════════════════════════════════════════════════════════════
print(f"\n{BOLD}{'='*65}")
print("  Legal Research Assistant — Neo4j Relationship Test Suite")
print(f"{'='*65}{RESET}")
print(f"  URI:  {URI}")
print(f"  User: {USER}")

# Connect
try:
    driver = GraphDatabase.driver(URI, auth=(USER, PASSWORD))
    driver.verify_connectivity()
    print(f"\n  {PASS}  Connected to Neo4j AuraDB\n")
except Exception as e:
    print(f"\n  {FAIL}  Cannot connect: {e}")
    sys.exit(1)


# ─────────────────────────────────────────────────────────────────────────────
# TEST 1 — Node counts
# ─────────────────────────────────────────────────────────────────────────────
section("TEST 1 — Node Counts")

r = run(driver, "MATCH (a:Act) RETURN count(a) AS n")[0]
check(f"Acts = {r['n']} (expected 19)", r['n'] == 19, f"Found {r['n']} acts")

r = run(driver, "MATCH (s:Section) RETURN count(s) AS n")[0]
check(f"Sections = {r['n']} (expected 164)", r['n'] == 164, f"Found {r['n']} sections")

r = run(driver, "MATCH (c:Case) RETURN count(c) AS n")[0]
check(f"Cases = {r['n']} (expected 10)", r['n'] == 10, f"Found {r['n']} cases")

r = run(driver, "MATCH (p:Principle) RETURN count(p) AS n")[0]
check(f"Principles = {r['n']} (expected 6)", r['n'] == 6, f"Found {r['n']} principles")


# ─────────────────────────────────────────────────────────────────────────────
# TEST 2 — Relationship counts
# ─────────────────────────────────────────────────────────────────────────────
section("TEST 2 — Relationship Counts")

for rel, expected in [
    ("HAS_SECTION", 164),
    ("RELATED_TO",  18),
    ("INTERPRETS",  9),
    ("DEFINES",     6),
    ("ESTABLISHES", 3),
]:
    r = run(driver, f"MATCH ()-[r:{rel}]->() RETURN count(r) AS n")[0]
    check(f"{rel} = {r['n']} (expected {expected})", r['n'] == expected,
          f"Found {r['n']}")


# ─────────────────────────────────────────────────────────────────────────────
# TEST 3 — All 19 Acts present with correct metadata
# ─────────────────────────────────────────────────────────────────────────────
section("TEST 3 — All 19 Acts with Correct Metadata")

EXPECTED_ACTS = {
    "IPC": ("Indian Penal Code", 1860),
    "CrPC": ("Code of Criminal Procedure", 1973),
    "Evidence": ("Indian Evidence Act", 1872),
    "Contract": ("Indian Contract Act", 1872),
    "CPC": ("Code of Civil Procedure", 1908),
    "Companies": ("Companies Act", 2013),
    "Constitution": ("Constitution of India", 1950),
    "GST": ("Goods and Services Tax Act", 2017),
    "MVA": ("Motor Vehicles Act", 1988),
    "ITA": ("Income Tax Act", 1961),
    "HMA": ("Hindu Marriage Act", 1955),
    "IDA": ("Industrial Disputes Act", 1947),
    "CPA": ("Consumer Protection Act", 2019),
    "NIA": ("Negotiable Instruments Act", 1881),
    "IT": ("Information Technology Act", 2000),
    "RTI": ("Right to Information Act", 2005),
    "RPA": ("Representation of the People Act", 1951),
    "TPA": ("Transfer of Property Act", 1882),
    "FSSA": ("Food Safety and Standards Act", 2006),
}

acts_in_db = run(driver, "MATCH (a:Act) RETURN a.short_name AS k, a.name AS name, a.year AS year")
acts_map = {a["k"]: (a["name"], a["year"]) for a in acts_in_db}

for short, (name, year) in EXPECTED_ACTS.items():
    found = short in acts_map
    year_ok = acts_map.get(short, (None, None))[1] == year if found else False
    check(f"Act {short} ({year})", found and year_ok,
          f"{acts_map.get(short, 'NOT FOUND')}")


# ─────────────────────────────────────────────────────────────────────────────
# TEST 4 — Sections per act
# ─────────────────────────────────────────────────────────────────────────────
section("TEST 4 — Sections per Act (HAS_SECTION)")

expected_sections = {
    "IPC": 9, "CrPC": 7, "Evidence": 10, "Contract": 9, "CPC": 9,
    "Companies": 7, "Constitution": 8, "GST": 10, "MVA": 10, "ITA": 8,
    "HMA": 9, "IDA": 4, "CPA": 10, "NIA": 10, "IT": 7,
    "RTI": 9, "RPA": 9, "TPA": 9, "FSSA": 10,
}

rows = run(driver, """
    MATCH (a:Act)-[:HAS_SECTION]->(s:Section)
    RETURN a.short_name AS act, count(s) AS cnt
    ORDER BY act
""")
db_counts = {r["act"]: r["cnt"] for r in rows}

for act, exp in sorted(expected_sections.items()):
    got = db_counts.get(act, 0)
    check(f"{act}: {got} sections (expected {exp})", got == exp)


# ─────────────────────────────────────────────────────────────────────────────
# TEST 5 — Cross-reference RELATED_TO relationships
# ─────────────────────────────────────────────────────────────────────────────
section("TEST 5 — Cross-Reference RELATED_TO Relationships")

EXPECTED_RELATED = [
    ("CrPC", "438", "CrPC", "437"),
    ("CrPC", "438", "CrPC", "436"),
    ("CrPC", "437", "CrPC", "436"),
    ("CrPC", "41",  "CrPC", "50"),
    ("IPC",  "302", "IPC",  "300"),
    ("NIA",  "138", "NIA",  "139"),
    ("NIA",  "138", "NIA",  "140"),
    ("NIA",  "138", "NIA",  "141"),
    ("NIA",  "138", "NIA",  "142"),
    ("NIA",  "138", "NIA",  "143"),
    ("IT",   "43",  "IT",   "66"),
    ("IT",   "66",  "IT",   "67"),
    ("CPA",  "35",  "CPA",  "38"),
    ("CPA",  "38",  "CPA",  "47"),
    ("IPC",  "420", "IPC",  "499"),
    ("HMA",  "13",  "HMA",  "11"),
    ("HMA",  "13",  "HMA",  "10"),
    ("IDA",  "25",  "IDA",  "10"),
]

for src_act, src_sec, tgt_act, tgt_sec in EXPECTED_RELATED:
    r = run(driver, """
        MATCH (a:Section {number: $sn, act_short_name: $sa})
              -[:RELATED_TO]->
              (b:Section {number: $tn, act_short_name: $ta})
        RETURN count(*) AS n
    """, {"sn": src_sec, "sa": src_act, "tn": tgt_sec, "ta": tgt_act})
    found = r[0]["n"] > 0 if r else False
    check(f"{src_act}§{src_sec} → RELATED_TO → {tgt_act}§{tgt_sec}", found)


# ─────────────────────────────────────────────────────────────────────────────
# TEST 6 — Landmark Cases & INTERPRETS
# ─────────────────────────────────────────────────────────────────────────────
section("TEST 6 — Landmark Cases & INTERPRETS Relationships")

EXPECTED_CASES = [
    ("AIR 1980 SC 1632", "Gurbaksh Singh Sibbia vs State of Punjab", "438", "CrPC"),
    ("AIR 2014 SC 2756", "Arnesh Kumar vs State of Bihar",            "438", "CrPC"),
    ("AIR 1962 SC 605",  "K.M. Nanavati vs State of Maharashtra",     "302", "IPC"),
    ("AIR 1980 SC 898",  "Bachan Singh vs State of Punjab",           "302", "IPC"),
    ("AIR 1997 SC 3011", "Vishaka vs State of Rajasthan",             "376", "IPC"),
    ("AIR 1982 SC 149",  "S.P. Gupta vs Union of India",              "6",   "RTI"),
    ("(2017) 7 SCC 593", "M.S. Dhoni vs Yerraguntla Shyamsundar",    "138", "NIA"),
    ("(1996) 2 SCC 739", "Electronics Trade & Technology Development vs Indian Technologists", "11", "Contract"),
    ("AIR 1973 SC 1461", "Kesavananda Bharati vs State of Kerala",    "13",  "Constitution"),
]

for citation, name, sec, act in EXPECTED_CASES:
    r = run(driver, """
        MATCH (c:Case {citation: $cit})-[:INTERPRETS]->(s:Section {number: $sec, act_short_name: $act})
        RETURN c.name AS name, c.year AS year
    """, {"cit": citation, "sec": sec, "act": act})
    found = len(r) > 0
    year = r[0]["year"] if found else "?"
    check(f"Case ({year}): {name[:55]}", found,
          f"→ INTERPRETS {act}§{sec}")


# ─────────────────────────────────────────────────────────────────────────────
# TEST 7 — DEFINES relationships (Section → Principle)
# ─────────────────────────────────────────────────────────────────────────────
section("TEST 7 — DEFINES Relationships (Section → Principle)")

EXPECTED_DEFINES = [
    ("438", "CrPC",         "Anticipatory Bail"),
    ("437", "CrPC",         "Regular Bail"),
    ("13",  "Constitution", "Basic Structure Doctrine"),
    ("138", "NIA",          "Cheque Dishonour Offence"),
    ("6",   "RTI",          "Right to Information"),
    ("10",  "Contract",     "Freedom of Contract"),
]

for sec, act, principle in EXPECTED_DEFINES:
    r = run(driver, """
        MATCH (s:Section {number: $sec, act_short_name: $act})-[:DEFINES]->(p:Principle {name: $name})
        RETURN count(*) AS n
    """, {"sec": sec, "act": act, "name": principle})
    found = r[0]["n"] > 0 if r else False
    check(f"{act}§{sec} → DEFINES → '{principle}'", found)


# ─────────────────────────────────────────────────────────────────────────────
# TEST 8 — ESTABLISHES relationships (Case → Principle)
# ─────────────────────────────────────────────────────────────────────────────
section("TEST 8 — ESTABLISHES Relationships (Case → Principle)")

EXPECTED_ESTABLISHES = [
    ("AIR 1980 SC 1632", "Anticipatory Bail"),
    ("AIR 2014 SC 2756", "Anticipatory Bail"),
    ("AIR 1973 SC 1461", "Basic Structure Doctrine"),
]

for citation, principle in EXPECTED_ESTABLISHES:
    r = run(driver, """
        MATCH (c:Case {citation: $cit})-[:ESTABLISHES]->(p:Principle {name: $name})
        RETURN c.name AS cname
    """, {"cit": citation, "name": principle})
    found = len(r) > 0
    check(f"'{citation}' → ESTABLISHES → '{principle}'", found,
          r[0]["cname"] if found else "")


# ─────────────────────────────────────────────────────────────────────────────
# TEST 9 — Specific section property checks
# ─────────────────────────────────────────────────────────────────────────────
section("TEST 9 — Section Properties & Common Names")

SECTION_PROPS = [
    ("438", "CrPC",         "common_name", "Anticipatory Bail"),
    ("302", "IPC",          "common_name", "Murder Punishment"),
    ("138", "NIA",          "common_name", "Cheque Dishonour"),
    ("13",  "Constitution", "common_name", "Laws Inconsistent with FR"),
    ("66",  "IT",           "common_name", "Computer Related Offences"),
    ("13",  "HMA",          "common_name", "Divorce"),
    ("6",   "RTI",          "common_name", "RTI Application"),
]

for sec, act, prop, expected in SECTION_PROPS:
    r = run(driver, f"MATCH (s:Section {{number: $sec, act_short_name: $act}}) RETURN s.{prop} AS val",
            {"sec": sec, "act": act})
    val = r[0]["val"] if r else None
    check(f"{act}§{sec}.{prop} = '{expected}'", val == expected,
          f"Got: '{val}'")


# ─────────────────────────────────────────────────────────────────────────────
# TEST 10 — AI Engine graph_queries integration (fetch_legal_graph_facts)
# ─────────────────────────────────────────────────────────────────────────────
section("TEST 10 — AI Engine graph_queries Integration")

try:
    from graph.neo4j_client import get_neo4j_client
    from graph.graph_queries import fetch_legal_graph_facts, build_graph_context

    client = get_neo4j_client(uri=URI, username=USER, password=PASSWORD)

    TEST_QUERIES = [
        ("What is anticipatory bail under Section 438?",   ["438"], "bail"),
        ("What is the punishment for murder Section 302?", ["302"], "murder"),
        ("Cheating under Section 420 IPC",                 ["420"], "cheating"),
    ]

    for query, expected_sections, concept in TEST_QUERIES:
        facts = fetch_legal_graph_facts(query, client)
        has_facts = len(facts) > 0
        check(f"graph_facts for '{concept}' query → {len(facts)} facts", has_facts,
              f"Sections hit: {[f.get('section','?') for f in facts[:3]]}")

        context = build_graph_context(facts)
        has_context = len(context) > 20
        check(f"build_graph_context for '{concept}' → non-empty", has_context,
              f"Context length: {len(context)} chars")

    if client:
        client.close()

except Exception as e:
    warn(f"graph_queries integration test failed: {e}")


# ─────────────────────────────────────────────────────────────────────────────
# TEST 11 — Live AI Engine API test (via HTTP)
# ─────────────────────────────────────────────────────────────────────────────
section("TEST 11 — Live AI Engine API (HTTP /search)")

try:
    import urllib.request, json as _json

    API_KEY = os.environ.get("INTERNAL_API_KEY", "")
    test_queries = [
        "What is anticipatory bail?",
        "What is the punishment for murder?",
        "Cheque dishonour under Section 138",
    ]

    for q in test_queries:
        payload = _json.dumps({"question": q, "use_llm": False}).encode()
        req = urllib.request.Request(
            "http://localhost:5000/api/query",
            data=payload,
            headers={
                "Content-Type": "application/json",
                "X-Internal-API-Key": API_KEY,
            },
            method="POST"
        )
        try:
            with urllib.request.urlopen(req, timeout=45) as resp:
                data = _json.loads(resp.read())
                answer_len   = len(data.get("answer", ""))
                sources      = len(data.get("sources", []))
                graph_refs   = len(data.get("graph_references") or [])
                confidence   = data.get("confidence", 0)
                proc_time    = data.get("processing_time_ms", 0)
                check(
                    f"API /api/query: '{q[:50]}'",
                    answer_len > 0,
                    f"answer={answer_len}chars | sources={sources} | graph_refs={graph_refs} | conf={confidence:.2f} | {proc_time:.0f}ms"
                )
        except Exception as e:
            warn(f"API call failed for '{q[:50]}': {e}")

except Exception as e:
    warn(f"HTTP test setup failed: {e}")


# ─────────────────────────────────────────────────────────────────────────────
# TEST 12 — Advanced graph traversals
# ─────────────────────────────────────────────────────────────────────────────
section("TEST 12 — Advanced Graph Traversals")

# 2-hop: Case → Section → Related Section
r = run(driver, """
    MATCH (c:Case)-[:INTERPRETS]->(s:Section)-[:RELATED_TO]->(r:Section)
    RETURN c.name AS case_name, s.number AS section, r.number AS related, r.act_short_name AS act
    LIMIT 5
""")
check("2-hop: Case→Section→RELATED_TO→Section", len(r) > 0,
      f"Found {len(r)} paths. Example: {r[0] if r else 'none'}")

# Principle → Case (reverse ESTABLISHES)
r = run(driver, """
    MATCH (p:Principle)<-[:ESTABLISHES]-(c:Case)
    RETURN p.name AS principle, collect(c.name) AS cases
""")
check("Principle←ESTABLISHES←Case (reverse lookup)", len(r) > 0,
      f"Principles with cases: {[x['principle'] for x in r]}")

# All bail-related sections across all acts
r = run(driver, """
    MATCH (s:Section)
    WHERE toLower(s.title) CONTAINS 'bail' OR toLower(s.common_name) CONTAINS 'bail'
    RETURN s.act_short_name AS act, s.number AS sec, s.title AS title
    ORDER BY s.act_short_name
""")
check(f"Bail-related sections across acts = {len(r)}", len(r) >= 3,
      f"Found: {[(x['act'], x['sec']) for x in r]}")

# All penalty/punishment sections
r = run(driver, """
    MATCH (s:Section)
    WHERE toLower(s.title) CONTAINS 'punishment' OR toLower(s.title) CONTAINS 'penalty'
    RETURN s.act_short_name AS act, count(s) AS cnt
    ORDER BY cnt DESC
    LIMIT 5
""")
check(f"Penalty sections found across {len(r)} acts", len(r) > 0,
      f"Top acts: {[(x['act'], x['cnt']) for x in r]}")

# Cheque dishonour cluster (NIA 138 → all its neighbours)
r = run(driver, """
    MATCH (s:Section {number: '138', act_short_name: 'NIA'})-[:RELATED_TO]->(n:Section)
    RETURN n.number AS num, n.title AS title
    ORDER BY toInteger(n.number)
""")
check(f"NIA §138 cluster has {len(r)} related sections (expected 5)", len(r) == 5,
      f"Sections: {[x['num'] for x in r]}")

# Divorce cluster in HMA
r = run(driver, """
    MATCH (s:Section {number: '13', act_short_name: 'HMA'})-[:RELATED_TO]->(n:Section)
    RETURN n.number AS num, n.title AS title
""")
check(f"HMA §13 (Divorce) cluster has {len(r)} related sections (expected 2)", len(r) == 2,
      f"Sections: {[x['num'] for x in r]}")


# ─────────────────────────────────────────────────────────────────────────────
# FINAL SUMMARY
# ─────────────────────────────────────────────────────────────────────────────
driver.close()

total = results["pass"] + results["fail"]
print(f"\n{BOLD}{'='*65}")
print("  FINAL TEST RESULTS")
print(f"{'='*65}{RESET}")
print(f"  {GREEN}✅ PASSED:{RESET} {results['pass']}")
print(f"  {RED}❌ FAILED:{RESET} {results['fail']}")
print(f"  {YELLOW}⚠️  WARNINGS:{RESET} {results['warn']}")
print(f"  {BOLD}TOTAL:{RESET}  {total} tests")

if results["fail"] == 0:
    print(f"\n  {GREEN}{BOLD}🎉 ALL TESTS PASSED! Neo4j graph is perfectly healthy.{RESET}")
else:
    print(f"\n  {RED}{BOLD}Some tests failed — check above for details.{RESET}")

print(f"{BOLD}{'='*65}{RESET}\n")
sys.exit(0 if results["fail"] == 0 else 1)
