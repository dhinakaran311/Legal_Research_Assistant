"""
Indian Acts Configuration
Popular acts with their sections to scrape from IndiaCode
"""
from typing import Dict, List

# Act configurations: Act ID, Year, Full Name, Short Name
ACT_CONFIGS = {
    "crpc": {
        "act_id": "AC_CEN_5_23_00037_19740325_1517807320172",
        "year": 1973,
        "full_name": "Code of Criminal Procedure, 1973",
        "short_name": "CrPC",
        "category": "criminal_procedure",
        "base_url_pattern": "https://www.indiacode.nic.in/show-data?actid={act_id}&orderno={section}"
    },
    "ipc": {
        "act_id": "AC_CEN_5_23_00045_18601201_1517807320172",
        "year": 1860,
        "full_name": "Indian Penal Code, 1860",
        "short_name": "IPC",
        "category": "criminal_law",
        "base_url_pattern": "https://www.indiacode.nic.in/show-data?actid={act_id}&orderno={section}"
    },
    "cpc": {
        "act_id": "AC_CEN_5_23_00004_19080321_1517807320172",
        "year": 1908,
        "full_name": "Code of Civil Procedure, 1908",
        "short_name": "CPC",
        "category": "civil_procedure",
        "base_url_pattern": "https://www.indiacode.nic.in/show-data?actid={act_id}&orderno={section}"
    },
    "evidence": {
        "act_id": "AC_CEN_5_23_00004_18720301_1517807320172",
        "year": 1872,
        "full_name": "Indian Evidence Act, 1872",
        "short_name": "Evidence",
        "category": "evidence_law",
        "base_url_pattern": "https://www.indiacode.nic.in/show-data?actid={act_id}&orderno={section}"
    },
    "contract": {
        "act_id": "AC_CEN_5_23_00009_18720425_1517807320172",
        "year": 1872,
        "full_name": "Indian Contract Act, 1872",
        "short_name": "Contract",
        "category": "commercial_law",
        "base_url_pattern": "https://www.indiacode.nic.in/show-data?actid={act_id}&orderno={section}"
    },
    "companies": {
        "act_id": "AC_CEN_5_23_00020_20130829_1517807320172",
        "year": 2013,
        "full_name": "Companies Act, 2013",
        "short_name": "Companies",
        "category": "corporate_law",
        "base_url_pattern": "https://www.indiacode.nic.in/show-data?actid={act_id}&orderno={section}"
    },
    "constitution": {
        "act_id": "CO_000000000019470",
        "year": 1950,
        "full_name": "Constitution of India, 1950",
        "short_name": "Constitution",
        "category": "constitutional_law",
        "base_url_pattern": "https://www.indiacode.nic.in/show-data?actid={act_id}&orderno={section}"
    }
}

# Popular sections to scrape for each act
ACT_SECTIONS = {
    "crpc": {
        "41": "When police may arrest without warrant",
        "41A": "Notice of appearance before police officer",
        "41D": "Right of arrested person to meet an advocate of his choice during interrogation",
        "50": "Person arrested to be informed of grounds of arrest and of right to bail",
        "50A": "Obligation of person making arrest to inform about the arrest, etc., to a nominated person",
        "154": "Information in cognizable cases",
        "156": "Police officer's power to investigate cognizable case",
        "436": "In what cases bail to be taken",
        "437": "When bail may be taken in case of non-bailable offence",
        "438": "Direction for grant of bail to person apprehending arrest"
    },
    "ipc": {
        "300": "Murder",
        "302": "Punishment for murder",
        "304": "Punishment for culpable homicide not amounting to murder",
        "307": "Attempt to murder",
        "376": "Punishment for rape",
        "377": "Unnatural offences",
        "420": "Cheating and dishonestly inducing delivery of property",
        "498A": "Husband or relative of husband of a woman subjecting her to cruelty",
        "499": "Defamation",
        "506": "Punishment for criminal intimidation"
    },
    "cpc": {
        "9": "Courts to try all civil suits unless barred",
        "10": "Stay of suit",
        "11": "Res judicata",
        "20": "Other suits to be instituted where defendants reside or cause of action arises",
        "100": "Second appeal",
        "104": "Orders from which appeal lies",
        "115": "Revision",
        "144": "Application for restitution",
        "148": "Power to award interest at any stage of decree"
    },
    "evidence": {
        "3": "Interpretation clause",
        "56": "Facts judicially noticeable need not be proved",
        "57": "Facts of which Court must take judicial notice",
        "101": "Burden of proof",
        "102": "On whom burden of proof lies",
        "103": "Burden of proof as to particular fact",
        "115": "Estoppel",
        "118": "Who may testify",
        "122": "Communications during marriage",
        "133": "Accomplice"
    },
    "contract": {
        "2": "Interpretation-clause",
        "10": "What agreements are contracts",
        "11": "Who are competent to contract",
        "14": "Free consent defined",
        "15": "Coercion defined",
        "23": "What considerations and objects are lawful, and what not",
        "56": "Agreement to do impossible act",
        "65": "Obligation of person who has received advantage under void agreement, or contract that becomes void",
        "73": "Compensation for loss or damage caused by breach of contract"
    },
    "companies": {
        "2": "Definitions",
        "12": "Incorporation of company",
        "149": "Company to have Board of Directors",
        "166": "Annual general meeting",
        "188": "Related party transactions",
        "201": "Compensation for loss of office",
        "241": "Application to Tribunal for relief in cases of oppression, etc."
    },
    "constitution": {
        "12": "Definition",
        "13": "Laws inconsistent with or in derogation of the fundamental rights",
        "14": "Equality before law",
        "15": "Prohibition of discrimination on grounds of religion, race, caste, sex or place of birth",
        "19": "Protection of certain rights regarding freedom of speech, etc.",
        "21": "Protection of life and personal liberty",
        "32": "Remedies for enforcement of rights conferred by this Part",
        "226": "Power of High Courts to issue certain writs",
        "300A": "Persons not to be deprived of property save by authority of law"
    }
}

# Subcategory mapping for better organization
SUBCATEGORY_MAP = {
    "crpc": {
        "41": "arrest_without_warrant",
        "41A": "arrest_procedures",
        "41D": "arrest_procedures",
        "50": "arrest_procedures",
        "50A": "arrest_procedures",
        "154": "information_to_police",
        "156": "investigation",
        "436": "bail",
        "437": "bail",
        "438": "bail"
    },
    "ipc": {
        "300": "offences_affecting_life",
        "302": "offences_affecting_life",
        "304": "offences_affecting_life",
        "307": "offences_affecting_life",
        "376": "sexual_offences",
        "377": "sexual_offences",
        "420": "cheating",
        "498A": "cruelty",
        "499": "defamation",
        "506": "criminal_intimidation"
    },
    "cpc": {
        "9": "jurisdiction",
        "10": "stay",
        "11": "res_judicata",
        "20": "jurisdiction",
        "100": "appeals",
        "104": "appeals",
        "115": "revision",
        "144": "restitution",
        "148": "interest"
    },
    "evidence": {
        "3": "definitions",
        "56": "judicial_notice",
        "57": "judicial_notice",
        "101": "burden_of_proof",
        "102": "burden_of_proof",
        "103": "burden_of_proof",
        "115": "estoppel",
        "118": "witnesses",
        "122": "privileged_communications",
        "133": "accomplice"
    },
    "contract": {
        "2": "definitions",
        "10": "formation",
        "11": "capacity",
        "14": "consent",
        "15": "coercion",
        "23": "consideration",
        "56": "impossibility",
        "65": "void_contracts",
        "73": "damages"
    },
    "companies": {
        "2": "definitions",
        "12": "incorporation",
        "149": "directors",
        "166": "meetings",
        "188": "related_party",
        "201": "compensation",
        "241": "oppression"
    },
    "constitution": {
        "12": "definitions",
        "13": "fundamental_rights",
        "14": "fundamental_rights",
        "15": "fundamental_rights",
        "19": "fundamental_rights",
        "21": "fundamental_rights",
        "32": "remedies",
        "226": "writs",
        "300A": "property_rights"
    }
}


def get_act_config(act_key: str) -> Dict:
    """Get configuration for a specific act"""
    return ACT_CONFIGS.get(act_key.lower(), {})


def get_act_sections(act_key: str) -> Dict[str, str]:
    """Get sections to scrape for a specific act"""
    return ACT_SECTIONS.get(act_key.lower(), {})


def get_act_url(act_key: str, section: str) -> str:
    """Generate URL for a specific act and section"""
    config = get_act_config(act_key)
    if not config:
        return ""
    
    act_id = config["act_id"]
    url_pattern = config["base_url_pattern"]
    return url_pattern.format(act_id=act_id, section=section)


def get_subcategory(act_key: str, section: str) -> str:
    """Get subcategory for a specific act and section"""
    subcategories = SUBCATEGORY_MAP.get(act_key.lower(), {})
    return subcategories.get(section, "general")


def list_all_acts() -> List[str]:
    """List all configured acts"""
    return list(ACT_CONFIGS.keys())


def get_total_sections_count() -> int:
    """Get total number of sections across all acts"""
    return sum(len(sections) for sections in ACT_SECTIONS.values())
