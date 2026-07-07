import requests
from bs4 import BeautifulSoup
import csv
import time
import json
from urllib.parse import urljoin
import random
import re

# ULTRA SLOW Configuration to avoid 403
DELAY_MIN = 8  # 8 seconds minimum
DELAY_MAX = 15  # 15 seconds maximum
MAX_RETRIES = 5
TIMEOUT = 20

# Rotate user agents to look more human
USER_AGENTS = [
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.1 Safari/605.1.15',
    'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
]

def get_random_headers():
    """Get random headers to look like a real browser"""
    return {
        'User-Agent': random.choice(USER_AGENTS),
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.5',
        'Accept-Encoding': 'gzip, deflate',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1'
    }

def smart_delay():
    """Ultra slow delay"""
    delay = random.uniform(DELAY_MIN, DELAY_MAX)
    print(f"  ⏳ Waiting {delay:.1f} seconds (avoiding 403)...")
    time.sleep(delay)

def fetch_with_retry(url, retries=MAX_RETRIES):
    """Fetch with aggressive retry and backoff"""
    for attempt in range(retries):
        try:
            headers = get_random_headers()
            response = requests.get(url, timeout=TIMEOUT, headers=headers)
            
            if response.status_code == 403:
                print(f"  ⚠️  403 Forbidden! Backing off...")
                # Long wait for 403
                wait_time = (attempt + 1) * 20
                print(f"  ⏰ Waiting {wait_time} seconds before retry...")
                time.sleep(wait_time)
                continue
            
            response.raise_for_status()
            return response
            
        except requests.exceptions.RequestException as e:
            if attempt < retries - 1:
                wait_time = (attempt + 1) * 10
                print(f"  ⚠️  Attempt {attempt + 1} failed. Retrying in {wait_time}s...")
                time.sleep(wait_time)
            else:
                print(f"  ❌ Failed after {retries} attempts: {str(e)[:100]}")
                return None
    return None

def save_progress(data):
    """Save progress"""
    import os
    import tempfile
    temp_dir = tempfile.gettempdir()
    filepath = os.path.join(temp_dir, 'myfootdr_progress.json')
    try:
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        print(f"  💾 Progress saved to: {filepath}")
    except Exception as e:
        print(f"  ⚠️ Could not save progress: {e}")

def load_progress():
    """Load progress"""
    import os
    import tempfile
    temp_dir = tempfile.gettempdir()
    filepath = os.path.join(temp_dir, 'myfootdr_progress.json')
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
            print(f"  📂 Loaded progress from: {filepath}")
            return data
    except FileNotFoundError:
        return {'scraped_urls': [], 'clinics': []}

def scrape_clinic_details(clinic_url):
    """Scrape clinic with improved extraction"""
    try:
        response = fetch_with_retry(clinic_url)
        if not response:
            return None
        
        soup = BeautifulSoup(response.content, 'html.parser')
        
        clinic_data = {
            'Name of Clinic': '',
            'Address': '',
            'Email': '',
            'Phone': '',
            'Services': ''
        }
        
        # Name
        name_tag = soup.find('h1')
        if name_tag:
            clinic_data['Name of Clinic'] = name_tag.get_text(strip=True)
        
        # Address
        address = ''
        address_tag = soup.find(['div', 'span', 'p'], itemprop='address')
        if address_tag:
            address = address_tag.get_text(strip=True)
        
        if not address:
            address_tag = soup.find(['div', 'p', 'span'], class_=lambda x: x and 'address' in str(x).lower())
            if address_tag:
                address = address_tag.get_text(strip=True)
        
        if not address:
            text_content = soup.get_text()
            lines = [line.strip() for line in text_content.split('\n') if line.strip()]
            aus_states = ['QLD', 'NSW', 'VIC', 'SA', 'WA', 'NT', 'TAS', 'ACT']
            street_keywords = ['Street', 'Road', 'Avenue', 'Drive', 'Lane', 'Court']
            
            for line in lines:
                if any(state in line.upper() for state in aus_states):
                    if 15 < len(line) < 200:
                        if any(keyword.lower() in line.lower() for keyword in street_keywords):
                            address = line
                            break
        
        clinic_data['Address'] = address
        
        # Email - Improved extraction with URL cleanup
        email = ''
        email_tag = soup.find('a', href=lambda x: x and 'mailto:' in x)
        if email_tag:
            email = email_tag['href'].replace('mailto:', '').strip()
        
        # Clean archive.org URLs from email
        if email and 'archive.org' in email:
            # Extract just the email part from archive URL
            # Example: https://web.archive.org/web/20250814053159/toowoomba@myfootdr.com.au
            # Should become: toowoomba@myfootdr.com.au
            parts = email.split('/')
            for part in reversed(parts):
                if '@' in part:
                    email = part
                    break
        
        if not email:
            email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
            email_match = re.search(email_pattern, soup.get_text())
            if email_match:
                email = email_match.group(0)
        
        if not email:
            email_containers = soup.find_all(['span', 'div', 'p'], class_=lambda x: x and 'email' in str(x).lower())
            for container in email_containers:
                text = container.get_text(strip=True)
                email_match = re.search(email_pattern, text)
                if email_match:
                    email = email_match.group(0)
                    break
        
        # Final cleanup - ensure no archive.org remnants
        if email and 'archive.org' in email:
            email_match = re.search(r'[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}', email)
            if email_match:
                email = email_match.group(0)
            else:
                email = ''  # Invalid email
        
        clinic_data['Email'] = email
        
        # Phone - Better cleaning
        phone = ''
        phone_tag = soup.find('a', href=lambda x: x and 'tel:' in x)
        if phone_tag:
            phone_href = phone_tag.get('href', '').replace('tel:', '').replace('+61', '0').strip()
            phone_text = phone_tag.get_text(strip=True)
            phone = phone_href if phone_href and phone_href[0].isdigit() else phone_text
        
        if not phone:
            phone_containers = soup.find_all(['span', 'div', 'p', 'a'], class_=lambda x: x and 'phone' in str(x).lower())
            for container in phone_containers:
                text = container.get_text(strip=True)
                text = re.sub(r'^(Phone|Tel|Call|Contact):\s*', '', text, flags=re.IGNORECASE)
                if text and any(c.isdigit() for c in text):
                    phone = text
                    break
        
        if not phone:
            phone_pattern = r'(?:1[38]00[\s\-]?\d{3}[\s\-]?\d{3}|(?:\+?61|0)?[2-478](?:[\s\-]?\d){8})'
            phone_match = re.search(phone_pattern, soup.get_text())
            if phone_match:
                phone = phone_match.group(0).strip()
        
        # Clean phone
        if phone:
            phone = re.sub(r'^[^0-9+(]+', '', phone)
            phone = re.sub(r'\s+', ' ', phone)
            phone = phone.replace('+61', '0')
        
        clinic_data['Phone'] = phone
        
        # Services
        services_list = []
        services_section = soup.find(['div', 'section'], class_=lambda x: x and 'service' in str(x).lower())
        if services_section:
            items = services_section.find_all(['li', 'p', 'span'])
            services_list = [item.get_text(strip=True) for item in items if item.get_text(strip=True)]
        
        if not services_list:
            lists = soup.find_all(['ul', 'ol'])
            for lst in lists:
                items = lst.find_all('li')
                if len(items) >= 3:
                    temp_services = [item.get_text(strip=True) for item in items]
                    temp_services = [s for s in temp_services if 5 < len(s) < 100]
                    if temp_services:
                        services_list = temp_services
                        break
        
        clinic_data['Services'] = ', '.join(services_list[:15]) if services_list else ''
        
        return clinic_data
        
    except Exception as e:
        print(f"  ❌ Error: {str(e)[:100]}")
        return None

def is_valid_clinic_url(url):
    """Check if valid clinic URL"""
    if url.startswith('javascript:'):
        return False
    if '#' in url and not any(x in url for x in ['/our-clinics/', '/clinic']):
        return False
    clinic_keywords = ['clinic', 'podiatry', 'podiatrist']
    if not any(keyword in url.lower() for keyword in clinic_keywords):
        return False
    skip_keywords = ['about-us', 'our-services', 'clinical-advisory']
    if any(keyword in url.lower() for keyword in skip_keywords):
        return False
    return True

def scrape_all_clinics(main_url):
    """Ultra-slow scraping"""
    print("=" * 70)
    print("   MyFootDr Ultra-Slow Scraper (Avoiding 403)")
    print("=" * 70)
    
    progress = load_progress()
    all_clinics = progress['clinics']
    scraped_urls = set(progress['scraped_urls'])
    
    if scraped_urls:
        print(f"\n📂 Resuming... Already have {len(all_clinics)} clinics\n")
    
    try:
        print(f"🌐 Fetching main page...")
        response = fetch_with_retry(main_url)
        
        if not response:
            print("❌ Could not fetch main page (403 or network error)")
            print("💡 Try again in 30 minutes or use VPN")
            return all_clinics
        
        soup = BeautifulSoup(response.content, 'html.parser')
        print("✅ Main page loaded\n")
        
        all_links = soup.find_all('a', href=True)
        clinic_urls = set()
        
        for link in all_links:
            href = link['href']
            full_url = urljoin(main_url, href)
            if is_valid_clinic_url(full_url):
                clinic_urls.add(full_url)
        
        clinic_urls = clinic_urls - scraped_urls
        clinic_urls = list(clinic_urls)
        
        print(f"📊 {len(clinic_urls)} clinics to scrape")
        print(f"⏱️  Estimated: {len(clinic_urls) * DELAY_MIN / 60:.0f}-{len(clinic_urls) * DELAY_MAX / 60:.0f} minutes\n")
        
        for idx, url in enumerate(clinic_urls, 1):
            print(f"\n[{idx}/{len(clinic_urls)}] {url}")
            
            if url in scraped_urls:
                continue
            
            clinic_data = scrape_clinic_details(url)
            
            if clinic_data and clinic_data['Name of Clinic']:
                duplicate = False
                for existing in all_clinics:
                    if existing['Name of Clinic'] == clinic_data['Name of Clinic']:
                        duplicate = True
                        break
                
                if not duplicate:
                    all_clinics.append(clinic_data)
                    print(f"  ✅ {clinic_data['Name of Clinic']}")
                    print(f"     📍 {clinic_data['Address'][:50]}...")
                    print(f"     📞 {clinic_data['Phone']}")
                    print(f"     ✉️  {clinic_data['Email']}")
            
            scraped_urls.add(url)
            
            if idx % 3 == 0:
                save_progress({'scraped_urls': list(scraped_urls), 'clinics': all_clinics})
            
            if idx < len(clinic_urls):
                smart_delay()
        
        print(f"\n✅ Complete! {len(all_clinics)} clinics\n")
        save_progress({'scraped_urls': list(scraped_urls), 'clinics': all_clinics})
        return all_clinics
        
    except KeyboardInterrupt:
        print("\n⚠️  Interrupted!")
        save_progress({'scraped_urls': list(scraped_urls), 'clinics': all_clinics})
        return all_clinics

def save_to_csv(clinics_data, filename='myfootdr_clinics_final.csv'):
    """Save to CSV on Desktop"""
    if not clinics_data:
        return
    
    # Save to Desktop to avoid permission issues
    import os
    desktop = os.path.join(os.path.expanduser('~'), 'Desktop')
    filepath = os.path.join(desktop, filename)
    
    fieldnames = ['Name of Clinic', 'Address', 'Email', 'Phone', 'Services']
    
    try:
        with open(filepath, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(clinics_data)
        
        print(f"✅ CSV saved: {filepath}")
        print(f"   Total: {len(clinics_data)} clinics")
    except Exception as e:
        # Fallback to current directory
        try:
            with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                writer.writeheader()
                writer.writerows(clinics_data)
            print(f"✅ CSV saved: {filename} (in current directory)")
        except Exception as e2:
            print(f"❌ Error saving CSV: {e2}")

def main():
    url = "https://web.archive.org/web/20250708180027/https://www.myfootdr.com.au/our-clinics/"
    clinics = scrape_all_clinics(url)
    if clinics:
        save_to_csv(clinics)

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"\n❌ Error: {e}")
    finally:
        input("\nPress Enter to exit...")
