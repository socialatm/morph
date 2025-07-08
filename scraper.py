import requests
from bs4 import BeautifulSoup
import pandas as pd
import re
import time
import dateutil
import os

def convert_decimal_to_american(decimal_odds: float) -> int:
    """
    Converts decimal (digital) odds to American odds.
    Args:
        decimal_odds: The decimal odds, which must be greater than 1.0.
    Returns:
        The equivalent American odds as an integer.
        Returns None if the input is invalid.
    """
    if not isinstance(decimal_odds, (int, float)) or decimal_odds <= 1.0:
        # Silently return None for invalid odds, as we handle this in the main loop.
        return None

    if decimal_odds >= 2.0:
        # This is an underdog or even money bet.
        american_odds = (decimal_odds - 1) * 100
    else:
        # This is a favorite.
        american_odds = -100 / (decimal_odds - 1)

    return int(round(american_odds))

def run_scraper(existing_events: set) -> pd.DataFrame:
    """
    Orchestrates the entire scraping process.
    1. Fetches the main page to get all fight card links.
    2. Scrapes each individual fight card page for events not already scraped.
    3. Collects the new data and returns it as a pandas DataFrame.
    """
    # A list to hold a dictionary for each valid fight record
    all_fight_records = []
    base_url = "http://www.betmma.tips/"

    # 1. Get all fight page links
    try:
        data = requests.get("http://www.betmma.tips/mma_betting_favorites_vs_underdogs.php?Org=1")
        data.raise_for_status() # Raise an exception for bad status codes
    except requests.exceptions.RequestException as e:
        print(f"Error fetching main page: {e}")
        return pd.DataFrame() # Return empty DataFrame on failure
    
    soup = BeautifulSoup(data.text, "html.parser")

    # table with 98% width 
    table = soup.find('table', {'width': "98%"})
    # find all links in that table
    links = table.find_all('a', href=True)

    # Create a list of (event_name, url) tuples, skipping existing ones
    all_links = []
    for link in links:
        event_name_from_link = link.text.strip()
        if event_name_from_link in existing_events:
            continue # Skip this event as it's already been scraped
        all_links.append((event_name_from_link, base_url + link.get('href')))

    if not all_links:
        return pd.DataFrame()

    print(f"Found {len(all_links)} new events to scrape.")
    # 2. Scrape each page and collect fight records
    for event_name_from_link, link in all_links:
        print(f"Now scraping: {event_name_from_link}")

        data = requests.get(link)
        soup = BeautifulSoup(data.text, 'html.parser')
        time.sleep(2) # Be respectful to the server

        # --- Fetch page-level data ONCE per page for efficiency ---
        h1 = soup.find("h1")
        event_name = h1.text.strip() if h1 else event_name_from_link

        h2 = soup.find("h2")
        loc, dt = None, None
        if h2 and h2.text:
            parts = h2.text.split(';', 1)
            loc = parts[0].strip()
            if len(parts) == 2:
                try:
                    parsed_date = dateutil.parser.parse(parts[1].strip())
                    dt = parsed_date.strftime('%Y-%m-%d')
                except (dateutil.parser.ParserError, TypeError):
                    dt = None # Keep date as None if parsing fails

        # --- Find all fight rows on the page and process them ---
        rows = soup.find_all('table', {'cellspacing': "5"})
        for row in rows:
            odds = row.find_all('td', {'align': "center", 'valign': "middle"})
            # Skip if it's not a valid fight row (e.g., a draw)
            if odds[0].text not in ['WON', 'LOST']:
                continue

            try:
                dec_odds1 = float(odds[2].text.strip(" @"))
                dec_odds2 = float(odds[3].text.strip(" @"))
            except ValueError:
                continue

            # Skip if odds are infinite or invalid
            if dec_odds1 == float('inf') or dec_odds2 == float('inf'):
                continue

            odds_f1_val = convert_decimal_to_american(dec_odds1)
            odds_f2_val = convert_decimal_to_american(dec_odds2)
            if odds_f1_val is None or odds_f2_val is None:
                continue

            # Extract fighters, winner, and determine favorite/label
            odds_dict = {odds[0].text: odds_f1_val, odds[1].text: odds_f2_val}
            label_val = "underdog" if odds_dict["WON"] > odds_dict["LOST"] else "favorite"

            fighters = row.find_all('a', attrs={'href': re.compile("^fighter_profile.php")})
            # Ensure we have enough fighter links before trying to access them
            if len(fighters) < 3:
                continue

            # If all data is valid, create a dictionary for this fight and append it
            fight_record = {
                "Events": event_name,
                "Location": loc,
                "Date": dt,
                "R_fighter": fighters[0].text,
                "B_fighter": fighters[1].text,
                "Winner": fighters[2].text,
                "R_odds": odds_f1_val,
                "B_odds": odds_f2_val,
                "Favorite": fighters[0].text if odds_f1_val < odds_f2_val else fighters[1].text,
                "Who_won": label_val
            }
            all_fight_records.append(fight_record)

    # 3. Create and return the final DataFrame
    return pd.DataFrame(all_fight_records)

if __name__ == "__main__":
    CSV_FILE = 'odds_data.csv'
    existing_events = set()
    existing_df = pd.DataFrame()

    # Check if the file exists and load existing data
    if os.path.exists(CSV_FILE):
        print(f"Found existing data in {CSV_FILE}. Reading...")
        try:
            existing_df = pd.read_csv(CSV_FILE)
            if not existing_df.empty:
                existing_events = set(existing_df['Events'].unique())
                print(f"Loaded {len(existing_events)} unique events. Will skip them if found.")
        except (pd.errors.EmptyDataError, KeyError) as e:
            print(f"Warning: {CSV_FILE} is empty or malformed ({e}). Starting fresh.")
            existing_df = pd.DataFrame()
    else:
        print(f"{CSV_FILE} not found. Starting a new scrape.")

    # Run the scraper, passing the set of events to skip
    new_df = run_scraper(existing_events)

    if not new_df.empty:
        print(f"\nSuccessfully scraped {new_df.shape[0]} new fights from {len(new_df['Events'].unique())} new events.")
        combined_df = pd.concat([existing_df, new_df], ignore_index=True)
        print(f"Total fights in dataset: {combined_df.shape[0]}")

        combined_df.to_csv(CSV_FILE, index=False)
        print(f"\nData updated and saved to {CSV_FILE}")
    else:
        print("\nScraping complete. No new events found to add.")
