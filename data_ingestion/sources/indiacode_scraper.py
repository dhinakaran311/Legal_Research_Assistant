"""
IndiaCode Scraper for CrPC Sections
Scrapes 10 specific CrPC sections from IndiaCode and saves as JSON
"""
import requests
from bs4 import BeautifulSoup
import json
import os
import time
import logging
from pathlib import Path
from typing import Dict, Optional

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Base URL for IndiaCode CrPC
BASE_URL = "https://www.indiacode.nic.in"

# 10 CrPC Sections to scrape
CRPC_SECTIONS = {
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
}

# CrPC Section URLs (IndiaCode structure)
# Act ID for CrPC 1973: AC_CEN_5_23_00037_19740325_1517807320172
# Format: https://www.indiacode.nic.in/show-data?actid=<ACT_ID>&orderno=<SECTION>
#
# NOTE: Verify these URLs are correct by visiting IndiaCode website
# The actid and orderno parameters may need adjustment based on actual IndiaCode structure
CRPC_ACT_ID = "AC_CEN_5_23_00037_19740325_1517807320172"

CRPC_SECTION_URLS = {
    "41": f"https://www.indiacode.nic.in/show-data?actid={CRPC_ACT_ID}&orderno=41",
    "41A": f"https://www.indiacode.nic.in/show-data?actid={CRPC_ACT_ID}&orderno=41A",
    "41D": f"https://www.indiacode.nic.in/show-data?actid={CRPC_ACT_ID}&orderno=41D",
    "50": f"https://www.indiacode.nic.in/show-data?actid={CRPC_ACT_ID}&orderno=50",
    "50A": f"https://www.indiacode.nic.in/show-data?actid={CRPC_ACT_ID}&orderno=50A",
    "154": f"https://www.indiacode.nic.in/show-data?actid={CRPC_ACT_ID}&orderno=154",
    "156": f"https://www.indiacode.nic.in/show-data?actid={CRPC_ACT_ID}&orderno=156",
    "436": f"https://www.indiacode.nic.in/show-data?actid={CRPC_ACT_ID}&orderno=436",
    "437": f"https://www.indiacode.nic.in/show-data?actid={CRPC_ACT_ID}&orderno=437",
    "438": f"https://www.indiacode.nic.in/show-data?actid={CRPC_ACT_ID}&orderno=438"
}

# Storage directory
STORAGE_DIR = Path(__file__).parent.parent / "storage" / "acts" / "crpc"
STORAGE_DIR.mkdir(parents=True, exist_ok=True)


def get_headers() -> Dict[str, str]:
    """Get HTTP headers for requests"""
    return {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.5",
        "Accept-Encoding": "gzip, deflate, br",
        "Connection": "keep-alive",
        "Upgrade-Insecure-Requests": "1"
    }


def extract_section_content(html: str, section_number: str) -> Optional[Dict[str, str]]:
    """
    Extract section content from IndiaCode HTML
    
    Args:
        html: HTML content from IndiaCode
        section_number: Section number being scraped
        
    Returns:
        Dictionary with section data or None if extraction fails
    """
    try:
        soup = BeautifulSoup(html, 'lxml')
        
        # Find section title (usually in h3, h4, or strong tags)
        title = None
        title_selectors = [
            'h3',
            'h4', 
            'strong',
            '.section-title',
            '[class*="section"]',
            '[id*="section"]'
        ]
        
        for selector in title_selectors:
            title_elem = soup.select_one(selector)
            if title_elem:
                title_text = title_elem.get_text(strip=True)
                # Check if it contains section number
                if section_number in title_text or 'Section' in title_text:
                    title = title_text
                    break
        
        # If no title found, use default
        if not title:
            title = CRPC_SECTIONS.get(section_number, f"Section {section_number}")
        
        # Extract main content
        # Try different content containers
        content = None
        content_selectors = [
            '.act-content',
            '.section-content',
            '.main-content',
            '#main-content',
            'article',
            '.section-body',
            '[class*="content"]'
        ]
        
        for selector in content_selectors:
            content_elem = soup.select_one(selector)
            if content_elem:
                # Get text and clean it
                content = content_elem.get_text(separator=' ', strip=True)
                if len(content) > 100:  # Ensure we have substantial content
                    break
        
        # Fallback: get all paragraph text
        if not content or len(content) < 100:
            paragraphs = soup.find_all('p')
            content_parts = []
            for p in paragraphs:
                text = p.get_text(strip=True)
                if text and len(text) > 10:
                    content_parts.append(text)
            content = ' '.join(content_parts)
        
        # If still no content, try getting text from body
        if not content or len(content) < 100:
            body = soup.find('body')
            if body:
                # Remove script and style elements
                for script in body(["script", "style", "nav", "header", "footer"]):
                    script.decompose()
                content = body.get_text(separator=' ', strip=True)
        
        if not content or len(content) < 50:
            logger.warning(f"⚠️  Section {section_number}: Insufficient content extracted")
            return None
        
        return {
            "title": title,
            "content": content
        }
        
    except Exception as e:
        logger.error(f"❌ Error extracting section {section_number}: {str(e)}")
        return None


def clean_text(text: str) -> str:
    """
    Basic text cleaning
    More comprehensive cleaning will be done in text_cleaner.py
    """
    if not text:
        return ""
    
    # Remove extra whitespace
    lines = text.split('\n')
    cleaned_lines = [line.strip() for line in lines if line.strip()]
    text = ' '.join(cleaned_lines)
    
    # Remove multiple spaces
    while '  ' in text:
        text = text.replace('  ', ' ')
    
    return text.strip()


def scrape_section(section_number: str, url: str) -> Optional[Dict]:
    """
    Scrape a single CrPC section from IndiaCode
    
    Args:
        section_number: Section number (e.g., "438", "41A")
        url: URL to scrape
        
    Returns:
        Dictionary with section data or None if failed
    """
    logger.info(f"📄 Scraping Section {section_number}: {url}")
    
    try:
        # Send GET request
        response = requests.get(url, headers=get_headers(), timeout=30)
        response.raise_for_status()
        
        # Extract content
        extracted = extract_section_content(response.text, section_number)
        
        if not extracted:
            logger.error(f"❌ Failed to extract content for Section {section_number}")
            return None
        
        # Create JSON structure
        section_data = {
            "act": "Code of Criminal Procedure, 1973",
            "section": section_number,
            "title": extracted["title"],
            "content": clean_text(extracted["content"]),
            "source": "IndiaCode",
            "source_url": url,
            "last_updated": "1974"
        }
        
        logger.info(f"✅ Successfully scraped Section {section_number}")
        return section_data
        
    except requests.exceptions.RequestException as e:
        logger.error(f"❌ Network error scraping Section {section_number}: {str(e)}")
        return None
    except Exception as e:
        logger.error(f"❌ Error scraping Section {section_number}: {str(e)}")
        return None


def save_section_json(section_data: Dict, section_number: str) -> bool:
    """
    Save section data as JSON file
    
    Args:
        section_data: Dictionary with section data
        section_number: Section number for filename
        
    Returns:
        True if saved successfully, False otherwise
    """
    try:
        filename = f"section_{section_number}.json"
        filepath = STORAGE_DIR / filename
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(section_data, f, indent=2, ensure_ascii=False)
        
        logger.info(f"💾 Saved: {filepath}")
        return True
        
    except Exception as e:
        logger.error(f"❌ Failed to save Section {section_number}: {str(e)}")
        return False


def scrape_all_crpc_sections() -> Dict[str, bool]:
    """
    Scrape all 10 CrPC sections
    
    Returns:
        Dictionary mapping section numbers to success status
    """
    logger.info("=" * 70)
    logger.info("🚀 Starting CrPC Section Scraping")
    logger.info("=" * 70)
    logger.info(f"📁 Storage directory: {STORAGE_DIR}")
    logger.info(f"📊 Sections to scrape: {len(CRPC_SECTION_URLS)}")
    logger.info("")
    
    results = {}
    
    for section_number, url in CRPC_SECTION_URLS.items():
        # Scrape section
        section_data = scrape_section(section_number, url)
        
        if section_data:
            # Save to JSON
            success = save_section_json(section_data, section_number)
            results[section_number] = success
        else:
            results[section_number] = False
        
        # Rate limiting: wait 2 seconds between requests
        if section_number != list(CRPC_SECTION_URLS.keys())[-1]:
            logger.info("⏳ Waiting 2 seconds before next request...")
            time.sleep(2)
        
        logger.info("")
    
    # Summary
    logger.info("=" * 70)
    logger.info("📊 Scraping Summary")
    logger.info("=" * 70)
    successful = sum(1 for v in results.values() if v)
    failed = len(results) - successful
    
    logger.info(f"✅ Successfully scraped: {successful}/{len(results)}")
    logger.info(f"❌ Failed: {failed}/{len(results)}")
    
    if failed > 0:
        logger.info("\nFailed sections:")
        for section, success in results.items():
            if not success:
                logger.info(f"   - Section {section}")
    
    logger.info("=" * 70)
    
    return results


if __name__ == "__main__":
    # Run scraper
    results = scrape_all_crpc_sections()
    
    # Exit with error code if any failures
    exit(0 if all(results.values()) else 1)
