
import os
import time
import pickle
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By

COOKIE_FILE = "shl_cookies.pkl"
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

def scrape_player_stats(driver):
    time.sleep(5)  # Wait for JavaScript rendering

    players = []
    # Try to identify player card or row structure by common container
    player_cards = driver.find_elements(By.CSS_SELECTOR, ".player-card, .PlayerCard__container, .player-row")

    for card in player_cards:
        try:
            name = card.find_element(By.CSS_SELECTOR, ".player-name, .PlayerCard__name").text
            team = card.find_element(By.CSS_SELECTOR, ".player-team, .PlayerCard__team").text
            position = card.find_element(By.CSS_SELECTOR, ".player-position, .PlayerCard__position").text
            price = card.find_element(By.CSS_SELECTOR, ".player-price, .PlayerCard__price").text
            points = card.find_element(By.CSS_SELECTOR, ".player-points, .PlayerCard__points").text

            players.append({
                "name": name,
                "team": team,
                "position": position,
                "price": price,
                "points": points
            })
        except Exception as e:
            continue

    print(f"Extracted {len(players)} players.")
    for p in players[:10]:  # Preview first 10 players
        print(p)

if __name__ == "__main__":
    driver = start_scrape_session()
    try:
        scrape_player_stats(driver)
    finally:
        driver.quit()
