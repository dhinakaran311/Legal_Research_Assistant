# 📚 Dataset Sources — Legal Search Assistant (India)

## 1️⃣ Acts & Amendments
- Source: [IndiaCode](https://www.indiacode.nic.in)
- Format: JSON / text
- Local path: `data_ingestion/storage/acts/`

## 2️⃣ Court Judgments
- Source: [Indian Kanoon](https://indiankanoon.org)
- API: `/search/?formInput=...`
- Local path: `data_ingestion/storage/judgments/`

## 3️⃣ Law Commission Reports
- Source: [Law Commission Reports Archive](https://lawcommissionofindia.nic.in/reports.htm)
- Format: PDF → text
- Local path: `data_ingestion/storage/reports/`

## 4️⃣ Knowledge Graph
- Stored in Neo4j AuraDB Cloud  
- Nodes: Acts, Sections, Cases, Judges, Principles

## 5️⃣ Vector Database
- Embeddings generated via LangChain (MiniLM-L6-v2)
- Stored in `/chroma_storage/`

---

### Local vs API Usage
| Data Type | Access Method | Storage |
|------------|----------------|----------|
| Acts & Amendments | Scrape once from IndiaCode | Local (JSON) |
| Judgments | Retrieve from Indian Kanoon API | Cached locally |
| Reports | Download PDFs → parse text | Local (text) |
| Graph Relations | Generated from data | Neo4j Cloud |
| Embeddings | Generated locally | ChromaDB |

---

### Licensing
All datasets are publicly accessible under Government of India Open Data Policy / fair use for research.
