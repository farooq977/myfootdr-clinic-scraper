# MyFootDr Clinic Scraper

Web scraping tool to extract clinic information from myfootdr.com.au

## Features
- Scrapes all regions and clinics
- Extracts: Name, Address, Email, Phone, Services
- Generates CSV with exact required column names
- Two versions: BeautifulSoup (simple) and Selenium (dynamic content)

## Installation

### Method 1: BeautifulSoup (Recommended for static pages)
```bash
pip install requests beautifulsoup4
```

### Method 2: Selenium (For dynamic/JavaScript-heavy pages)
```bash
pip install selenium webdriver-manager beautifulsoup4
```

## Usage

### Option 1: Run BeautifulSoup version
```bash
python myfootdr_scraper.py
```

### Option 2: Run Selenium version (if BeautifulSoup doesn't work)
```bash
python myfootdr_scraper_selenium.py
```

## Output
- File name: `myfootdr_clinics.csv`
- Columns (exact names):
  - Name of Clinic
  - Address
  - Email
  - Phone
  - Services

## How It Works

1. **Main Page**: Loads the clinic listing page
2. **Find Regions**: Identifies all region/location links
3. **Visit Clinics**: Goes to each clinic's individual page
4. **Extract Data**: Scrapes the 5 required fields
5. **Save CSV**: Writes all data to CSV file

## Troubleshooting

### If no data is scraped:
1. Check your internet connection
2. The website structure may have changed
3. Try the Selenium version instead
4. Manually inspect the website and adjust CSS selectors in the code

### If missing some fields:
- Website may not have all information for every clinic
- Check the HTML structure and update selectors

### Rate Limiting:
- Script includes delays (1-2 seconds) between requests
- If blocked, increase sleep time in the code

## Customization

You can modify the script to:
- Change sleep delays (search for `time.sleep()`)
- Adjust CSS selectors (if website structure is different)
- Add more fields to extract
- Filter specific regions only

## Important Notes

⚠️ **Web Scraping Ethics**:
- This script is for educational/legitimate business purposes
- Includes polite delays to avoid server overload
- Check website's robots.txt and terms of service
- Use responsibly

⚠️ **Archive.org URL**:
- The script uses the Wayback Machine archived version
- The site structure is from the archived date (2025-07-08)

## Example Output

```csv
Name of Clinic,Address,Email,Phone,Services
"Podiatrist Noosa","123 Main St, Noosa QLD 4567","noosa@myfootdr.com.au","(07) 1234 5678","Orthotics, Ingrown Toenails, Bunions, Heel Pain"
```

## Support

If the script doesn't work:
1. Check if the website structure has changed
2. Try both versions (BeautifulSoup and Selenium)
3. Inspect the website manually to identify correct HTML elements
4. Update CSS selectors in the code accordingly

---

**Created for**: Web scraping task
**Target**: https://web.archive.org/web/20250708180027/https://www.myfootdr.com.au/our-clinics/
