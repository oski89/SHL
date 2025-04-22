
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

def navigate_to_all_players_tab(driver):
    try:
        # Use XPath to click the correct tab by its data-target
        all_players_tab = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.XPATH, "//a[@data-target='#allplayers']"))
        )
        all_players_tab.click()
        time.sleep(3)
    except Exception as e:
        print("Could not navigate to 'Alla Spelare' tab:", e)

def get_stat_headers(driver):
    try:
        header_cells = driver.find_elements(By.CSS_SELECTOR, "thead tr th.data")
        return [cell.text.strip().lower().replace(" ", "_") for cell in header_cells]
    except:
        return []

def scrape_player_stats(driver):
    navigate_to_all_players_tab(driver)
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
                key = stat_labels[i] if i < len(stat_labels) else f"stat_{i+1}"
                player_data[key] = stat

            players.append(player_data)
        except Exception as e:
            continue

    print(f"Extracted {len(players)} players.")
    return players

def export_to_csv(players, filename):
    if not players:
        print("No data to export.")
        return
    keys = players[0].keys()
    with open(filename, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=keys)
        writer.writeheader()
        writer.writerows(players)
    print(f"Data exported to {filename}")

if __name__ == "__main__":
    driver = start_scrape_session()
    try:
        players = scrape_player_stats(driver)
        export_to_csv(players, CSV_FILE)
    finally:
        driver.quit()
