# Data Ingestion System

This module handles scraping, cleaning, and loading legal documents into the vector database (ChromaDB).

## Overview

The data ingestion pipeline:
1. **Scrapes** legal documents from public sources (IndiaCode)
2. **Stores** documents as structured JSON files
3. **Cleans** text for better embeddings
4. **Loads** documents into ChromaDB for semantic search

## Quick Start

### Prerequisites

Install dependencies:
```bash
cd data_ingestion
pip install -r requirements.txt
```

### Scrape Multiple Acts (Recommended)

**Scrape all popular acts:**
```bash
python sources/multi_act_scraper.py
```

**Scrape specific acts:**
```bash
python sources/multi_act_scraper.py --acts ipc crpc cpc evidence contract
```

**List configured acts:**
```bash
python sources/multi_act_scraper.py --list
```

This will:
- Scrape sections from multiple acts (IPC, CrPC, CPC, Evidence Act, Contract Act, Companies Act, Constitution)
- Save JSON files to `storage/acts/{act_key}/`
- Wait 2 seconds between requests (rate limiting)

### Load All Acts into ChromaDB

```bash
python loaders/load_multi_act_data.py
```

**Load specific acts:**
```bash
python loaders/load_multi_act_data.py --acts ipc crpc cpc
```

This will:
- Load all JSON files from all acts (or specified acts)
- Clean text using text_cleaner module
- Add documents to ChromaDB collection
- Skip documents that already exist

### Legacy: Scrape Only CrPC Sections

```bash
python sources/indiacode_scraper.py
```

### Legacy: Load Only CrPC into ChromaDB

```bash
python loaders/load_crpc_data.py
```

### Test Everything

```bash
python test_crpc_scraper.py
```

This will:
- Validate JSON structure
- Test text cleaning
- Verify ChromaDB integration

## Structure

```
data_ingestion/
├── config/
│   ├── __init__.py
│   └── acts_config.py             # Configuration for multiple acts
├── sources/
│   ├── indiacode_scraper.py       # Legacy: Scrapes only CrPC sections
│   ├── multi_act_scraper.py       # NEW: Scrapes multiple acts
│   ├── indiankanoon_scraper.py    # (Future) Scrapes judgments
│   └── lawcommission_downloader.py # (Future) Downloads reports
├── preprocess/
│   └── text_cleaner.py            # Text cleaning functions
├── loaders/
│   ├── pdf_parser.py              # PDF parsing (for reports)
│   ├── load_crpc_data.py          # Legacy: Loads only CrPC JSON to ChromaDB
│   └── load_multi_act_data.py     # NEW: Loads multiple acts to ChromaDB
├── storage/
│   ├── acts/
│   │   ├── crpc/                  # CrPC section JSON files
│   │   ├── ipc/                   # IPC section JSON files
│   │   ├── cpc/                   # CPC section JSON files
│   │   ├── evidence/              # Evidence Act JSON files
│   │   ├── contract/              # Contract Act JSON files
│   │   ├── companies/             # Companies Act JSON files
│   │   └── constitution/          # Constitution JSON files
│   ├── judgments/                 # (Future) Court judgments
│   └── reports/                   # (Future) Law Commission reports
├── test_crpc_scraper.py           # Test suite
└── POPULAR_ACTS.md                # Documentation for popular acts
```

## JSON Format

Each section is stored as a JSON file with this structure:

```json
{
  "act": "Code of Criminal Procedure, 1973",
  "section": "438",
  "title": "Direction for grant of bail to person apprehending arrest",
  "content": "Full section text here...",
  "source": "IndiaCode",
  "source_url": "https://www.indiacode.nic.in/...",
  "last_updated": "1974"
}
```

## ChromaDB Integration

Documents are loaded with metadata:

```python
metadata = {
    "act": "CrPC",
    "section": "438",
    "source": "IndiaCode",
    "category": "criminal_procedure",
    "subcategory": "bail",
    "title": "...",
    "source_url": "...",
    "last_updated": "..."
}
```

Document ID format: `{act_key}_section_{section_number}`

Examples:
- `crpc_section_438`
- `ipc_section_302`
- `cpc_section_9`
- `evidence_section_101`

## Usage Examples

### Scrape Single Section (for testing)

Edit `indiacode_scraper.py` and modify `CRPC_SECTION_URLS` to include only one URL for testing.

### Clean Text Manually

```python
from preprocess.text_cleaner import clean_legal_text

raw_text = "..."
cleaned = clean_legal_text(raw_text, section_number="438")
```

### Check What's in ChromaDB

```bash
cd ../ai_engine
python check_data.py
```

## Troubleshooting

### Scraper fails to extract content

- Check if IndiaCode HTML structure has changed
- Inspect page source and update selectors in `extract_section_content()`
- Verify URLs are correct

### Text cleaning removes important content

- Adjust `text_cleaner.py` cleaning functions
- Test with sample text before bulk processing

### ChromaDB loading fails

- Verify `ai_engine/.env` is configured
- Check ChromaDB path is correct
- Ensure ChromaDB is accessible

### Import errors

- Make sure Python paths are set correctly
- Verify all dependencies are installed
- Check `__init__.py` files exist in each module

## Popular Acts

The system now supports scraping and loading from **7 popular Indian acts**:

1. **CrPC** - Code of Criminal Procedure (10 sections)
2. **IPC** - Indian Penal Code (10 sections)
3. **CPC** - Code of Civil Procedure (9 sections)
4. **Evidence Act** - Indian Evidence Act (10 sections)
5. **Contract Act** - Indian Contract Act (9 sections)
6. **Companies Act** - Companies Act 2013 (7 sections)
7. **Constitution** - Constitution of India (9 sections)

**Total: 64 popular sections across 7 acts**

See `POPULAR_ACTS.md` for detailed information about each act and their sections.

## Next Steps

1. ✅ Multiple acts support (COMPLETED)
2. Expand sections for existing acts
3. Add more acts (GST Act, Income Tax Act, etc.)
4. Scrape judgments from Indian Kanoon
5. Download Law Commission reports
6. Create Neo4j graph relationships
