"""Check available scraped data"""
from pathlib import Path
import json

storage = Path('storage/acts')

if not storage.exists():
    print(f"Storage directory not found: {storage}")
    exit(1)

acts = [d.name for d in storage.iterdir() if d.is_dir()]
print(f"Acts with scraped data: {len(acts)}\n")

total_sections = 0
for act in sorted(acts):
    json_files = list((storage / act).glob('section_*.json'))
    total_sections += len(json_files)
    print(f"{act.upper():15s}: {len(json_files):3d} sections")

print(f"\n{'TOTAL':15s}: {total_sections:3d} sections")
print(f"\nCurrently in ChromaDB: 61 sections")
print(f"Available to load: {total_sections} sections")
print(f"Missing: {total_sections - 61} sections")
