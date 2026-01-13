"""
Retry Scraper for Sections with Alphabets
Handles sections like 41A, 50A, 498A, etc. that may require special URL encoding
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
import re
import urllib.parse

# Add config directory to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from config.acts_config import (
    ACT_CONFIGS, ACT_SECTIONS, get_act_config, get_act_sections,
    get_act_url, get_subcategory, list_all_acts
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

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


def build_url_with_alpha_section(act_key: str, section_number: str) -> List[str]:
    """
    Build multiple URL variations for sections with alphabets
    IndiaCode may use different formats for sections with letters
    """
    config = get_act_config(act_key)
    if not config:
        return []
    
    act_id = config["act_id"]
    base_pattern = config["base_url_pattern"]
    
    # Try different URL formats
    urls_to_try = []
    
    # Format 1: Direct section number (e.g., 41A)
    url1 = base_pattern.format(act_id=act_id, section=section_number)
    urls_to_try.append(url1)
    
    # Format 2: URL encoded section
    encoded_section = urllib.parse.quote(section_number)
    url2 = base_pattern.format(act_id=act_id, section=encoded_section)
    if url2 != url1:
        urls_to_try.append(url2)
    
    # Format 3: Section with underscore (e.g., 41_A)
    if re.search(r'[A-Za-z]', section_number):
        section_with_underscore = re.sub(r'([0-9]+)([A-Za-z]+)', r'\1_\2', section_number)
        url3 = base_pattern.format(act_id=act_id, section=section_with_underscore)
        urls_to_try.append(url3)
    
    # Format 4: Section with hyphen (e.g., 41-A)
    if re.search(r'[A-Za-z]', section_number):
        section_with_hyphen = re.sub(r'([0-9]+)([A-Za-z]+)', r'\1-\2', section_number)
        url4 = base_pattern.format(act_id=act_id, section=section_with_hyphen)
        urls_to_try.append(url4)
    
    # Format 5: Try lowercase
    if section_number != section_number.lower():
        url5 = base_pattern.format(act_id=act_id, section=section_number.lower())
        urls_to_try.append(url5)
    
    # Format 6: Try uppercase
    if section_number != section_number.upper():
        url6 = base_pattern.format(act_id=act_id, section=section_number.upper())
        urls_to_try.append(url6)
    
    # Remove duplicates while preserving order
    seen = set()
    unique_urls = []
    for url in urls_to_try:
        if url not in seen:
            seen.add(url)
            unique_urls.append(url)
    
    return unique_urls


def extract_section_content_enhanced(html: str, section_number: str, act_name: str) -> Optional[Dict[str, str]]:
    """
    Enhanced extraction with multiple strategies for sections with alphabets
    """
    try:
        soup = BeautifulSoup(html, 'lxml')
        
        # Strategy 1: Look for section number in various formats
        section_patterns = [
            section_number,
            f"Section {section_number}",
            f"section {section_number}",
            f"Sec. {section_number}",
            f"sec. {section_number}",
            f"Section {section_number.upper()}",
            f"Section {section_number.lower()}"
        ]
        
        # Find section title
        title = None
        title_selectors = [
            'h1', 'h2', 'h3', 'h4', 'h5',
            'strong', 'b',
            '.section-title', '.act-title',
            '[class*="section"]', '[id*="section"]',
            '[class*="title"]', '[id*="title"]'
        ]
        
        for selector in title_selectors:
            elements = soup.select(selector)
            for elem in elements:
                text = elem.get_text(strip=True)
                # Check if it matches any section pattern
                for pattern in section_patterns:
                    if pattern in text or text.startswith(pattern) or pattern in text.upper():
                        title = text
                        break
                if title:
                    break
            if title:
                break
        
        # If no title found, try searching in all text
        if not title:
            body_text = soup.get_text()
            for pattern in section_patterns:
                if pattern in body_text:
                    # Try to extract the line containing the pattern
                    lines = body_text.split('\n')
                    for line in lines:
                        if pattern in line and len(line) < 200:
                            title = line.strip()
                            break
                    if title:
                        break
        
        # If still no title, use default
        if not title:
            title = f"Section {section_number}"
        
        # Extract content - try multiple strategies
        content = None
        
        # Strategy 1: Look for content containers
        content_selectors = [
            '.act-content', '.section-content', '.main-content',
            '#main-content', 'article', '.section-body',
            '[class*="content"]', '.provision-text',
            '.act-provision', '.section-provision'
        ]
        
        for selector in content_selectors:
            content_elem = soup.select_one(selector)
            if content_elem:
                content = content_elem.get_text(separator=' ', strip=True)
                if len(content) > 100:
                    break
        
        # Strategy 2: Find the section title element and get following content
        if not content or len(content) < 100:
            for selector in title_selectors:
                title_elem = soup.select_one(selector)
                if title_elem:
                    # Get all following siblings
                    content_parts = []
                    for sibling in title_elem.next_siblings:
                        if hasattr(sibling, 'get_text'):
                            text = sibling.get_text(strip=True)
                            if text and len(text) > 10:
                                content_parts.append(text)
                        elif isinstance(sibling, str) and sibling.strip():
                            content_parts.append(sibling.strip())
                    if content_parts:
                        content = ' '.join(content_parts)
                        if len(content) > 100:
                            break
        
        # Strategy 3: Get all paragraphs
        if not content or len(content) < 100:
            paragraphs = soup.find_all('p')
            content_parts = []
            for p in paragraphs:
                text = p.get_text(strip=True)
                if text and len(text) > 10:
                    content_parts.append(text)
            content = ' '.join(content_parts)
        
        # Strategy 4: Get body text (last resort)
        if not content or len(content) < 100:
            body = soup.find('body')
            if body:
                # Remove unwanted elements
                for unwanted in body(["script", "style", "nav", "header", "footer", "aside", "form"]):
                    unwanted.decompose()
                content = body.get_text(separator=' ', strip=True)
        
        # Clean content
        if content:
            # Remove excessive whitespace
            content = ' '.join(content.split())
            # Remove very short lines that are likely navigation
            lines = content.split('. ')
            content = '. '.join([line for line in lines if len(line) > 20])
        
        if not content or len(content) < 50:
            return None
        
        return {
            "title": title,
            "content": content
        }
        
    except Exception as e:
        logger.error(f"Error extracting content: {str(e)}")
        return None


def clean_text(text: str) -> str:
    """Basic text cleaning"""
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


def scrape_alphabet_section(act_key: str, section_number: str, section_title: str) -> Optional[Dict]:
    """
    Scrape a section with alphabet using multiple URL strategies
    """
    config = get_act_config(act_key)
    act_name = config.get("full_name", act_key.upper())
    short_name = config.get("short_name", act_key.upper())
    
    logger.info(f"📄 Retrying {short_name} Section {section_number}")
    
    # Get all URL variations to try
    urls_to_try = build_url_with_alpha_section(act_key, section_number)
    
    if not urls_to_try:
        logger.error(f"❌ Failed to generate URLs for {short_name} Section {section_number}")
        return None
    
    logger.info(f"   Trying {len(urls_to_try)} URL variations...")
    
    for idx, url in enumerate(urls_to_try, 1):
        logger.info(f"   Attempt {idx}/{len(urls_to_try)}: {url}")
        
        try:
            # Send GET request
            response = requests.get(url, headers=get_headers(), timeout=30)
            response.raise_for_status()
            
            # Check if we got a valid page (not error page)
            if "error" in response.text.lower() and "404" in response.text.lower():
                logger.warning(f"   ⚠️  URL returned 404, trying next variation...")
                continue
            
            # Extract content
            extracted = extract_section_content_enhanced(response.text, section_number, short_name)
            
            if extracted and len(extracted.get("content", "")) > 50:
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
                
                logger.info(f"✅ Successfully scraped {short_name} Section {section_number} using URL variation {idx}")
                return section_data
            else:
                logger.warning(f"   ⚠️  Insufficient content extracted, trying next variation...")
                continue
                
        except requests.exceptions.RequestException as e:
            logger.warning(f"   ⚠️  Network error: {str(e)}, trying next variation...")
            continue
        except Exception as e:
            logger.warning(f"   ⚠️  Error: {str(e)}, trying next variation...")
            continue
        
        # Small delay between attempts
        time.sleep(1)
    
    logger.error(f"❌ All URL variations failed for {short_name} Section {section_number}")
    return None


def save_section_json(section_data: Dict, act_key: str, section_number: str) -> bool:
    """Save section data as JSON file"""
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


def get_failed_alphabet_sections() -> List[tuple]:
    """
    Get all sections with alphabets that are missing from storage
    """
    failed_sections = []
    
    for act_key, sections in ACT_SECTIONS.items():
        for section_number, section_title in sections.items():
            # Check if section has alphabet
            if re.search(r'[A-Za-z]', section_number):
                # Check if file exists
                filepath = STORAGE_BASE_DIR / act_key.lower() / f"section_{section_number}.json"
                if not filepath.exists():
                    failed_sections.append((act_key, section_number, section_title))
    
    return failed_sections


def retry_all_failed_sections() -> Dict[str, bool]:
    """
    Retry scraping all failed sections with alphabets
    """
    failed_sections = get_failed_alphabet_sections()
    
    if not failed_sections:
        logger.info("✅ No failed sections with alphabets found!")
        return {}
    
        logger.info("=" * 70)
        logger.info(f"Retrying {len(failed_sections)} Failed Sections with Alphabets")
        logger.info("=" * 70)
    logger.info("")
    
    results = {}
    
    for act_key, section_number, section_title in failed_sections:
        config = get_act_config(act_key)
        short_name = config.get("short_name", act_key.upper())
        
        logger.info(f"\n{'=' * 70}")
        logger.info(f"📚 {short_name} - Section {section_number}")
        logger.info(f"{'=' * 70}")
        
        # Scrape section
        section_data = scrape_alphabet_section(act_key, section_number, section_title)
        
        if section_data:
            # Save to JSON
            success = save_section_json(section_data, act_key, section_number)
            results[f"{act_key}:{section_number}"] = success
        else:
            results[f"{act_key}:{section_number}"] = False
        
        # Rate limiting
        time.sleep(3)
        logger.info("")
    
    # Summary
    logger.info("=" * 70)
    logger.info("📊 Retry Summary")
    logger.info("=" * 70)
    successful = sum(1 for v in results.values() if v)
    failed = len(results) - successful
    
    logger.info(f"✅ Successfully scraped: {successful}/{len(results)}")
    logger.info(f"❌ Still failed: {failed}/{len(results)}")
    
    if failed > 0:
        logger.info("\nStill failed sections:")
        for key, success in results.items():
            if not success:
                logger.info(f"   - {key}")
    
    logger.info("=" * 70)
    
    return results


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Retry scraping sections with alphabets")
    parser.add_argument(
        "--act",
        type=str,
        help="Specific act to retry (e.g., 'crpc')"
    )
    parser.add_argument(
        "--section",
        type=str,
        help="Specific section to retry (e.g., '41A')"
    )
    parser.add_argument(
        "--list",
        action="store_true",
        help="List all failed sections with alphabets"
    )
    
    args = parser.parse_args()
    
    if args.list:
        failed = get_failed_alphabet_sections()
        logger.info("=" * 70)
        logger.info("📋 Failed Sections with Alphabets")
        logger.info("=" * 70)
        for act_key, section_number, section_title in failed:
            config = get_act_config(act_key)
            short_name = config.get("short_name", act_key.upper())
            logger.info(f"{short_name} Section {section_number}: {section_title}")
        logger.info("=" * 70)
        logger.info(f"Total: {len(failed)} sections")
    elif args.act and args.section:
        # Retry specific section
        config = get_act_config(args.act)
        if not config:
            logger.error(f"❌ Unknown act: {args.act}")
            exit(1)
        
        sections = get_act_sections(args.act)
        if args.section not in sections:
            logger.error(f"❌ Section {args.section} not found in {args.act}")
            exit(1)
        
        section_title = sections[args.section]
        section_data = scrape_alphabet_section(args.act, args.section, section_title)
        
        if section_data:
            success = save_section_json(section_data, args.act, args.section)
            if success:
                logger.info("✅ Section scraped and saved successfully!")
                exit(0)
            else:
                logger.error("❌ Failed to save section")
                exit(1)
        else:
            logger.error("❌ Failed to scrape section")
            exit(1)
    else:
        # Retry all failed sections
        results = retry_all_failed_sections()
        
        # Exit with error code if any failures
        all_success = all(results.values())
        exit(0 if all_success else 1)
