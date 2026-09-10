"""
=============================================================================
Legal Research Assistant — Neo4j Knowledge Graph Setup Script
=============================================================================
Reads credentials from ai_engine/.env and populates a fresh Neo4j AuraDB
instance with:
  • 19 Acts (all folders under data_ingestion/storage/acts/)
  • ~164 Sections (all JSON files, dynamically loaded)
  • HAS_SECTION relationships (Act → Section)
  • RELATED_TO cross-references (bail, murder, cheque sections)
  • Landmark Case nodes + INTERPRETS relationships
  • Principle nodes + DEFINES relationships
  • Indexes on Section.number and Section.act_short_name

Usage:
    cd ai_engine
    python setup_neo4j_graph.py
=============================================================================
"""

import sys
import os
import json
import logging
from pathlib import Path

# ── Setup paths ──────────────────────────────────────────────────────────────
SCRIPT_DIR   = Path(__file__).parent
SRC_DIR      = SCRIPT_DIR / "src"
ACTS_DIR     = SCRIPT_DIR.parent / "data_ingestion" / "storage" / "acts"
ENV_FILE     = SCRIPT_DIR / ".env"

sys.path.insert(0, str(SRC_DIR))

# ── Load .env manually (no dependency on pydantic here) ──────────────────────
def load_env(env_path: Path) -> dict:
    env = {}
    if env_path.exists():
        with open(env_path, encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#"):
                    continue
                if "=" in line:
                    key, _, value = line.partition("=")
                    env[key.strip()] = value.strip()
    return env

env = load_env(ENV_FILE)
NEO4J_URI      = env.get("NEO4J_URI", "")
NEO4J_USERNAME = env.get("NEO4J_USERNAME", "neo4j")
NEO4J_PASSWORD = env.get("NEO4J_PASSWORD", "")

# ── Logging ───────────────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-8s  %(message)s",
    datefmt="%H:%M:%S",
)
log = logging.getLogger("neo4j_setup")


# ═════════════════════════════════════════════════════════════════════════════
# ACT METADATA  (short_name → metadata used in graph nodes)
# ═════════════════════════════════════════════════════════════════════════════
ACT_META = {
    "ipc":           {"short_name": "IPC",           "name": "Indian Penal Code",                   "year": 1860},
    "crpc":          {"short_name": "CrPC",          "name": "Code of Criminal Procedure",          "year": 1973},
    "evidence":      {"short_name": "Evidence",      "name": "Indian Evidence Act",                  "year": 1872},
    "contract":      {"short_name": "Contract",      "name": "Indian Contract Act",                  "year": 1872},
    "cpc":           {"short_name": "CPC",           "name": "Code of Civil Procedure",             "year": 1908},
    "companies":     {"short_name": "Companies",     "name": "Companies Act",                        "year": 2013},
    "constitution":  {"short_name": "Constitution",  "name": "Constitution of India",                "year": 1950},
    "gst":           {"short_name": "GST",           "name": "Goods and Services Tax Act",           "year": 2017},
    "mva":           {"short_name": "MVA",           "name": "Motor Vehicles Act",                   "year": 1988},
    "ita":           {"short_name": "ITA",           "name": "Income Tax Act",                       "year": 1961},
    "hindu_marriage":{"short_name": "HMA",           "name": "Hindu Marriage Act",                   "year": 1955},
    "ida":           {"short_name": "IDA",           "name": "Industrial Disputes Act",              "year": 1947},
    "cpa":           {"short_name": "CPA",           "name": "Consumer Protection Act",              "year": 2019},
    "nia":           {"short_name": "NIA",           "name": "Negotiable Instruments Act",           "year": 1881},
    "it_act":        {"short_name": "IT",            "name": "Information Technology Act",           "year": 2000},
    "rti":           {"short_name": "RTI",           "name": "Right to Information Act",             "year": 2005},
    "rpa":           {"short_name": "RPA",           "name": "Representation of the People Act",     "year": 1951},
    "tpa":           {"short_name": "TPA",           "name": "Transfer of Property Act",             "year": 1882},
    "fssa":          {"short_name": "FSSA",          "name": "Food Safety and Standards Act",        "year": 2006},
}

# ═════════════════════════════════════════════════════════════════════════════
# LANDMARK CASES  (name, year, court, citation, section_number, act_folder)
# ═════════════════════════════════════════════════════════════════════════════
LANDMARK_CASES = [
    {
        "name":    "Gurbaksh Singh Sibbia vs State of Punjab",
        "year":    1980,
        "court":   "Supreme Court of India",
        "citation":"AIR 1980 SC 1632",
        "section": "438",
        "act":     "crpc",
        "principle": "Anticipatory Bail",
    },
    {
        "name":    "Arnesh Kumar vs State of Bihar",
        "year":    2014,
        "court":   "Supreme Court of India",
        "citation":"AIR 2014 SC 2756",
        "section": "438",
        "act":     "crpc",
        "principle": "Anticipatory Bail",
    },
    {
        "name":    "K.M. Nanavati vs State of Maharashtra",
        "year":    1962,
        "court":   "Supreme Court of India",
        "citation":"AIR 1962 SC 605",
        "section": "302",
        "act":     "ipc",
        "principle": None,
    },
    {
        "name":    "Bachan Singh vs State of Punjab",
        "year":    1980,
        "court":   "Supreme Court of India",
        "citation":"AIR 1980 SC 898",
        "section": "302",
        "act":     "ipc",
        "principle": None,
    },
    {
        "name":    "Vishaka vs State of Rajasthan",
        "year":    1997,
        "court":   "Supreme Court of India",
        "citation":"AIR 1997 SC 3011",
        "section": "376",
        "act":     "ipc",
        "principle": None,
    },
    {
        "name":    "Mohd. Ahmad Khan vs Shah Bano Begum",
        "year":    1985,
        "court":   "Supreme Court of India",
        "citation":"AIR 1985 SC 945",
        "section": "125",
        "act":     "crpc",
        "principle": None,
    },
    {
        "name":    "S.P. Gupta vs Union of India",
        "year":    1981,
        "court":   "Supreme Court of India",
        "citation":"AIR 1982 SC 149",
        "section": "6",
        "act":     "rti",
        "principle": None,
    },
    {
        "name":    "M.S. Dhoni vs Yerraguntla Shyamsundar",
        "year":    2017,
        "court":   "Supreme Court of India",
        "citation":"(2017) 7 SCC 593",
        "section": "138",
        "act":     "nia",
        "principle": None,
    },
    {
        "name":    "Electronics Trade & Technology Development vs Indian Technologists",
        "year":    1996,
        "court":   "Supreme Court of India",
        "citation":"(1996) 2 SCC 739",
        "section": "11",
        "act":     "contract",
        "principle": None,
    },
    {
        "name":    "Kesavananda Bharati vs State of Kerala",
        "year":    1973,
        "court":   "Supreme Court of India",
        "citation":"AIR 1973 SC 1461",
        "section": "13",
        "act":     "constitution",
        "principle": "Basic Structure Doctrine",
    },
]

# ═════════════════════════════════════════════════════════════════════════════
# CROSS-REFERENCE RELATIONSHIPS  (section_num, act_folder) → [(section_num, act_folder)]
# ═════════════════════════════════════════════════════════════════════════════
CROSS_REFERENCES = [
    # Bail: Anticipatory bail references Regular bail
    (("438", "crpc"), ("437", "crpc")),
    (("438", "crpc"), ("436", "crpc")),
    (("437", "crpc"), ("436", "crpc")),
    # Arrest powers
    (("41",  "crpc"), ("50",  "crpc")),
    # Murder: Punishment references definition
    (("302", "ipc"),  ("300", "ipc")),
    # Cheque dishonour cluster
    (("138", "nia"),  ("139", "nia")),
    (("138", "nia"),  ("140", "nia")),
    (("138", "nia"),  ("141", "nia")),
    (("138", "nia"),  ("142", "nia")),
    (("138", "nia"),  ("143", "nia")),
    # IT Act: Cybercrime sections
    (("43",  "it_act"), ("66", "it_act")),
    (("66",  "it_act"), ("67", "it_act")),
    # Consumer Protection: complaint → appeal
    (("35",  "cpa"),  ("38",  "cpa")),
    (("38",  "cpa"),  ("47",  "cpa")),
    # IPC: Cheating → Defamation
    (("420", "ipc"),  ("499", "ipc")),
    # Divorce sections in HMA
    (("13",  "hindu_marriage"), ("11",  "hindu_marriage")),
    (("13",  "hindu_marriage"), ("10",  "hindu_marriage")),
    # Industrial Disputes: retrenchment
    (("25",  "ida"),  ("10",  "ida")),
]

# ═════════════════════════════════════════════════════════════════════════════
# PRINCIPLES (name, description, section_num, act_folder)
# ═════════════════════════════════════════════════════════════════════════════
PRINCIPLES = [
    {
        "name":        "Anticipatory Bail",
        "description": "Bail granted by a court in anticipation of an arrest",
        "section":     "438",
        "act":         "crpc",
    },
    {
        "name":        "Regular Bail",
        "description": "Bail granted after arrest in non-bailable offence",
        "section":     "437",
        "act":         "crpc",
    },
    {
        "name":        "Basic Structure Doctrine",
        "description": "Constitutional amendments cannot destroy the basic structure of the Constitution",
        "section":     "13",
        "act":         "constitution",
    },
    {
        "name":        "Cheque Dishonour Offence",
        "description": "Dishonour of cheque for insufficiency of funds is a criminal offence",
        "section":     "138",
        "act":         "nia",
    },
    {
        "name":        "Right to Information",
        "description": "Every citizen has the right to access information held by public authorities",
        "section":     "6",
        "act":         "rti",
    },
    {
        "name":        "Freedom of Contract",
        "description": "Parties have the freedom to enter into contracts on mutually agreed terms",
        "section":     "10",
        "act":         "contract",
    },
]


# ═════════════════════════════════════════════════════════════════════════════
# SECTION METADATA  (common_name, subcategory by folder+section)
# ═════════════════════════════════════════════════════════════════════════════
SECTION_EXTRA = {
    ("crpc", "438"): {"common_name": "Anticipatory Bail",         "subcategory": "bail,arrest"},
    ("crpc", "437"): {"common_name": "Regular Bail",              "subcategory": "bail"},
    ("crpc", "436"): {"common_name": "Bail in Bailable Offence",  "subcategory": "bail"},
    ("crpc", "154"): {"common_name": "FIR",                        "subcategory": "investigation,fir"},
    ("crpc", "156"): {"common_name": "Police Investigation",       "subcategory": "investigation"},
    ("crpc", "41"):  {"common_name": "Arrest Without Warrant",     "subcategory": "arrest"},
    ("crpc", "50"):  {"common_name": "Person Arrested to be Informed", "subcategory": "arrest"},
    ("ipc",  "302"): {"common_name": "Murder Punishment",          "subcategory": "homicide,punishment"},
    ("ipc",  "300"): {"common_name": "Definition of Murder",       "subcategory": "homicide"},
    ("ipc",  "304"): {"common_name": "Culpable Homicide",          "subcategory": "homicide,punishment"},
    ("ipc",  "307"): {"common_name": "Attempt to Murder",          "subcategory": "homicide,punishment"},
    ("ipc",  "376"): {"common_name": "Rape Punishment",            "subcategory": "sexual offence,punishment"},
    ("ipc",  "377"): {"common_name": "Unnatural Offences",         "subcategory": "sexual offence,punishment"},
    ("ipc",  "420"): {"common_name": "Cheating",                   "subcategory": "fraud,cheating"},
    ("ipc",  "499"): {"common_name": "Defamation",                 "subcategory": "defamation"},
    ("ipc",  "506"): {"common_name": "Criminal Intimidation",      "subcategory": "intimidation"},
    ("nia",  "138"): {"common_name": "Cheque Dishonour",           "subcategory": "cheque,dishonour,banking"},
    ("nia",  "139"): {"common_name": "Presumption for Holder",     "subcategory": "cheque,dishonour"},
    ("nia",  "140"): {"common_name": "Defence Not Allowed",        "subcategory": "cheque,dishonour"},
    ("nia",  "141"): {"common_name": "Company Offences",           "subcategory": "cheque,dishonour"},
    ("constitution","13"):  {"common_name": "Laws Inconsistent with FR", "subcategory": "fundamental rights"},
    ("constitution","21"):  {"common_name": "Right to Life",             "subcategory": "fundamental rights"},
    ("constitution","226"): {"common_name": "High Court Writ Jurisdiction","subcategory": "writ,fundamental rights"},
    ("ita", "139"): {"common_name": "Income Tax Return",           "subcategory": "tax,return"},
    ("ita", "143"): {"common_name": "Assessment",                  "subcategory": "tax,assessment"},
    ("ita", "147"): {"common_name": "Income Escaping Assessment",  "subcategory": "tax,assessment"},
    ("ita", "10"):  {"common_name": "Exempt Incomes",              "subcategory": "tax,exemption"},
    ("hindu_marriage","13"):{"common_name": "Divorce",             "subcategory": "divorce,family"},
    ("hindu_marriage","10"):{"common_name": "Judicial Separation", "subcategory": "separation,family"},
    ("ida",  "25"):  {"common_name": "Retrenchment",               "subcategory": "labour,retrenchment"},
    ("cpa",  "35"):  {"common_name": "Consumer Complaint",         "subcategory": "consumer,complaint"},
    ("it_act","66"): {"common_name": "Computer Related Offences",  "subcategory": "cyber,offence"},
    ("it_act","67"): {"common_name": "Publishing Obscene Content", "subcategory": "cyber,offence"},
    ("rti",  "6"):   {"common_name": "RTI Application",            "subcategory": "information,application"},
    ("rti",  "8"):   {"common_name": "Exemptions from Disclosure", "subcategory": "information,exemption"},
}


# ═════════════════════════════════════════════════════════════════════════════
# HELPER FUNCTIONS
# ═════════════════════════════════════════════════════════════════════════════

def load_all_sections() -> list[dict]:
    """Walk data_ingestion/storage/acts/ and read every JSON file."""
    sections = []
    if not ACTS_DIR.exists():
        log.error(f"Acts directory not found: {ACTS_DIR}")
        return sections

    for folder in sorted(ACTS_DIR.iterdir()):
        if not folder.is_dir():
            continue
        folder_name = folder.name
        meta = ACT_META.get(folder_name)
        if not meta:
            log.warning(f"No ACT_META entry for folder '{folder_name}', skipping")
            continue

        for json_file in sorted(folder.glob("*.json")):
            try:
                data = json.loads(json_file.read_text(encoding="utf-8"))
                section_num = str(data.get("section", "")).strip()
                extra = SECTION_EXTRA.get((folder_name, section_num), {})
                sections.append({
                    "folder":      folder_name,
                    "act_key":     meta["short_name"],
                    "act_name":    meta["name"],
                    "act_year":    meta["year"],
                    "number":      section_num,
                    "title":       data.get("title", ""),
                    "content":     data.get("content", ""),
                    "source_url":  data.get("source_url", ""),
                    "common_name": extra.get("common_name", ""),
                    "subcategory": extra.get("subcategory", ""),
                })
            except Exception as e:
                log.warning(f"Failed to read {json_file}: {e}")

    log.info(f"Loaded {len(sections)} sections from {ACTS_DIR}")
    return sections


def connect_neo4j():
    """Connect to Neo4j and return driver. Exits on failure."""
    try:
        from neo4j import GraphDatabase
    except ImportError:
        log.error("neo4j package not installed. Run: pip install neo4j")
        sys.exit(1)

    if not NEO4J_URI:
        log.error("NEO4J_URI is not set in ai_engine/.env")
        sys.exit(1)
    if not NEO4J_PASSWORD:
        log.error("NEO4J_PASSWORD is not set in ai_engine/.env")
        sys.exit(1)

    log.info(f"Connecting to Neo4j: {NEO4J_URI}")
    log.info(f"Username: {NEO4J_USERNAME}")

    try:
        driver = GraphDatabase.driver(
            NEO4J_URI,
            auth=(NEO4J_USERNAME, NEO4J_PASSWORD),
            max_connection_pool_size=10,
            connection_timeout=30,
        )
        driver.verify_connectivity()
        log.info("✅ Connected to Neo4j successfully!")
        return driver
    except Exception as e:
        log.error(f"❌ Failed to connect to Neo4j: {e}")
        log.error("")
        log.error("Troubleshooting:")
        log.error("  1. Check your NEO4J_URI, NEO4J_USERNAME, NEO4J_PASSWORD in ai_engine/.env")
        log.error("  2. Ensure the AuraDB instance is Running (not Paused/Deleted)")
        log.error("  3. Check your internet connection")
        sys.exit(1)


def run(driver, query: str, params: dict = None):
    """Execute a Cypher query."""
    with driver.session() as session:
        result = session.run(query, params or {})
        return [r.data() for r in result]


# ═════════════════════════════════════════════════════════════════════════════
# SETUP STEPS
# ═════════════════════════════════════════════════════════════════════════════

def step_clear_database(driver):
    """Remove all existing nodes and relationships."""
    log.info("🗑️  Step 1: Clearing existing database...")
    run(driver, "MATCH (n) DETACH DELETE n")
    result = run(driver, "MATCH (n) RETURN count(n) AS remaining")
    remaining = result[0]["remaining"] if result else 0
    log.info(f"   Database cleared. Remaining nodes: {remaining}")


def step_create_constraints_and_indexes(driver):
    """Create constraints and indexes for performance."""
    log.info("📐 Step 2: Creating constraints and indexes...")

    constraints = [
        "CREATE CONSTRAINT act_short_name IF NOT EXISTS FOR (a:Act) REQUIRE a.short_name IS UNIQUE",
        "CREATE CONSTRAINT section_id IF NOT EXISTS FOR (s:Section) REQUIRE s.id IS UNIQUE",
        "CREATE CONSTRAINT case_citation IF NOT EXISTS FOR (c:Case) REQUIRE c.citation IS UNIQUE",
        "CREATE CONSTRAINT principle_name IF NOT EXISTS FOR (p:Principle) REQUIRE p.name IS UNIQUE",
    ]

    indexes = [
        "CREATE INDEX section_number IF NOT EXISTS FOR (s:Section) ON (s.number)",
        "CREATE INDEX section_act_key IF NOT EXISTS FOR (s:Section) ON (s.act_short_name)",
        "CREATE INDEX section_subcategory IF NOT EXISTS FOR (s:Section) ON (s.subcategory)",
    ]

    for stmt in constraints + indexes:
        try:
            run(driver, stmt)
        except Exception as e:
            log.debug(f"   Constraint/index note: {e}")

    log.info("   ✅ Constraints and indexes created")


def step_load_acts_and_sections(driver, sections: list[dict]):
    """Create Act nodes and Section nodes with HAS_SECTION relationships."""
    log.info(f"📚 Step 3: Loading {len(sections)} sections into Neo4j...")

    # Create Act nodes first
    acts_seen = set()
    for s in sections:
        if s["act_key"] not in acts_seen:
            acts_seen.add(s["act_key"])
            act_meta = next((v for v in ACT_META.values() if v["short_name"] == s["act_key"]), {})
            run(driver, """
                MERGE (a:Act {short_name: $short_name})
                SET a.name = $name,
                    a.year = $year
            """, {
                "short_name": s["act_key"],
                "name": s["act_name"],
                "year": s["act_year"],
            })

    log.info(f"   Created {len(acts_seen)} Act nodes: {sorted(acts_seen)}")

    # Create Section nodes with HAS_SECTION relationships in batches
    batch_size = 50
    total = len(sections)
    created = 0

    for i in range(0, total, batch_size):
        batch = sections[i:i + batch_size]
        for s in batch:
            section_id = f"{s['act_key']}_{s['number']}"
            run(driver, """
                MERGE (s:Section {id: $id})
                SET s.number        = $number,
                    s.title         = $title,
                    s.content       = $content,
                    s.act_short_name= $act_key,
                    s.act_name      = $act_name,
                    s.common_name   = $common_name,
                    s.subcategory   = $subcategory,
                    s.source_url    = $source_url
                WITH s
                MATCH (a:Act {short_name: $act_key})
                MERGE (a)-[:HAS_SECTION]->(s)
            """, {
                "id":          section_id,
                "number":      s["number"],
                "title":       s["title"],
                "content":     s["content"],
                "act_key":     s["act_key"],
                "act_name":    s["act_name"],
                "common_name": s["common_name"],
                "subcategory": s["subcategory"],
                "source_url":  s["source_url"],
            })
            created += 1

        log.info(f"   Progress: {min(i + batch_size, total)}/{total} sections")

    log.info(f"   ✅ {created} sections loaded with HAS_SECTION relationships")


def step_create_cross_references(driver, sections: list[dict]):
    """Create RELATED_TO relationships between cross-referenced sections."""
    log.info(f"🔗 Step 4: Creating {len(CROSS_REFERENCES)} cross-reference relationships...")

    # Build lookup: (act_short_name, section_number) → bool
    section_lookup = {
        (s["act_key"], s["number"]): True for s in sections
    }

    created = 0
    skipped = 0

    for (src_num, src_folder), (tgt_num, tgt_folder) in CROSS_REFERENCES:
        src_key = ACT_META.get(src_folder, {}).get("short_name", "")
        tgt_key = ACT_META.get(tgt_folder, {}).get("short_name", "")

        if not section_lookup.get((src_key, src_num)):
            log.debug(f"   Skip RELATED_TO: source {src_key}§{src_num} not in DB")
            skipped += 1
            continue
        if not section_lookup.get((tgt_key, tgt_num)):
            log.debug(f"   Skip RELATED_TO: target {tgt_key}§{tgt_num} not in DB")
            skipped += 1
            continue

        run(driver, """
            MATCH (src:Section {number: $src_num, act_short_name: $src_key})
            MATCH (tgt:Section {number: $tgt_num, act_short_name: $tgt_key})
            MERGE (src)-[:RELATED_TO]->(tgt)
        """, {
            "src_num": src_num, "src_key": src_key,
            "tgt_num": tgt_num, "tgt_key": tgt_key,
        })
        created += 1
        log.info(f"   ✅ {src_key}§{src_num} → RELATED_TO → {tgt_key}§{tgt_num}")

    log.info(f"   Created: {created} relationships | Skipped (section missing): {skipped}")


def step_create_landmark_cases(driver, sections: list[dict]):
    """Create Case nodes and INTERPRETS relationships."""
    log.info(f"⚖️  Step 5: Loading {len(LANDMARK_CASES)} landmark cases...")

    section_lookup = {(s["act_key"], s["number"]): True for s in sections}
    created = 0

    for case in LANDMARK_CASES:
        act_key = ACT_META.get(case["act"], {}).get("short_name", "")
        section_num = case["section"]

        # Create case node
        run(driver, """
            MERGE (c:Case {citation: $citation})
            SET c.name   = $name,
                c.year   = $year,
                c.court  = $court
        """, {
            "citation": case["citation"],
            "name":     case["name"],
            "year":     case["year"],
            "court":    case["court"],
        })

        # Create INTERPRETS relationship if section exists
        if section_lookup.get((act_key, section_num)):
            run(driver, """
                MATCH (c:Case {citation: $citation})
                MATCH (s:Section {number: $section, act_short_name: $act_key})
                MERGE (c)-[:INTERPRETS]->(s)
            """, {
                "citation":    case["citation"],
                "section":     section_num,
                "act_key":     act_key,
            })
            log.info(f"   ✅ Case: {case['name'][:55]} → INTERPRETS → {act_key}§{section_num}")
            created += 1
        else:
            log.warning(f"   ⚠️  Section {act_key}§{section_num} not found for case: {case['name'][:40]}")

    log.info(f"   Created {created} INTERPRETS relationships")


def step_create_principles(driver, sections: list[dict]):
    """Create Principle nodes and DEFINES relationships."""
    log.info(f"💡 Step 6: Loading {len(PRINCIPLES)} legal principles...")

    section_lookup = {(s["act_key"], s["number"]): True for s in sections}
    created = 0

    for p in PRINCIPLES:
        act_key = ACT_META.get(p["act"], {}).get("short_name", "")
        section_num = p["section"]

        # Create Principle node
        run(driver, """
            MERGE (pr:Principle {name: $name})
            SET pr.description = $description
        """, {
            "name":        p["name"],
            "description": p["description"],
        })

        # Link from case if any landmark case establishes this principle
        matching_cases = [
            c for c in LANDMARK_CASES
            if c.get("principle") == p["name"]
        ]
        for case in matching_cases:
            run(driver, """
                MATCH (c:Case {citation: $citation})
                MATCH (pr:Principle {name: $principle})
                MERGE (c)-[:ESTABLISHES]->(pr)
            """, {"citation": case["citation"], "principle": p["name"]})

        # Link section → Principle
        if section_lookup.get((act_key, section_num)):
            run(driver, """
                MATCH (s:Section {number: $section, act_short_name: $act_key})
                MATCH (pr:Principle {name: $name})
                MERGE (s)-[:DEFINES]->(pr)
            """, {
                "section": section_num,
                "act_key": act_key,
                "name":    p["name"],
            })
            log.info(f"   ✅ {act_key}§{section_num} → DEFINES → {p['name']}")
            created += 1

    log.info(f"   Created {created} DEFINES relationships")


def step_verify(driver):
    """Run verification queries and print summary."""
    log.info("")
    log.info("=" * 65)
    log.info("  VERIFICATION SUMMARY")
    log.info("=" * 65)

    # Node counts
    counts = run(driver, """
        MATCH (a:Act)     WITH count(a) AS acts
        MATCH (s:Section) WITH acts, count(s) AS sections
        MATCH (c:Case)    WITH acts, sections, count(c) AS cases
        MATCH (p:Principle) RETURN acts, sections, cases, count(p) AS principles
    """)
    if counts:
        c = counts[0]
        log.info(f"  📊 Acts:       {c['acts']}")
        log.info(f"  📊 Sections:   {c['sections']}")
        log.info(f"  📊 Cases:      {c['cases']}")
        log.info(f"  📊 Principles: {c['principles']}")

    # Relationship counts
    rels = run(driver, """
        MATCH ()-[r:HAS_SECTION]->()   WITH count(r) AS has_section
        MATCH ()-[r:RELATED_TO]->()    WITH has_section, count(r) AS related_to
        MATCH ()-[r:INTERPRETS]->()    WITH has_section, related_to, count(r) AS interprets
        MATCH ()-[r:DEFINES]->()       WITH has_section, related_to, interprets, count(r) AS defines
        MATCH ()-[r:ESTABLISHES]->()   RETURN has_section, related_to, interprets, defines, count(r) AS establishes
    """)
    if rels:
        r = rels[0]
        log.info(f"  🔗 HAS_SECTION:  {r['has_section']}")
        log.info(f"  🔗 RELATED_TO:   {r['related_to']}")
        log.info(f"  🔗 INTERPRETS:   {r['interprets']}")
        log.info(f"  🔗 DEFINES:      {r['defines']}")
        log.info(f"  🔗 ESTABLISHES:  {r['establishes']}")

    # Acts breakdown
    log.info("")
    log.info("  📋 Acts breakdown:")
    acts = run(driver, """
        MATCH (a:Act)-[:HAS_SECTION]->(s:Section)
        RETURN a.short_name AS act, a.name AS name, count(s) AS sections
        ORDER BY sections DESC
    """)
    for a in acts:
        log.info(f"     {a['act']:12s} | {a['sections']:3d} sections | {a['name']}")

    # Test query: S438 related sections
    log.info("")
    log.info("  🔍 Test: Sections related to CrPC §438 (Anticipatory Bail):")
    related = run(driver, """
        MATCH (s:Section {number: '438', act_short_name: 'CrPC'})-[:RELATED_TO]->(r:Section)
        RETURN r.number AS num, r.title AS title, r.act_short_name AS act
    """)
    if related:
        for r in related:
            log.info(f"     → {r['act']} §{r['num']}: {r['title']}")
    else:
        log.info("     (none found)")

    # Test query: Cases interpreting S438
    log.info("")
    log.info("  🔍 Test: Cases interpreting CrPC §438:")
    cases = run(driver, """
        MATCH (c:Case)-[:INTERPRETS]->(s:Section {number: '438', act_short_name: 'CrPC'})
        RETURN c.name AS case_name, c.year AS year, c.citation AS citation
        ORDER BY c.year
    """)
    if cases:
        for c in cases:
            log.info(f"     → {c['case_name']} ({c['year']}) — {c['citation']}")
    else:
        log.info("     (none found)")

    log.info("")
    log.info("=" * 65)
    log.info("  ✅ Neo4j Knowledge Graph setup COMPLETE!")
    log.info("")
    log.info("  Next steps:")
    log.info("  1. Test connection: python verify_neo4j_data.py")
    log.info("  2. Run graph demo:  python demo_graph_queries.py")
    log.info("  3. Start AI Engine: python run.py")
    log.info("=" * 65)


# ═════════════════════════════════════════════════════════════════════════════
# MAIN
# ═════════════════════════════════════════════════════════════════════════════

def main():
    print()
    print("=" * 65)
    print("  Legal Research Assistant — Neo4j Graph Setup")
    print("=" * 65)
    print(f"  URI:      {NEO4J_URI}")
    print(f"  Username: {NEO4J_USERNAME}")
    print(f"  Acts dir: {ACTS_DIR}")
    print("=" * 65)
    print()

    # 0. Load all section JSON files
    sections = load_all_sections()
    if not sections:
        log.error("No sections loaded. Check ACTS_DIR path.")
        sys.exit(1)

    # 1. Connect
    driver = connect_neo4j()

    try:
        # 2. Clear existing data
        step_clear_database(driver)

        # 3. Constraints & indexes
        step_create_constraints_and_indexes(driver)

        # 4. Acts + Sections + HAS_SECTION
        step_load_acts_and_sections(driver, sections)

        # 5. RELATED_TO cross-references
        step_create_cross_references(driver, sections)

        # 6. Landmark Cases + INTERPRETS
        step_create_landmark_cases(driver, sections)

        # 7. Principles + DEFINES + ESTABLISHES
        step_create_principles(driver, sections)

        # 8. Verify
        step_verify(driver)

    except KeyboardInterrupt:
        log.warning("Script interrupted by user.")
    except Exception as e:
        log.error(f"❌ Unexpected error: {e}", exc_info=True)
        sys.exit(1)
    finally:
        driver.close()
        log.info("Neo4j driver closed.")


if __name__ == "__main__":
    main()
