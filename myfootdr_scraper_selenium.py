"""
Alternative scraper using Selenium (for dynamically loaded content)
Install requirements: pip install selenium webdriver-manager beautifulsoup4
"""

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup
import csv
import time

def setup_driver():
    """Setup Chrome driver with options"""
    options = webdriver.ChromeOptions()
    options.add_argument('--headless')  # Run in background
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('--disable-blink-features=AutomationControlled')
    options.add_argument('user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36')
    
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
    return driver

def scrape_clinic_selenium(driver, clinic_url):
    """Scrape individual clinic using Selenium"""
    try:
        driver.get(clinic_url)
        time.sleep(2)  # Wait for page to load
        
        # Get page source and parse with BeautifulSoup
        soup = BeautifulSoup(driver.page_source, 'html.parser')
        
        clinic_data = {
            'Name of Clinic': '',
            'Address': '',
            'Email': '',
            'Phone': '',
            'Services': ''
        }
        
        # Extract Name
        name_elem = driver.find_elements(By.TAG_NAME, 'h1')
        if name_elem:
            clinic_data['Name of Clinic'] = name_elem[0].text.strip()
        
        # Extract Address
        try:
            address_elem = driver.find_element(By.CSS_SELECTOR, '[itemprop="address"], .address')
            clinic_data['Address'] = address_elem.text.strip()
        except:
            # Fallback: look in page source
            for line in soup.get_text().split('\n'):
                line = line.strip()
                if any(keyword in line.lower() for keyword in ['street', 'road', 'qld', 'nsw', 'vic']):
                    if 10 < len(line) < 200:
                        clinic_data['Address'] = line
                        break
        
        # Extract Email
        try:
            email_elem = driver.find_element(By.CSS_SELECTOR, 'a[href^="mailto:"]')
            clinic_data['Email'] = email_elem.get_attribute('href').replace('mailto:', '').strip()
        except:
            pass
        
        # Extract Phone
        try:
            phone_elem = driver.find_element(By.CSS_SELECTOR, 'a[href^="tel:"]')
            clinic_data['Phone'] = phone_elem.text.strip()
        except:
            import re
            phone_pattern = r'(\(?\d{2}\)?\s?\d{4}\s?\d{4})'
            phone_match = re.search(phone_pattern, driver.page_source)
            if phone_match:
                clinic_data['Phone'] = phone_match.group(1).strip()
        
        # Extract Services
        try:
            services_elems = driver.find_elements(By.CSS_SELECTOR, 'ul li, .services li')
            if services_elems and len(services_elems) > 2:
                services = [s.text.strip() for s in services_elems if s.text.strip()]
                clinic_data['Services'] = ', '.join(services[:10])  # Limit to 10 services
        except:
            pass
        
        return clinic_data
        
    except Exception as e:
        print(f"Error scraping {clinic_url}: {str(e)}")
        return None

def scrape_all_clinics_selenium(main_url):
    """Main function using Selenium"""
    print("Setting up Selenium driver...")
    driver = setup_driver()
    all_clinics = []
    
    try:
        print(f"Loading main page: {main_url}")
        driver.get(main_url)
        time.sleep(3)
        
        # Find all links
        all_links = driver.find_elements(By.TAG_NAME, 'a')
        clinic_urls = set()
        
        for link in all_links:
            try:
                href = link.get_attribute('href')
                if href and ('clinic' in href.lower() or 'podiatrist' in href.lower()):
                    if main_url.split('/web/')[0] in href:  # Same domain
                        clinic_urls.add(href)
            except:
                continue
        
        clinic_urls = list(clinic_urls)
        print(f"Found {len(clinic_urls)} potential clinic pages")
        
        # Scrape each clinic
        for idx, url in enumerate(clinic_urls, 1):
            print(f"\nProcessing {idx}/{len(clinic_urls)}: {url}")
            clinic_data = scrape_clinic_selenium(driver, url)
            
            if clinic_data and clinic_data['Name of Clinic']:
                all_clinics.append(clinic_data)
                print(f"✓ Added: {clinic_data['Name of Clinic']}")
            
            time.sleep(2)
        
        return all_clinics
        
    except Exception as e:
        print(f"Error: {str(e)}")
        return []
    finally:
        driver.quit()
        print("\nDriver closed")

def save_to_csv(clinics_data, filename='myfootdr_clinics.csv'):
    """Save to CSV"""
    fieldnames = ['Name of Clinic', 'Address', 'Email', 'Phone', 'Services']
    
    with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(clinics_data)
    
    print(f"\n✓ Saved {len(clinics_data)} clinics to {filename}")

def main():
    url = "https://web.archive.org/web/20250708180027/https://www.myfootdr.com.au/our-clinics/"
    
    print("\n" + "="*60)
    print("MyFootDr Selenium Scraper")
    print("="*60 + "\n")
    
    clinics = scrape_all_clinics_selenium(url)
    
    if clinics:
        save_to_csv(clinics)
    else:
        print("No data scraped!")

if __name__ == "__main__":
    main()
