# Retry Scraper for Sections with Alphabets

## Overview
This script is specifically designed to retry scraping sections that contain alphabets (e.g., 41A, 50A, 498A, 80C, etc.) which may have failed during the initial scraping process.

## Problem
Sections with alphabets often fail because:
1. IndiaCode may use different URL encoding for sections with letters
2. The section number format may vary (41A vs 41-A vs 41_A)
3. Content extraction may need different strategies

## Solution
The retry script:
- Tries multiple URL variations for each section
- Uses enhanced content extraction strategies
- Handles different section number formats
- Provides detailed logging for debugging

## Usage

### List All Failed Sections
```bash
python data_ingestion/sources/retry_alphabet_sections.py --list
```

### Retry All Failed Sections
```bash
python data_ingestion/sources/retry_alphabet_sections.py
```

### Retry Specific Section
```bash
python data_ingestion/sources/retry_alphabet_sections.py --act crpc --section 41A
```

## Failed Sections Identified (18 total)

### CrPC (3 sections)
- Section 41A: Notice of appearance before police officer
- Section 41D: Right of arrested person to meet an advocate
- Section 50A: Obligation of person making arrest to inform

### IPC (1 section)
- Section 498A: Husband or relative of husband of a woman subjecting her to cruelty

### Constitution (1 section)
- Section 300A: Persons not to be deprived of property save by authority of law

### Income Tax Act (2 sections)
- Section 80C: Deduction in respect of life insurance premia, etc.
- Section 80D: Deduction in respect of health insurance premia

### Representation of People Act (1 section)
- Section 125A: Penalty for filing false affidavit, etc.

### Information Technology Act (2 sections)
- Section 43A: Compensation for failure to protect data
- Section 72A: Punishment for disclosure of information in breach of lawful contract

### Transfer of Property Act (1 section)
- Section 122A: Gift of existing movable property

### Industrial Disputes Act (5 sections)
- Section 11A: Powers of Labour Courts, Tribunals and National Tribunals
- Section 25F: Conditions precedent to retrenchment of workmen
- Section 25G: Procedure for retrenchment
- Section 25H: Re-employment of retrenched workmen
- Section 33A: Special provision for adjudication

### Hindu Marriage Act (2 sections)
- Section 13A: Alternate relief in divorce proceedings
- Section 13B: Divorce by mutual consent

## URL Variations Tried

For each section, the script tries multiple URL formats:
1. Direct section number: `orderno=41A`
2. URL encoded: `orderno=41A` (encoded)
3. With underscore: `orderno=41_A`
4. With hyphen: `orderno=41-A`
5. Lowercase: `orderno=41a`
6. Uppercase: `orderno=41A`

## Enhanced Extraction Strategies

1. **Multiple Title Selectors**: Tries various HTML selectors to find section titles
2. **Pattern Matching**: Searches for section number in multiple formats
3. **Content Following Title**: Extracts content that follows the section title
4. **Fallback Strategies**: Multiple fallback methods if primary extraction fails

## Output

Successfully scraped sections are saved to:
```
data_ingestion/storage/acts/{act_key}/section_{section_number}.json
```

## Example Output

```
======================================================================
Retrying 18 Failed Sections with Alphabets
======================================================================

======================================================================
CrPC - Section 41A
======================================================================
📄 Retrying CrPC Section 41A
   Trying 6 URL variations...
   Attempt 1/6: https://www.indiacode.nic.in/show-data?actid=...&orderno=41A
   Attempt 2/6: https://www.indiacode.nic.in/show-data?actid=...&orderno=41-A
   ...
✅ Successfully scraped CrPC Section 41A using URL variation 2
💾 Saved: data_ingestion/storage/acts/crpc/section_41A.json
```

## Notes

- The script includes rate limiting (3 seconds between sections)
- Each URL variation is tried with a 1-second delay
- Failed sections are logged with detailed error messages
- The script exits with code 0 if all sections succeed, 1 if any fail

## Troubleshooting

If sections still fail after retry:
1. Check the IndiaCode website manually for the section
2. Verify the Act ID is correct in `acts_config.py`
3. Check if the section number format on IndiaCode differs
4. Review the detailed logs for specific error messages
