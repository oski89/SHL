
import os
import time
import pickle
import csv
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

COOKIE_FILE = "shl_cookies.pkl"
CSV_FILE = "shl_player_stats.csv"
URL = "https://fantasy.shl.se/app/transfer"

def create_browser(headless=False):
    options = Options()
    if headless:
        options.add_argument("--headless")
    options.add_argument("--disable-gpu")
    options.add_argument("--window-size=1920,1080")
    options.add_argument("--disable-blink-features=AutomationControlled")
    driver = webdriver.Chrome(options=options)
    return driver

def load_cookies(driver, cookie_file):
    if os.path.exists(cookie_file):
        with open(cookie_file, "rb") as f:
            cookies = pickle.load(f)
        driver.get("https://fantasy.shl.se")
        for cookie in cookies:
            driver.add_cookie(cookie)
        driver.get(URL)
        return True
    return False

def save_cookies(driver, cookie_file):
    with open(cookie_file, "wb") as f:
        pickle.dump(driver.get_cookies(), f)

def start_scrape_session():
    first_time_login = not os.path.exists(COOKIE_FILE)
    driver = create_browser(headless=not first_time_login)

    if not load_cookies(driver, COOKIE_FILE):
        print("Please log in manually using Google in the browser.")
        driver.get("https://fantasy.shl.se")
        input("After logging in and opening 'Alla Spelare', press Enter to continue...")
        save_cookies(driver, COOKIE_FILE)

    driver.get(URL)
    time.sleep(5)
    return driver

def normalize_label(text):
    return text.lower().replace(" ", "_").replace("ä", "a").replace("ö", "o").replace("/", "_")

def get_stat_headers(driver):
    try:
        header_cells = driver.find_elements(By.CSS_SELECTOR, "thead th")
        headers = []
        for i, cell in enumerate(header_cells):
            title = cell.get_attribute("title").strip() if cell.get_attribute("title") else ""
            text = cell.text.strip()
            raw = title or text or f"stat_{i+1}"
            label = normalize_label(raw)
            # Remove "poang_for_" prefix from labels 4 to 22 (adjusting by 3 for name/pos/price)
            if 3 <= i < 22 and label.startswith("poang_for_"):
                label = label.replace("poang_for_", "")
            headers.append(label)
        print("Detected column headers:", headers)
        return headers
    except Exception as e:
        print("Failed to extract headers:", e)
        return []

def scrape_player_stats(driver):
    from selenium.webdriver.common.by import By
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC

    WebDriverWait(driver, 10).until(
        EC.element_to_be_clickable((By.XPATH, "//a[@data-target='#allplayers']"))
    ).click()
    time.sleep(5)

    players = []
    stat_labels = get_stat_headers(driver)
    player_rows = driver.find_elements(By.CSS_SELECTOR, "tr.player-line")

    for row in player_rows:
        try:
            name = row.find_element(By.CSS_SELECTOR, ".name").text
            position = row.find_element(By.CSS_SELECTOR, ".pos").text
            price = row.find_element(By.CSS_SELECTOR, ".value").text
            stat_cells = row.find_elements(By.CSS_SELECTOR, "td.points")
            stats = [cell.text for cell in stat_cells]

            player_data = {
                "name": name,
                "position": position,
                "price": price
            }

            for i, stat in enumerate(stats):
                key = stat_labels[i + 3] if i + 3 < len(stat_labels) else f"stat_{i+1}"
                player_data[key] = stat

            # Skip rows with no meaningful data
            if any(value.strip() for value in player_data.values() if isinstance(value, str)):
                players.append(player_data)
        except Exception:
            continue

    print(f"Extracted {len(players)} players.")
    return players

def export_to_csv(players, filename):
    import pandas as pd

    if not players:
        print("No data to export.")
        return

    df = pd.DataFrame(players)

    # Drop columns that are entirely empty (like stat_24/stat_25)
    df.dropna(axis=1, how='all', inplace=True)

    # Save cleaned DataFrame
    df.to_csv(filename, index=False)
    print(f"Data exported to {filename}")

if __name__ == "__main__":
    driver = start_scrape_session()
    try:
        players = scrape_player_stats(driver)
        export_to_csv(players, CSV_FILE)
    finally:
        driver.quit()
