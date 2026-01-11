"""
Multi-Act IndiaCode Scraper
Scrapes popular sections from multiple Indian acts
"""
import requests
from bs4 import BeautifulSoup
import json
import os
import time
import logging
from pathlib import Path
from typing import Dict, Optional, List
import sys

# Add config directory to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from config.acts_config import (
    ACT_CONFIGS, ACT_SECTIONS, get_act_config, get_act_sections,
    get_act_url, get_subcategory, list_all_acts, get_total_sections_count
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Base URL for IndiaCode
BASE_URL = "https://www.indiacode.nic.in"

# Storage base directory
STORAGE_BASE_DIR = Path(__file__).parent.parent / "storage" / "acts"


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


def extract_section_content(html: str, section_number: str, act_name: str) -> Optional[Dict[str, str]]:
    """
    Extract section content from IndiaCode HTML
    
    Args:
        html: HTML content from IndiaCode
        section_number: Section number being scraped
        act_name: Name of the act (for logging)
        
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
            '[id*="section"]',
            '.act-title'
        ]
        
        for selector in title_selectors:
            title_elem = soup.select_one(selector)
            if title_elem:
                title_text = title_elem.get_text(strip=True)
                # Check if it contains section number or relevant keywords
                if section_number in title_text or 'Section' in title_text or 'Article' in title_text:
                    title = title_text
                    break
        
        # If no title found, use section number
        if not title:
            title = f"Section {section_number}"
        
        # Extract main content
        content = None
        content_selectors = [
            '.act-content',
            '.section-content',
            '.main-content',
            '#main-content',
            'article',
            '.section-body',
            '[class*="content"]',
            '.provision-text'
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
                for script in body(["script", "style", "nav", "header", "footer", "aside"]):
                    script.decompose()
                content = body.get_text(separator=' ', strip=True)
        
        if not content or len(content) < 50:
            logger.warning(f"⚠️  {act_name} Section {section_number}: Insufficient content extracted")
            return None
        
        return {
            "title": title,
            "content": content
        }
        
    except Exception as e:
        logger.error(f"❌ Error extracting {act_name} Section {section_number}: {str(e)}")
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


def scrape_section(act_key: str, section_number: str, section_title: str, url: str) -> Optional[Dict]:
    """
    Scrape a single section from IndiaCode
    
    Args:
        act_key: Act key (e.g., "ipc", "crpc")
        section_number: Section number (e.g., "438", "302")
        section_title: Section title/description
        url: URL to scrape
        
    Returns:
        Dictionary with section data or None if failed
    """
    config = get_act_config(act_key)
    act_name = config.get("full_name", act_key.upper())
    
    logger.info(f"📄 Scraping {config.get('short_name', act_key.upper())} Section {section_number}: {url}")
    
    try:
        # Send GET request
        response = requests.get(url, headers=get_headers(), timeout=30)
        response.raise_for_status()
        
        # Extract content
        extracted = extract_section_content(response.text, section_number, config.get('short_name', act_key))
        
        if not extracted:
            logger.error(f"❌ Failed to extract content for {config.get('short_name', act_key)} Section {section_number}")
            return None
        
        # Use provided title if available, otherwise use extracted
        final_title = section_title if section_title else extracted["title"]
        
        # Create JSON structure
        section_data = {
            "act": act_name,
            "section": section_number,
            "title": final_title,
            "content": clean_text(extracted["content"]),
            "source": "IndiaCode",
            "source_url": url,
            "last_updated": str(config.get("year", ""))
        }
        
        logger.info(f"✅ Successfully scraped {config.get('short_name', act_key)} Section {section_number}")
        return section_data
        
    except requests.exceptions.RequestException as e:
        logger.error(f"❌ Network error scraping {config.get('short_name', act_key)} Section {section_number}: {str(e)}")
        return None
    except Exception as e:
        logger.error(f"❌ Error scraping {config.get('short_name', act_key)} Section {section_number}: {str(e)}")
        return None


def save_section_json(section_data: Dict, act_key: str, section_number: str) -> bool:
    """
    Save section data as JSON file
    
    Args:
        section_data: Dictionary with section data
        act_key: Act key (e.g., "ipc", "crpc")
        section_number: Section number for filename
        
    Returns:
        True if saved successfully, False otherwise
    """
    try:
        # Create act-specific directory
        act_dir = STORAGE_BASE_DIR / act_key.lower()
        act_dir.mkdir(parents=True, exist_ok=True)
        
        filename = f"section_{section_number}.json"
        filepath = act_dir / filename
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(section_data, f, indent=2, ensure_ascii=False)
        
        logger.info(f"💾 Saved: {filepath}")
        return True
        
    except Exception as e:
        logger.error(f"❌ Failed to save {act_key.upper()} Section {section_number}: {str(e)}")
        return False


def scrape_act(act_key: str) -> Dict[str, bool]:
    """
    Scrape all sections for a specific act
    
    Args:
        act_key: Act key (e.g., "ipc", "crpc", "cpc")
        
    Returns:
        Dictionary mapping section numbers to success status
    """
    config = get_act_config(act_key)
    if not config:
        logger.error(f"❌ Unknown act: {act_key}")
        return {}
    
    sections = get_act_sections(act_key)
    if not sections:
        logger.warning(f"⚠️  No sections configured for act: {act_key}")
        return {}
    
    act_name = config.get("short_name", act_key.upper())
    logger.info("=" * 70)
    logger.info(f"🚀 Starting {act_name} Section Scraping")
    logger.info("=" * 70)
    logger.info(f"📊 Sections to scrape: {len(sections)}")
    logger.info("")
    
    results = {}
    
    for section_number, section_title in sections.items():
        # Generate URL
        url = get_act_url(act_key, section_number)
        
        if not url:
            logger.error(f"❌ Failed to generate URL for {act_name} Section {section_number}")
            results[section_number] = False
            continue
        
        # Scrape section
        section_data = scrape_section(act_key, section_number, section_title, url)
        
        if section_data:
            # Save to JSON
            success = save_section_json(section_data, act_key, section_number)
            results[section_number] = success
        else:
            results[section_number] = False
        
        # Rate limiting: wait 2 seconds between requests
        time.sleep(2)
        
        logger.info("")
    
    # Summary
    logger.info("=" * 70)
    logger.info(f"📊 {act_name} Scraping Summary")
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


def scrape_all_acts(act_keys: Optional[List[str]] = None) -> Dict[str, Dict[str, bool]]:
    """
    Scrape all sections for multiple acts
    
    Args:
        act_keys: List of act keys to scrape. If None, scrapes all configured acts.
        
    Returns:
        Dictionary mapping act keys to their scraping results
    """
    if act_keys is None:
        act_keys = list_all_acts()
    
    logger.info("=" * 70)
    logger.info("🚀 Starting Multi-Act Section Scraping")
    logger.info("=" * 70)
    logger.info(f"📊 Acts to scrape: {len(act_keys)}")
    logger.info(f"📊 Total sections: {get_total_sections_count()}")
    logger.info("")
    
    all_results = {}
    
    for act_key in act_keys:
        config = get_act_config(act_key)
        if not config:
            logger.warning(f"⚠️  Skipping unknown act: {act_key}")
            continue
        
        logger.info(f"\n{'=' * 70}")
        logger.info(f"📚 Processing Act: {config.get('full_name', act_key)}")
        logger.info(f"{'=' * 70}\n")
        
        results = scrape_act(act_key)
        all_results[act_key] = results
        
        # Wait between acts (longer delay)
        if act_key != act_keys[-1]:
            logger.info("⏳ Waiting 5 seconds before next act...")
            time.sleep(5)
    
    # Overall summary
    logger.info("\n" + "=" * 70)
    logger.info("📊 Overall Scraping Summary")
    logger.info("=" * 70)
    
    total_successful = 0
    total_failed = 0
    
    for act_key, results in all_results.items():
        config = get_act_config(act_key)
        act_name = config.get("short_name", act_key.upper())
        successful = sum(1 for v in results.values() if v)
        failed = len(results) - successful
        
        total_successful += successful
        total_failed += failed
        
        logger.info(f"{act_name}: {successful}/{len(results)} successful, {failed} failed")
    
    logger.info("=" * 70)
    logger.info(f"✅ Total Successfully scraped: {total_successful}/{total_successful + total_failed}")
    logger.info(f"❌ Total Failed: {total_failed}/{total_successful + total_failed}")
    logger.info("=" * 70)
    
    return all_results


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Scrape Indian Acts from IndiaCode")
    parser.add_argument(
        "--acts",
        nargs="+",
        choices=list_all_acts(),
        help="Specific acts to scrape (default: all acts)"
    )
    parser.add_argument(
        "--list",
        action="store_true",
        help="List all configured acts and sections"
    )
    
    args = parser.parse_args()
    
    if args.list:
        logger.info("=" * 70)
        logger.info("📚 Configured Acts")
        logger.info("=" * 70)
        for act_key in list_all_acts():
            config = get_act_config(act_key)
            sections = get_act_sections(act_key)
            logger.info(f"\n{config.get('short_name', act_key.upper())} - {config.get('full_name', '')}")
            logger.info(f"   Sections: {len(sections)}")
            logger.info(f"   Sections: {', '.join(list(sections.keys())[:5])}{'...' if len(sections) > 5 else ''}")
        logger.info("=" * 70)
    else:
        # Run scraper
        results = scrape_all_acts(args.acts)
        
        # Exit with error code if any failures
        all_success = all(
            all(section_results.values())
            for section_results in results.values()
        )
        exit(0 if all_success else 1)
