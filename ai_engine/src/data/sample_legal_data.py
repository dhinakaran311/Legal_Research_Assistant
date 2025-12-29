"""
Sample Legal Documents for Development and Testing
Contains hardcoded Indian legal provisions from IPC, CrPC, and Contract Act
"""

# Sample legal documents with metadata
SAMPLE_LEGAL_DOCUMENTS = [
    {
        "id": "ipc_section_302",
        "title": "IPC Section 302 - Punishment for Murder",
        "content": """Section 302 in The Indian Penal Code:
Punishment for murder.—Whoever commits murder shall be punished with death, or imprisonment for life, and shall also be liable to fine.

Key Elements:
1. Intentional killing of another person
2. With premeditation or malice aforethought
3. Punishable by death or life imprisonment
4. Additionally liable to fine

This is one of the most serious offenses under the Indian Penal Code. The prosecution must prove beyond reasonable doubt that the accused had the intention to cause death or knew that their actions would likely cause death.""",
        "metadata": {
            "source": "Indian Penal Code, 1860",
            "section": "302",
            "category": "criminal_law",
            "subcategory": "offences_affecting_life",
            "act": "IPC",
            "chapter": "XVI",
            "keywords": "murder, homicide, death penalty, life imprisonment"
        }
    },
    {
        "id": "ipc_section_420",
        "title": "IPC Section 420 - Cheating and Dishonestly Inducing Delivery of Property",
        "content": """Section 420 in The Indian Penal Code:
Cheating and dishonestly inducing delivery of property.—Whoever cheats and thereby dishonestly induces the person deceived to deliver any property to any person, or to make, alter or destroy the whole or any part of a valuable security, or anything which is signed or sealed, and which is capable of being converted into a valuable security, shall be punished with imprisonment of either description for a term which may extend to seven years, and shall also be liable to fine.

Key Elements:
1. Deception or fraudulent act
2. Dishonest inducement to deliver property
3. Victim must be deceived
4. Punishable up to 7 years imprisonment and fine

Common applications include fraud, forgery, and dishonest misrepresentation in commercial transactions.""",
        "metadata": {
            "source": "Indian Penal Code, 1860",
            "section": "420",
            "category": "criminal_law",
            "subcategory": "offences_relating_to_property",
            "act": "IPC",
            "chapter": "XVII",
            "keywords": "cheating, fraud, dishonesty, property, deception"
        }
    },
    {
        "id": "crpc_section_154",
        "title": "CrPC Section 154 - Information in Cognizable Cases",
        "content": """Section 154 in The Code Of Criminal Procedure, 1973:
Information in cognizable cases.—
(1) Every information relating to the commission of a cognizable offence, if given orally to an officer in charge of a police station, shall be reduced to writing by him or under his direction, and be read over to the informant; and every such information, whether given in writing or reduced to writing as aforesaid, shall be signed by the person giving it, and the substance thereof shall be entered in a book to be kept by such officer in such form as the State Government may prescribe in this behalf.

(2) A copy of the information as recorded under sub-section (1) shall be given forthwith, free of cost, to the informant.

(3) Any person aggrieved by a refusal on the part of an officer in charge of a police station to record the information referred to in sub-section (1) may send the substance of such information, in writing and by post, to the Superintendent of Police concerned who, if satisfied that such information discloses the commission of a cognizable offence, shall either investigate the case himself or direct an investigation to be made by any police officer subordinate to him.

This section is the foundation of criminal investigation in India, establishing the First Information Report (FIR) mechanism.""",
        "metadata": {
            "source": "Code of Criminal Procedure, 1973",
            "section": "154",
            "category": "criminal_procedure",
            "subcategory": "information_to_police",
            "act": "CrPC",
            "chapter": "XII",
            "keywords": "FIR, cognizable offence, police station, investigation, complaint"
        }
    },
    {
        "id": "contract_act_section_10",
        "title": "Indian Contract Act Section 10 - What Agreements are Contracts",
        "content": """Section 10 in The Indian Contract Act, 1872:
What agreements are contracts.—All agreements are contracts if they are made by the free consent of parties competent to contract, for a lawful consideration and with a lawful object, and are not hereby expressly declared to be void.

Essential Elements of a Valid Contract:
1. Free Consent: Agreement must be made with free and genuine consent of all parties
2. Competent Parties: Parties must be legally capable of entering into a contract (age of majority, sound mind, not disqualified by law)
3. Lawful Consideration: Something of value must be exchanged between parties
4. Lawful Object: The purpose of the contract must be legal
5. Not Expressly Void: The agreement must not fall under categories declared void by the Act

This section forms the foundation of contract law in India, establishing the basic requirements for an enforceable agreement.""",
        "metadata": {
            "source": "Indian Contract Act, 1872",
            "section": "10",
            "category": "contract_law",
            "subcategory": "formation_of_contract",
            "act": "Contract_Act",
            "chapter": "II",
            "keywords": "contract, agreement, consent, consideration, lawful object, competent parties"
        }
    },
    {
        "id": "contract_act_section_73",
        "title": "Indian Contract Act Section 73 - Compensation for Loss or Damage",
        "content": """Section 73 in The Indian Contract Act, 1872:
Compensation for loss or damage caused by breach of contract.—When a contract has been broken, the party who suffers by such breach is entitled to receive, from the party who has broken the contract, compensation for any loss or damage caused to him thereby, which naturally arose in the usual course of things from such breach, or which the parties knew, when they made the contract, to be likely to result from the breach of it.

Such compensation is not to be given for any remote and indirect loss or damage sustained by reason of the breach.

Principles of Damages:
1. Compensation for actual loss suffered
2. Loss must arise naturally from the breach
3. Loss must be foreseeable at the time of contract
4. Remote and indirect losses are not compensable
5. Damages aim to put the injured party in the position they would have been in had the contract been performed

This section establishes the principle of compensatory damages in contract law.""",
        "metadata": {
            "source": "Indian Contract Act, 1872",
            "section": "73",
            "category": "contract_law",
            "subcategory": "breach_and_remedies",
            "act": "Contract_Act",
            "chapter": "VI",
            "keywords": "breach of contract, damages, compensation, remedies, loss"
        }
    }
]


def get_sample_documents():
    """
    Get all sample legal documents
    
    Returns:
        List of dictionaries containing legal documents with metadata
    """
    return SAMPLE_LEGAL_DOCUMENTS


def get_documents_by_category(category: str):
    """
    Get sample documents filtered by category
    
    Args:
        category: Category to filter by (e.g., 'criminal_law', 'contract_law')
        
    Returns:
        List of matching documents
    """
    return [
        doc for doc in SAMPLE_LEGAL_DOCUMENTS 
        if doc['metadata']['category'] == category
    ]


def get_documents_by_act(act: str):
    """
    Get sample documents filtered by act
    
    Args:
        act: Act to filter by (e.g., 'IPC', 'CrPC', 'Contract_Act')
        
    Returns:
        List of matching documents
    """
    return [
        doc for doc in SAMPLE_LEGAL_DOCUMENTS 
        if doc['metadata']['act'] == act
    ]
