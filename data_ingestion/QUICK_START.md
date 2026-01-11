# Quick Start Guide - Multi-Act Scraping

## 🚀 Quick Start

### 1. Install Dependencies

```bash
cd data_ingestion
pip install -r requirements.txt
```

### 2. Scrape All Popular Acts

```bash
python sources/multi_act_scraper.py
```

This will scrape:
- **CrPC** (10 sections) - Criminal Procedure
- **IPC** (10 sections) - Indian Penal Code
- **CPC** (9 sections) - Civil Procedure
- **Evidence Act** (10 sections) - Evidence Law
- **Contract Act** (9 sections) - Commercial Law
- **Companies Act** (7 sections) - Corporate Law
- **Constitution** (9 sections) - Constitutional Law

**Total: 64 sections across 7 acts**

### 3. Load All Acts to ChromaDB

```bash
python loaders/load_multi_act_data.py
```

This will load all scraped sections into ChromaDB for semantic search.

## 📋 Advanced Usage

### Scrape Specific Acts Only

```bash
# Scrape only IPC and CrPC
python sources/multi_act_scraper.py --acts ipc crpc

# Scrape only Contract Act
python sources/multi_act_scraper.py --acts contract
```

### Load Specific Acts Only

```bash
# Load only IPC and CrPC
python loaders/load_multi_act_data.py --acts ipc crpc
```

### List Configured Acts

```bash
python sources/multi_act_scraper.py --list
```

## 📊 Act Codes

Use these act codes with `--acts` parameter:

- `crpc` - Code of Criminal Procedure
- `ipc` - Indian Penal Code
- `cpc` - Code of Civil Procedure
- `evidence` - Indian Evidence Act
- `contract` - Indian Contract Act
- `companies` - Companies Act
- `constitution` - Constitution of India

## 📁 Output Locations

Scraped JSON files are saved to:

```
data_ingestion/storage/acts/
├── crpc/
│   ├── section_41.json
│   ├── section_438.json
│   └── ...
├── ipc/
│   ├── section_302.json
│   └── ...
├── cpc/
│   └── ...
├── evidence/
│   └── ...
├── contract/
│   └── ...
├── companies/
│   └── ...
└── constitution/
    └── ...
```

## ⚠️ Important Notes

1. **URLs May Need Verification**: The IndiaCode URLs in the configuration are based on expected patterns. You may need to verify and update them.

2. **Rate Limiting**: The scraper waits 2 seconds between requests to be respectful to IndiaCode servers.

3. **Act IDs**: The Act IDs in `config/acts_config.py` may need to be updated based on actual IndiaCode structure.

4. **Verification**: Before scraping all acts, test with a single act first:
   ```bash
   python sources/multi_act_scraper.py --acts crpc
   ```

## 🔍 Verify Results

### Check JSON Files

```bash
# Count files
ls data_ingestion/storage/acts/crpc/*.json | wc -l

# View a file
cat data_ingestion/storage/acts/crpc/section_438.json
```

### Check ChromaDB

After loading, test search in the AI Engine or use the test script:

```bash
python test_crpc_scraper.py
```

## 📖 More Information

- **Full Documentation**: See `README.md`
- **Act Details**: See `POPULAR_ACTS.md`
- **Configuration**: See `config/acts_config.py`

## 🆘 Troubleshooting

### Import Errors

```bash
# Make sure you're in the data_ingestion directory
cd data_ingestion

# Verify dependencies
pip install -r requirements.txt
```

### No JSON Files Created

1. Check internet connection
2. Verify IndiaCode URLs are correct
3. Check logs for error messages
4. Test with a single act first

### ChromaDB Loading Fails

1. Verify `ai_engine/.env` is configured
2. Check ChromaDB path is correct
3. Ensure ChromaDB is accessible
