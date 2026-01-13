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
    },
    # High Priority Acts
    "mva": {
        "act_id": "AC_CEN_5_23_00059_19881114_1517807320172",
        "year": 1988,
        "full_name": "Motor Vehicles Act, 1988",
        "short_name": "MVA",
        "category": "traffic_law",
        "base_url_pattern": "https://www.indiacode.nic.in/show-data?actid={act_id}&orderno={section}"
    },
    "ita": {
        "act_id": "AC_CEN_5_23_00043_19610413_1517807320172",
        "year": 1961,
        "full_name": "Income Tax Act, 1961",
        "short_name": "ITA",
        "category": "tax_law",
        "base_url_pattern": "https://www.indiacode.nic.in/show-data?actid={act_id}&orderno={section}"
    },
    "gst": {
        "act_id": "AC_CEN_5_23_00012_20170329_1517807320172",
        "year": 2017,
        "full_name": "Central Goods and Services Tax Act, 2017",
        "short_name": "GST",
        "category": "tax_law",
        "base_url_pattern": "https://www.indiacode.nic.in/show-data?actid={act_id}&orderno={section}"
    },
    "cpa": {
        "act_id": "AC_CEN_5_23_00009_20190809_1517807320172",
        "year": 2019,
        "full_name": "Consumer Protection Act, 2019",
        "short_name": "CPA",
        "category": "consumer_law",
        "base_url_pattern": "https://www.indiacode.nic.in/show-data?actid={act_id}&orderno={section}"
    },
    "rpa": {
        "act_id": "AC_CEN_5_23_00043_19510517_1517807320172",
        "year": 1951,
        "full_name": "Representation of the People Act, 1951",
        "short_name": "RPA",
        "category": "election_law",
        "base_url_pattern": "https://www.indiacode.nic.in/show-data?actid={act_id}&orderno={section}"
    },
    "it_act": {
        "act_id": "AC_CEN_5_23_00021_20000609_1517807320172",
        "year": 2000,
        "full_name": "Information Technology Act, 2000",
        "short_name": "IT Act",
        "category": "cyber_law",
        "base_url_pattern": "https://www.indiacode.nic.in/show-data?actid={act_id}&orderno={section}"
    },
    "rti": {
        "act_id": "AC_CEN_5_23_00022_20050615_1517807320172",
        "year": 2005,
        "full_name": "Right to Information Act, 2005",
        "short_name": "RTI",
        "category": "administrative_law",
        "base_url_pattern": "https://www.indiacode.nic.in/show-data?actid={act_id}&orderno={section}"
    },
    # Medium Priority Acts
    "tpa": {
        "act_id": "AC_CEN_5_23_00004_18820317_1517807320172",
        "year": 1882,
        "full_name": "Transfer of Property Act, 1882",
        "short_name": "TPA",
        "category": "property_law",
        "base_url_pattern": "https://www.indiacode.nic.in/show-data?actid={act_id}&orderno={section}"
    },
    "nia": {
        "act_id": "AC_CEN_5_23_00026_18810309_1517807320172",
        "year": 1881,
        "full_name": "Negotiable Instruments Act, 1881",
        "short_name": "NIA",
        "category": "commercial_law",
        "base_url_pattern": "https://www.indiacode.nic.in/show-data?actid={act_id}&orderno={section}"
    },
    "ida": {
        "act_id": "AC_CEN_5_23_00014_19470401_1517807320172",
        "year": 1947,
        "full_name": "Industrial Disputes Act, 1947",
        "short_name": "IDA",
        "category": "labor_law",
        "base_url_pattern": "https://www.indiacode.nic.in/show-data?actid={act_id}&orderno={section}"
    },
    "hindu_marriage": {
        "act_id": "AC_CEN_5_23_00025_19550518_1517807320172",
        "year": 1955,
        "full_name": "Hindu Marriage Act, 1955",
        "short_name": "HMA",
        "category": "family_law",
        "base_url_pattern": "https://www.indiacode.nic.in/show-data?actid={act_id}&orderno={section}"
    },
    "fssa": {
        "act_id": "AC_CEN_5_23_00034_20060823_1517807320172",
        "year": 2006,
        "full_name": "Food Safety and Standards Act, 2006",
        "short_name": "FSSA",
        "category": "food_law",
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
    },
    # High Priority Acts - Sections
    "mva": {
        "3": "Necessity for driving licence",
        "4": "Age limit for driving licence",
        "5": "Authority to issue driving licence",
        "19": "Disqualification for holding or obtaining driving licence",
        "20": "Power of Court to disqualify",
        "130": "Duty of driver to stop in certain cases",
        "177": "General provision for punishment of offences",
        "184": "Dangerous driving",
        "185": "Driving by a drunken person or by a person under the influence of drugs",
        "196": "Driving uninsured vehicle"
    },
    "ita": {
        "2": "Definitions",
        "4": "Charge of income-tax",
        "5": "Scope of total income",
        "10": "Incomes not included in total income",
        "24": "Deductions from income from house property",
        "80C": "Deduction in respect of life insurance premia, deferred annuity, contributions to provident fund, subscription to certain equity shares or debentures, etc.",
        "80D": "Deduction in respect of health insurance premia",
        "139": "Return of income",
        "143": "Assessment",
        "147": "Income escaping assessment"
    },
    "gst": {
        "2": "Definitions",
        "7": "Scope of supply",
        "9": "Levy and collection",
        "16": "Eligibility and conditions for taking input tax credit",
        "17": "Apportionment of credit and blocked credits",
        "22": "Persons liable for registration",
        "24": "Compulsory registration in certain cases",
        "29": "Cancellation or suspension of registration",
        "37": "Furnishing details of outward supplies",
        "39": "Furnishing of returns"
    },
    "cpa": {
        "2": "Definitions",
        "10": "Establishment of Consumer Protection Councils",
        "18": "Powers and functions of Central Authority",
        "27": "Penalty for non-compliance of order of Central Authority",
        "35": "Jurisdiction of District Commission",
        "38": "Jurisdiction of State Commission",
        "39": "Jurisdiction of National Commission",
        "47": "Appeal against order passed under section 27",
        "49": "Appeal against order of State Commission",
        "52": "Appeal against order of National Commission"
    },
    "rpa": {
        "8": "Disqualification on conviction for certain offences",
        "33": "Presentation of nomination papers and requirements for a valid nomination",
        "36": "Scrutiny of nominations",
        "62": "Right to vote",
        "77": "Account of election expenses and maximum thereof",
        "123": "Corrupt practices",
        "125A": "Penalty for filing false affidavit, etc.",
        "126": "Prohibition of public meetings during period of forty-eight hours ending with hour fixed for conclusion of poll",
        "127": "Distributing or exhibiting of election pamphlets, posters, etc.",
        "171": "Punishment for bribery"
    },
    "it_act": {
        "2": "Definitions",
        "43": "Penalty and compensation for damage to computer, computer system, etc.",
        "43A": "Compensation for failure to protect data",
        "66": "Computer related offences",
        "67": "Punishment for publishing or transmitting obscene material in electronic form",
        "69": "Power to issue directions for interception or monitoring or decryption of any information through any computer resource",
        "72": "Penalty for breach of confidentiality and privacy",
        "72A": "Punishment for disclosure of information in breach of lawful contract",
        "79": "Exemption from liability of intermediary in certain cases"
    },
    "rti": {
        "2": "Definitions",
        "4": "Obligations of public authorities",
        "6": "Request for obtaining information",
        "7": "Disposal of request",
        "8": "Exemption from disclosure of information",
        "18": "Powers and functions of Information Commission",
        "19": "Appeal",
        "20": "Penalties",
        "24": "Act not to apply to certain organisations"
    },
    # Medium Priority Acts - Sections
    "tpa": {
        "3": "Interpretation clause",
        "5": "Transfer of property defined",
        "6": "What may be transferred",
        "54": "Sale how made",
        "58": "Mortgage defined",
        "105": "Lease defined",
        "106": "Duration of certain leases in absence of written contract or local usage",
        "107": "Leases how made",
        "108": "Rights and liabilities of lessor and lessee",
        "122A": "Gift of existing movable property"
    },
    "nia": {
        "4": "Promissory note",
        "5": "Bill of exchange",
        "6": "Cheque",
        "13": "Negotiable instrument",
        "138": "Dishonour of cheque for insufficiency, etc., of funds in the account",
        "139": "Presumption in favour of holder",
        "140": "Defence which may not be allowed in any prosecution under section 138",
        "141": "Offences by companies",
        "142": "Cognizance of offences",
        "143": "Power of Court to try cases summarily"
    },
    "ida": {
        "2": "Definitions",
        "10": "Reference of disputes to Boards, Courts or Tribunals",
        "11A": "Powers of Labour Courts, Tribunals and National Tribunals to give appropriate relief in case of discharge or dismissal of workmen",
        "25": "Lay-off",
        "25F": "Conditions precedent to retrenchment of workmen",
        "25G": "Procedure for retrenchment",
        "25H": "Re-employment of retrenched workmen",
        "33": "Conditions of service, etc., to remain unchanged under certain circumstances during pendency of proceedings",
        "33A": "Special provision for adjudication as to whether conditions of service, etc., changed during pendency of proceeding"
    },
    "hindu_marriage": {
        "5": "Conditions for a Hindu marriage",
        "7": "Ceremonies for a Hindu marriage",
        "9": "Restitution of conjugal rights",
        "10": "Judicial separation",
        "11": "Void marriages",
        "12": "Voidable marriages",
        "13": "Divorce",
        "13A": "Alternate relief in divorce proceedings",
        "13B": "Divorce by mutual consent",
        "24": "Maintenance pendente lite and expenses of proceedings",
        "25": "Permanent alimony and maintenance"
    },
    "fssa": {
        "2": "Definitions",
        "3": "Establishment of Food Safety and Standards Authority of India",
        "16": "Functions of Food Authority",
        "23": "Food Safety and Standards Officer",
        "26": "Duties of Food Business Operator",
        "31": "Licensing and registration of food business",
        "50": "Penalty for selling food not of the nature or substance or quality demanded",
        "51": "General penalty",
        "59": "Punishment for unsafe food",
        "63": "Punishment for carrying out a business without licence"
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
    },
    # High Priority Acts - Subcategories
    "mva": {
        "3": "driving_licence",
        "4": "driving_licence",
        "5": "driving_licence",
        "19": "disqualification",
        "20": "disqualification",
        "130": "traffic_violations",
        "177": "penalties",
        "184": "dangerous_driving",
        "185": "drunk_driving",
        "196": "insurance"
    },
    "ita": {
        "2": "definitions",
        "4": "charge_of_tax",
        "5": "scope_of_income",
        "10": "exemptions",
        "24": "deductions",
        "80C": "deductions",
        "80D": "deductions",
        "139": "returns",
        "143": "assessment",
        "147": "reassessment"
    },
    "gst": {
        "2": "definitions",
        "7": "supply",
        "9": "levy",
        "16": "input_tax_credit",
        "17": "input_tax_credit",
        "22": "registration",
        "24": "registration",
        "29": "registration",
        "37": "returns",
        "39": "returns"
    },
    "cpa": {
        "2": "definitions",
        "10": "councils",
        "18": "authority_powers",
        "27": "penalties",
        "35": "jurisdiction",
        "38": "jurisdiction",
        "39": "jurisdiction",
        "47": "appeals",
        "49": "appeals",
        "52": "appeals"
    },
    "rpa": {
        "8": "disqualification",
        "33": "nomination",
        "36": "nomination",
        "62": "voting",
        "77": "election_expenses",
        "123": "corrupt_practices",
        "125A": "penalties",
        "126": "campaigning",
        "127": "campaigning",
        "171": "corrupt_practices"
    },
    "it_act": {
        "2": "definitions",
        "43": "penalties",
        "43A": "data_protection",
        "66": "cyber_crimes",
        "67": "obscenity",
        "69": "surveillance",
        "72": "privacy",
        "72A": "privacy",
        "79": "intermediary_liability"
    },
    "rti": {
        "2": "definitions",
        "4": "obligations",
        "6": "request",
        "7": "disposal",
        "8": "exemptions",
        "18": "commission_powers",
        "19": "appeals",
        "20": "penalties",
        "24": "exemptions"
    },
    # Medium Priority Acts - Subcategories
    "tpa": {
        "3": "definitions",
        "5": "transfer",
        "6": "transfer",
        "54": "sale",
        "58": "mortgage",
        "105": "lease",
        "106": "lease",
        "107": "lease",
        "108": "lease",
        "122A": "gift"
    },
    "nia": {
        "4": "promissory_note",
        "5": "bill_of_exchange",
        "6": "cheque",
        "13": "negotiable_instrument",
        "138": "dishonour",
        "139": "dishonour",
        "140": "dishonour",
        "141": "dishonour",
        "142": "dishonour",
        "143": "dishonour"
    },
    "ida": {
        "2": "definitions",
        "10": "disputes",
        "11A": "dismissal",
        "25": "lay_off",
        "25F": "retrenchment",
        "25G": "retrenchment",
        "25H": "retrenchment",
        "33": "conditions_of_service",
        "33A": "conditions_of_service"
    },
    "hindu_marriage": {
        "5": "marriage_conditions",
        "7": "marriage_ceremonies",
        "9": "conjugal_rights",
        "10": "separation",
        "11": "void_marriage",
        "12": "voidable_marriage",
        "13": "divorce",
        "13A": "divorce",
        "13B": "divorce",
        "24": "maintenance",
        "25": "maintenance"
    },
    "fssa": {
        "2": "definitions",
        "3": "authority",
        "16": "authority_functions",
        "23": "officers",
        "26": "obligations",
        "31": "licensing",
        "50": "penalties",
        "51": "penalties",
        "59": "punishment",
        "63": "punishment"
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
