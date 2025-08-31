from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service as ChromeService
from webdriver_manager.chrome import ChromeDriverManager
from selenium.common.exceptions import TimeoutException
import argparse
import time
import json
import os
import random
import glob

class HouseBot:
    def __init__(self, dry_run: bool | None = None, headless: bool | None = None):
        # Use a dynamic filename based on timestamp for data storage
        self.CURRENT_TIMESTAMP = int(time.time())
        self.PROPERTIES_FILE = f"properties_data_{self.CURRENT_TIMESTAMP}.json"
        self.SEEN_URLS_FILE = os.getenv("SEEN_URLS_FILE", "seen_urls.json")
        # Dry-run mode: don't submit motivation and don't persist seen/processed
        if dry_run is None:
            self.dry_run = os.getenv("HW_DRY_RUN", "0") == "1"
        else:
            self.dry_run = bool(dry_run)
        # Headless mode: run browser without visible window
        if headless is None:
            self.headless = os.getenv("HEADLESS", "0") == "1"
        else:
            self.headless = bool(headless)
        self.DEFAULT_APPLICATION_TEXT = """Beste verhuurder,

Ik zag uw woning aan de {street_name} en ik ben meteen super enthousiast!! Ik zoek op korte termijn een woning in DenHaag voor werk. Ik ben een volwassen vrouw van 54, ik heb 15 jaar in verschillende landen als arts gewerkt. Geleidelijk heb ik mij laten leiden door mijn passie en via verschillende vormen van heling, psychologisch welzijn en meditatie uiteindelijk succesvol tot essentieel psychotherapeut her-opgeleid waarin ik nu werk. Daarnaast ben ik ook teacher van essence ( Diamond Logos Akademie). Ik ben mijn Essentiele Psychologie practijk aan het opbouwen en geef ook groepen op een locatie in Zeeheldenkwartier, heerlijk vlakbij. Ik heb een stabiel maandinkomen van ongveer €2000 netto te besteden (vaak steeds meer), ik ben ZZP'er, en heb enig vermogen achter de hand. Ik ben single, ik rook niet en heb geen kinderen, en houd van een schone en gezellige omgeving om in rust te kunnen werken. Heel graag zou ik komen kijken! Mijn telefoon is 0636002634 en mijn e-mail prem1adhira@gmail.com (of onderstaande). Ik ben onmiddellijk beschikbaar voor verhuizen. Heel graag hoor ik van u!"""
        # Read configuration from environment variables so we don't hard-code secrets in the repo
        self.LOGIN_URL = os.getenv("HW_LOGIN_URL", "https://www.huurwoningen.nl/account/inloggen-email/?_target_path=/")
        # Browse account (User 2)
        self.BROWSE_USERNAME = os.getenv("HW_BROWSE_USERNAME", os.getenv("HW_USERNAME", ""))
        self.BROWSE_PASSWORD = os.getenv("HW_BROWSE_PASSWORD", os.getenv("HW_PASSWORD", ""))
        # Apply account (Adira)
        self.APPLY_USERNAME = os.getenv("HW_APPLY_USERNAME", os.getenv("HW_USERNAME", ""))
        self.APPLY_PASSWORD = os.getenv("HW_APPLY_PASSWORD", os.getenv("HW_PASSWORD", ""))
        # Track current session role: 'browse' or 'apply'
        self.current_role = None
        self.SEARCH_URL = os.getenv("HW_SEARCH_URL", "https://www.huurwoningen.nl/in/den-haag/wijk/zeeheldenkwartier/?price=600-900&radius=1&bedrooms=1")
        self.BASE_URL = os.getenv("HW_BASE_URL", "https://www.huurwoningen.nl")

        # Chrome options for different environments
        chrome_options = webdriver.ChromeOptions()
        # Only run headless if explicitly requested
        if self.headless:
            chrome_options.add_argument("--headless=new")
            print("Running in headless mode (no visible browser)")
        else:
            print("Running in visible mode (browser window will appear)")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-extensions")
        chrome_options.add_argument("--disable-plugins")
        chrome_options.add_argument("--remote-debugging-port=9222")
        
        # Detect Chrome binary location for different environments
        chrome_binary = None
        
        # Try different Chrome locations in order of preference
        possible_chrome_paths = [
            os.getenv("GOOGLE_CHROME_BIN"),  # Heroku buildpack sets this
            "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",  # macOS
            "/usr/bin/google-chrome",  # Linux
            "/usr/bin/google-chrome-stable",  # Some Linux distros
            "/usr/bin/chromium-browser",  # Ubuntu/Debian fallback
        ]
        
        for path in possible_chrome_paths:
            if path and os.path.exists(path):
                chrome_binary = path
                print(f"Found Chrome binary at: {chrome_binary}")
                break
        
        if chrome_binary:
            chrome_options.binary_location = chrome_binary
        else:
            print("Warning: Chrome binary not found, using system default")

        self.driver = webdriver.Chrome(
            service=ChromeService(ChromeDriverManager().install()),
            options=chrome_options
        )
        self.driver.maximize_window()
        self.wait = WebDriverWait(self.driver, 5)

    def load_seen_urls(self):
        try:
            if os.path.exists(self.SEEN_URLS_FILE):
                with open(self.SEEN_URLS_FILE, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    # stored as list
                    return set(data if isinstance(data, list) else [])
        except Exception:
            pass
        return set()

    def save_seen_urls(self, seen_urls: set):
        try:
            with open(self.SEEN_URLS_FILE, "w", encoding="utf-8") as f:
                json.dump(sorted(list(seen_urls)), f, indent=2, ensure_ascii=False)
        except Exception:
            pass

    def load_state(self):
        """Load previously processed houses from the most recent data file.

        Older versions of the file contained raw scraped entries under keys
        like ``house1``. We reconstruct a dict keyed by URL from any processed
        entries found (entries that have a ``processed_date`` field). This keeps
        internal deduplication by URL while allowing files to use ``houseN`` keys.
        """
        property_files = glob.glob("properties_data_*.json")
        if property_files:
            most_recent_file = max(property_files)
            try:
                with open(most_recent_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    # If file has URL keys (legacy/newer internal format), keep as is
                    # Else if file has houseN keys, rebuild dict keyed by URL for dedup purposes
                    processed_by_url = {}
                    for key, value in data.items():
                        # Accept only entries that look processed
                        if isinstance(value, dict) and value.get("processed_date"):
                            url = value.get("url")
                            if url:
                                processed_by_url[url] = value
                    return processed_by_url
        except (json.JSONDecodeError, FileNotFoundError):
            return {}
    return {}

    def save_state(self, processed_houses):
        """Persist processed houses using enumerated keys (house1, house2, ...).

        This matches the desired external JSON shape while we still deduplicate
        internally by URL.
        """
        # Sort entries by processed_date (oldest first) for stable output
        items = list(processed_houses.values())
        try:
            items.sort(key=lambda v: v.get("processed_date", ""))
        except Exception:
            pass
        output = {}
        for idx, item in enumerate(items, start=1):
            output[f"house{idx}"] = {
                "name": item.get("name"),
                "url": item.get("url"),
                "address": item.get("address"),
                "price": item.get("price"),
                "details": item.get("details"),
                "processed_date": item.get("processed_date"),
                "success": item.get("success", False),
            }
        with open(self.PROPERTIES_FILE, "w", encoding="utf-8") as f:
            json.dump(output, f, indent=2, ensure_ascii=False)

    def login_with(self, username: str, password: str, role: str):
        """Login using provided credentials and record current role."""
        self.driver.get(self.LOGIN_URL)
        try:
            email_input = self.wait.until(
        EC.presence_of_element_located((By.NAME, "email"))
    )
    email_input.clear()
            email_input.send_keys(username)
            self.handle_cookies()
            password_input = self.wait.until(
                EC.presence_of_element_located((By.NAME, "password"))
            )
            password_input.clear()
            password_input.send_keys(password)
            submit_button = self.wait.until(
                EC.element_to_be_clickable((By.XPATH, "//button[contains(., 'Inloggen')]")
            ))
            submit_button.click()
            self.wait.until(lambda driver: driver.current_url != self.LOGIN_URL)
            self.current_role = role
        except Exception as e:
            print(f"Login failed ({role}): {e}")

    def ensure_logged_in_role(self, role: str):
        """Ensure driver is authenticated as the requested role ('browse'|'apply').
        If not, clear cookies and login with the right user.
        """
        if role == self.current_role:
            return
        # Clear cookies to avoid being stuck in previous session
        try:
            self.driver.delete_all_cookies()
        except Exception:
            pass
        if role == 'browse':
            self.login_with(self.BROWSE_USERNAME, self.BROWSE_PASSWORD, 'browse')
        elif role == 'apply':
            self.login_with(self.APPLY_USERNAME, self.APPLY_PASSWORD, 'apply')

    def handle_cookies(self):
        cookie_selectors = [
            "//button[contains(text(), 'Accept')]",
            "//button[contains(text(), 'Accepteren')]",
            "//button[contains(text(), 'Alle cookies accepteren')]",
            "//button[contains(text(), 'Akkoord')]",
            "//button[@id='onetrust-accept-btn-handler']",
            "//button[contains(@class, 'accept')]",
            "//button[contains(@class, 'cookie')]"
        ]
        for selector in cookie_selectors:
            try:
                cookie_button = WebDriverWait(self.driver, 1).until(
                    EC.element_to_be_clickable((By.XPATH, selector))
                )
                cookie_button.click()
                break
            except TimeoutException:
                continue
        
    def scrape_list(self):
        # Navigate to the search results page for the configured query/city.
        self.driver.get(self.SEARCH_URL)
        
        # Wait until at least one listing container is present on the page.
        # This avoids brittle fixed sleeps and ensures the DOM is ready.
        try:
            WebDriverWait(self.driver, 5).until(
                EC.presence_of_element_located((By.XPATH, "//div[contains(@class, 'listing-search-item')]"))
            )
        except TimeoutException:
            print("No listings found on page")
        
        # This dict will hold scraped houses keyed as house1, house2, ...
        houses_data = {}
        try:
            # Find all listing containers on the results page.
            property_containers = self.driver.find_elements(By.XPATH, "//div[contains(@class, 'listing-search-item')]")
            if property_containers:
                house_counter = 1
                # Iterate over each container and extract structured data.
                for i, container in enumerate(property_containers, 1):
                    temp_house_data = {}
                    
                    # Extract listing title and absolute URL.
                    try:
                        name_element = container.find_element(By.XPATH, ".//a[contains(@class, 'listing-search-item__link--title')]")
                        name = name_element.text.strip()
                        href = name_element.get_attribute('href')
                        full_url = f"{self.BASE_URL}{href}" if href.startswith('/') else href
                        temp_house_data['name'] = name
                        temp_house_data['url'] = full_url
                    except Exception:
                        # If name/URL is missing, skip this card as it's not actionable.
                        continue
                    
                    # Assign the next sequential key (house1, house2, ...).
                    house_key = f"house{house_counter}"
                    houses_data[house_key] = temp_house_data
                    
                    # Extract address/subtitle if available.
                    try:
                        address_element = container.find_element(By.XPATH, ".//div[contains(@class, 'listing-search-item__sub-title')]")
                        address = address_element.text.strip()
                        houses_data[house_key]['address'] = address
                    except Exception:
                        houses_data[house_key]['address'] = "Address not found"
                    
                    # Extract displayed price if available.
                    try:
                        price_element = container.find_element(By.XPATH, ".//div[contains(@class, 'listing-search-item__price')]")
                        price = price_element.text.strip()
                        houses_data[house_key]['price'] = price
                    except Exception:
                        houses_data[house_key]['price'] = "Price not found"
                    
                    # Extract quick feature bullets (e.g., area, rooms, furnished).
                    try:
                        details_list = []
                        feature_elements = container.find_elements(By.XPATH, ".//ul[contains(@class, 'illustrated-features')]//li")
                        for feature in feature_elements:
                            detail = feature.text.strip()
                            if detail:
                                details_list.append(detail)
                        houses_data[house_key]['details'] = details_list
                    except Exception:
                        houses_data[house_key]['details'] = ["Details not found"]
                    
                    # Move to the next sequential key for the following listing.
                    house_counter += 1
        except Exception as e:
            print(f"Error scraping property details: {e}")
                
        # Immediately persist the raw scrape snapshot for debugging/backup.
        # Later, save_state() will overwrite this same file with processed metadata.
                if houses_data:
            with open(self.PROPERTIES_FILE, "w", encoding="utf-8") as f:
                        json.dump(houses_data, f, indent=2, ensure_ascii=False)
            print(f"Saved scraped data to {self.PROPERTIES_FILE}")
        
        # Return the in-memory structure for further filtering/processing.
        return houses_data

    def filter_new(self, current_houses, processed_houses, seen_urls: set):
        """Select houses that are not seen before AND not yet applied by Adira.
        processed_houses is keyed by URL with processed status; seen_urls is a set of URLs previously observed.
        """
        new_houses = {}
        for house_key, house_data in current_houses.items():
            house_url = house_data.get('url')
            house_name = house_data.get('name')
            house_id = house_url if house_url else house_name
            if not house_id:
                continue
            # Skip if seen before
            if house_url in seen_urls:
                continue
            # Skip if already processed/applied by Adira
            if house_url in processed_houses:
                continue
            new_houses[house_key] = house_data
        return new_houses

    def apply_to_listing(self, house_data):
        driver = self.driver
                        if house_data.get('url') and house_data.get('name'):
                            driver.get(house_data['url'])
            time.sleep(3)  # Give page more time to fully load
                            try:
                                reageer_selectors = [
                                    "//a[contains(text(), 'Reageer op deze woning')]",
                    "//a[contains(text(), ' Reageer op deze woning ')]",
                                    "//a[contains(@class, 'listing-contact-info__button--contact-request')]",
                                    "//a[contains(@href, '/reageer/')]",
                                    "//button[contains(text(), 'Reageer op deze woning')]",
                    "//button[contains(text(), ' Reageer op deze woning ')]",
                                    "//button[contains(text(), 'Bekijk opnieuw')]",
                    "//button[contains(@class, 'listing-contact-info__button--viewed')]",
                    "//a[contains(@class, 'listing-contact-info__button--viewed') and contains(text(), 'Bekijk je reactie')]"
                                ]
                                reageer_button = None
                                button_text = ""
                                for selector in reageer_selectors:
                                    try:
                        reageer_button = WebDriverWait(driver, 3).until(
                                            EC.element_to_be_clickable((By.XPATH, selector))
                                        )
                        button_text = (reageer_button.text or "").strip()
                                        break
                                    except TimeoutException:
                                        continue
                                if reageer_button:
                    # If we already see 'Bekijk je reactie', treat as already applied and skip
                    if "bekijk je reactie" in button_text.lower():
                        return True
                                    reageer_button.click()
                    time.sleep(2)  # Human-like pause after clicking
                                    if "bekijk opnieuw" in button_text.lower():
                                            ga_verder_selectors = [
                                                "//button[contains(text(), 'Ga verder')]",
                                                "//button[contains(@class, 'dialog__external-button')]",
                                                "//button[@type='submit'][contains(text(), 'Ga verder')]"
                                            ]
                                            ga_verder_button = None
                                            for selector in ga_verder_selectors:
                                                try:
                                ga_verder_button = WebDriverWait(driver, 3).until(
                                                        EC.element_to_be_clickable((By.XPATH, selector))
                                                    )
                                                    break
                                                except TimeoutException:
                                                    continue
                                            if ga_verder_button:
                                                ga_verder_button.click()
                            time.sleep(2)  # Human-like pause after popup action
                    # Handle additional cookies
                                        additional_cookie_selectors = [
                                            "//button[contains(text(), 'Alle cookies toestaan')]",
                                            "//button[contains(@class, 'ch2-allow-all-btn')]",
                                            "//button[contains(@class, 'ch2-btn-primary')]"
                                        ]
                                        for selector in additional_cookie_selectors:
                                            try:
                                                additional_cookie_button = WebDriverWait(driver, 2).until(
                                                    EC.element_to_be_clickable((By.XPATH, selector))
                                                )
                            additional_cookie_button.click()
                                                break
                                            except TimeoutException:
                                                continue
                    # Fill motivation textarea
                                        textarea_selectors = [
                                            "//textarea[@name='contact_form[motivation]']",
                                            "//textarea[contains(@class, 'text-control__control')]",
                                            "//textarea[contains(@id, 'text-control')]"
                                        ]
                                        motivation_textarea = None
                                        for selector in textarea_selectors:
                                            try:
                            motivation_textarea = WebDriverWait(driver, 3).until(
                                                    EC.presence_of_element_located((By.XPATH, selector))
                                                )
                                                break
                                            except TimeoutException:
                                                continue
                                        if motivation_textarea:
                                            motivation_textarea.clear()
                                            street_name = house_data['name']
                        application_text = self.DEFAULT_APPLICATION_TEXT.format(street_name=street_name)
                                            motivation_textarea.send_keys(application_text)
                        # Actually submit the motivation (skip click in dry-run)
                        submit_selectors = [
                            "//button[contains(text(), 'Verstuur')]",
                            "//button[contains(text(), 'Verzenden')]",
                            "//button[contains(text(), 'Reageer')]",
                            "//button[@type='submit']",
                            "//form//button[@type='submit']",
                        ]
                        submit_button = None
                        for selector in submit_selectors:
                            try:
                                submit_button = WebDriverWait(driver, 3).until(
                                    EC.element_to_be_clickable((By.XPATH, selector))
                                )
                                break
                            except TimeoutException:
                                continue
                        if submit_button:
                            if not self.dry_run:
                                submit_button.click()
                                time.sleep(2)
                                return True
                            else:
                                print("[DRY-RUN] Filled motivation, skipping submit click")
                                return False
                        else:
                            # If no submit button found, still consider filled but not submitted
                            return False
                                        else:
                                            print("Could not find motivation textarea - skipping to next house")
                                else:
                                    print("'Reageer op deze woning' or 'Bekijk opnieuw' button not found - skipping to next house")
                            except Exception as e:
                                print(f"Error finding application button: {e} - skipping to next house")
                        else:
            print(f"Skipping - missing URL or name")
        return False

    def mark_house_as_processed(self, processed_houses, house_data, success=True):
        house_url = house_data.get('url')
        house_name = house_data.get('name')
        # Internally we deduplicate by URL, but we will serialize as houseN later
        house_id = house_url if house_url else house_name
        if house_id:
            processed_houses[house_id] = {
                'name': house_name,
                'url': house_url,
                'address': house_data.get('address'),
                'price': house_data.get('price'),
                'details': house_data.get('details'),
                'processed_date': time.strftime('%Y-%m-%d %H:%M:%S'),
                'success': success,
            }

        '''TODO: or this code is responsible for creating a url as value'''

    def run(self):
        try:
            # 1) Login as browsing user (User 2) and scrape
            self.ensure_logged_in_role('browse')
            processed_houses = {} if self.dry_run else self.load_state()
            seen_urls = set() if self.dry_run else self.load_seen_urls()
            houses_data = self.scrape_list()
            new_houses_to_process = self.filter_new(houses_data, processed_houses, seen_urls)
            print(f"Found {len(new_houses_to_process)} new houses to process.")
            for house_key, house_data in new_houses_to_process.items():
                print(f"\n--- Processing {house_key}: {house_data.get('name', '')} ---")
                print(f"URL: {house_data.get('url', '')}")
                if self.dry_run:
                    # Stay on browse account and do not submit; just preview listing
                    _ = self.apply_to_listing(house_data)
                else:
                    # 2) Switch to Adira (apply user) to submit the application
                    self.ensure_logged_in_role('apply')
                    success = self.apply_to_listing(house_data)
                    self.mark_house_as_processed(processed_houses, house_data, success)
                    time.sleep(random.randint(2, 5))  # Random delay between houses (2-5s)
            if not self.dry_run:
                # 3) Update seen URLs with all scraped listing URLs
                for _, house in houses_data.items():
                    if house.get('url'):
                        seen_urls.add(house['url'])
                self.save_seen_urls(seen_urls)
                self.save_state(processed_houses)
                print(f"Saved {len(processed_houses)} processed houses to tracking file.")
        finally:
            print("Closing browser...")
            self.driver.quit()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run HouseBot scraper over multiple cycles or hours.")
    parser.add_argument("--cycles", type=int, default=1, help="Number of complete scraping cycles to run (default 1)")
    parser.add_argument("--hours", type=float, default=None, help="Run duration in hours (overrides cycles if shorter)")
    parser.add_argument("--pause", type=int, default=300, help="Seconds to pause between cycles (default 300s)")
    parser.add_argument("--dry-run", action="store_true", help="Open listings but do not submit and do not persist state")
    parser.add_argument("--visible", action="store_true", help="Show browser window (default is headless for server mode)")
    args = parser.parse_args()

    executed = 0
    start_time = time.time()
    while True:
        if args.cycles and executed >= args.cycles:
            break
        if args.hours and (time.time() - start_time) / 3600 >= args.hours:
            break

        bot = HouseBot(dry_run=args.dry_run, headless=not args.visible)
        bot.run()
        executed += 1

        # Respect pause interval unless we're about to exit
        if (args.cycles and executed >= args.cycles) or (
            args.hours and (time.time() - start_time) / 3600 >= args.hours
        ):
            break
        time.sleep(args.pause)

