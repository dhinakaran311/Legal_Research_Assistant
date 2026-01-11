# CrPC Data Scraping and Loading - Usage Guide

## Quick Start

### Step 1: Install Dependencies

```bash
cd data_ingestion
pip install -r requirements.txt
```

### Step 2: Verify URLs (IMPORTANT)

Before running the scraper, verify the IndiaCode URLs are correct:

1. Visit https://www.indiacode.nic.in
2. Navigate to Code of Criminal Procedure, 1973
3. Open one section (e.g., Section 438)
4. Copy the actual URL from your browser
5. Update URLs in `sources/indiacode_scraper.py` if needed

**Note:** The URLs in the scraper are based on the expected IndiaCode URL format. You may need to adjust them based on the actual website structure.

### Step 3: Scrape Sections

```bash
python sources/indiacode_scraper.py
```

**What it does:**
- Scrapes 10 CrPC sections from IndiaCode
- Saves JSON files to `storage/acts/crpc/`
- Waits 2 seconds between requests (rate limiting)
- Logs progress and errors

**Expected output:**
- 10 JSON files in `storage/acts/crpc/`
- Each file named `section_XXX.json`

### Step 4: Verify JSON Files

Check that JSON files are created correctly:

```bash
python test_crpc_scraper.py
```

This will validate:
- JSON structure
- Required fields
- Content length

### Step 5: Load into ChromaDB

```bash
python loaders/load_crpc_data.py
```

**What it does:**
- Loads all JSON files from `storage/acts/crpc/`
- Cleans text using text_cleaner module
- Creates metadata for ChromaDB
- Adds documents to ChromaDB collection
- Skips documents that already exist

**Expected output:**
- Documents added to ChromaDB
- Test query executed
- Summary of documents loaded

### Step 6: Verify in ChromaDB

Check that documents are in ChromaDB:

```bash
cd ../ai_engine
python check_data.py
```

Or test via search:
- Start AI Engine
- Start Backend
- Start Frontend
- Search for "What is anticipatory bail?" (should find Section 438)

## Troubleshooting

### Scraper Issues

**Problem: No content extracted**

**Solution:**
1. Check if IndiaCode HTML structure has changed
2. Inspect page source in browser
3. Update selectors in `extract_section_content()` function
4. Test with a single URL first

**Problem: 404 or Connection Error**

**Solution:**
1. Verify URLs are correct
2. Check internet connection
3. Verify IndiaCode website is accessible
4. Update URLs with actual working URLs

**Problem: Text is empty or malformed**

**Solution:**
1. Check if HTML structure changed
2. Adjust CSS selectors in scraper
3. Check logs for extraction errors

### Loader Issues

**Problem: Import errors**

**Solution:**
1. Verify Python paths in `load_crpc_data.py`
2. Make sure `ai_engine/src` is accessible
3. Check `data_ingestion` directory structure

**Problem: ChromaDB connection fails**

**Solution:**
1. Verify `ai_engine/.env` is configured
2. Check `CHROMA_DB_PATH` is correct
3. Ensure ChromaDB directory exists
4. Check permissions

**Problem: Documents not appearing in search**

**Solution:**
1. Verify documents were added (check count)
2. Test with exact section number query
3. Check metadata filters
4. Verify embeddings were generated

## Manual Testing

### Test Single Section

Edit `indiacode_scraper.py` and modify `CRPC_SECTION_URLS` to include only one URL:

```python
CRPC_SECTION_URLS = {
    "438": f"https://www.indiacode.nic.in/show-data?actid={CRPC_ACT_ID}&orderno=438"
}
```

Then run:
```bash
python sources/indiacode_scraper.py
```

### Test Text Cleaning

```python
from preprocess.text_cleaner import clean_legal_text

raw_text = "Your raw scraped text here..."
cleaned = clean_legal_text(raw_text, section_number="438")
print(cleaned)
```

### Test ChromaDB Query

```python
from vectorstore.chroma_client import ChromaClient
from config import settings

client = ChromaClient(
    persist_directory=settings.CHROMA_DB_PATH,
    collection_name=settings.CHROMA_COLLECTION_NAME
)
client.connect()

results = client.query(
    query_texts=["What is anticipatory bail?"],
    n_results=5,
    where={"act": "CrPC"}
)

print(f"Found {len(results['ids'][0])} results")
```

## File Locations

- **Scraped JSON files:** `data_ingestion/storage/acts/crpc/section_*.json`
- **Scraper script:** `data_ingestion/sources/indiacode_scraper.py`
- **Loader script:** `data_ingestion/loaders/load_crpc_data.py`
- **Text cleaner:** `data_ingestion/preprocess/text_cleaner.py`
- **Test script:** `data_ingestion/test_crpc_scraper.py`

## Next Steps

After successfully scraping and loading CrPC sections:

1. **Expand to more sections** - Add more CrPC sections
2. **Add IPC sections** - Follow same pattern for IPC
3. **Neo4j integration** - Create graph relationships
4. **Incremental updates** - Add functionality to update changed sections
