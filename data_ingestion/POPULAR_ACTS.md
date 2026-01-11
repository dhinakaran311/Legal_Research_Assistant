# Popular Indian Acts - Configuration

This document lists all the popular Indian acts configured for scraping and loading into ChromaDB.

## Configured Acts

### 1. **CrPC** - Code of Criminal Procedure, 1973
- **Category:** Criminal Procedure
- **Sections:** 10 popular sections (41, 41A, 41D, 50, 50A, 154, 156, 436, 437, 438)
- **Topics:** Arrest, bail, investigation, police powers

### 2. **IPC** - Indian Penal Code, 1860
- **Category:** Criminal Law
- **Sections:** 10 popular sections (300, 302, 304, 307, 376, 377, 420, 498A, 499, 506)
- **Topics:** Murder, rape, cheating, defamation, criminal intimidation

### 3. **CPC** - Code of Civil Procedure, 1908
- **Category:** Civil Procedure
- **Sections:** 9 popular sections (9, 10, 11, 20, 100, 104, 115, 144, 148)
- **Topics:** Jurisdiction, res judicata, appeals, revision, restitution

### 4. **Evidence Act** - Indian Evidence Act, 1872
- **Category:** Evidence Law
- **Sections:** 10 popular sections (3, 56, 57, 101, 102, 103, 115, 118, 122, 133)
- **Topics:** Burden of proof, estoppel, witnesses, judicial notice

### 5. **Contract Act** - Indian Contract Act, 1872
- **Category:** Commercial Law
- **Sections:** 9 popular sections (2, 10, 11, 14, 15, 23, 56, 65, 73)
- **Topics:** Formation, capacity, consent, coercion, damages

### 6. **Companies Act** - Companies Act, 2013
- **Category:** Corporate Law
- **Sections:** 7 popular sections (2, 12, 149, 166, 188, 201, 241)
- **Topics:** Incorporation, directors, meetings, related party transactions

### 7. **Constitution** - Constitution of India, 1950
- **Category:** Constitutional Law
- **Sections:** 9 popular articles (12, 13, 14, 15, 19, 21, 32, 226, 300A)
- **Topics:** Fundamental rights, equality, freedom of speech, writs

## Total Sections

- **Total Acts:** 7
- **Total Sections:** 64 popular sections

## Usage

### Scrape All Acts

```bash
cd data_ingestion
python sources/multi_act_scraper.py
```

### Scrape Specific Acts

```bash
python sources/multi_act_scraper.py --acts ipc crpc cpc
```

### List Configured Acts

```bash
python sources/multi_act_scraper.py --list
```

### Load All Acts to ChromaDB

```bash
python loaders/load_multi_act_data.py
```

### Load Specific Acts to ChromaDB

```bash
python loaders/load_multi_act_data.py --acts ipc crpc cpc
```

## Storage Structure

```
data_ingestion/storage/acts/
├── crpc/
│   ├── section_41.json
│   ├── section_41A.json
│   └── ...
├── ipc/
│   ├── section_300.json
│   ├── section_302.json
│   └── ...
├── cpc/
│   ├── section_9.json
│   ├── section_10.json
│   └── ...
├── evidence/
│   ├── section_3.json
│   └── ...
├── contract/
│   ├── section_2.json
│   └── ...
├── companies/
│   ├── section_2.json
│   └── ...
└── constitution/
    ├── section_12.json
    └── ...
```

## ChromaDB Document IDs

Each document in ChromaDB has a unique ID format:

- `crpc_section_438`
- `ipc_section_302`
- `cpc_section_9`
- `evidence_section_101`
- `contract_section_10`
- `companies_section_149`
- `constitution_section_21`

## Adding More Acts

To add more acts or sections:

1. Edit `config/acts_config.py`
2. Add act configuration to `ACT_CONFIGS`
3. Add sections to `ACT_SECTIONS`
4. Add subcategory mapping to `SUBCATEGORY_MAP`
5. Run scraper and loader

## Notes

- **Act IDs:** May need verification on IndiaCode website
- **URLs:** Based on expected IndiaCode URL pattern
- **Rate Limiting:** 2 seconds between section requests
- **Subcategories:** Organized for better search and filtering
