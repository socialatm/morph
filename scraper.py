import requests
from bs4 import BeautifulSoup
import pandas as pd
import re
import time
import dateutil

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

def run_scraper() -> pd.DataFrame:
    """
    Orchestrates the entire scraping process.
    1. Fetches the main page to get all fight card links.
    2. Scrapes each individual fight card page.
    3. Collects the data and returns it as a pandas DataFrame.
    """
    # A list to hold a dictionary for each valid fight record
    all_fight_records = []
    base_url = "http://www.betmma.tips/"

    # 1. Get all fight page links
    data = requests.get("http://www.betmma.tips/mma_betting_favorites_vs_underdogs.php?Org=1")
    soup = BeautifulSoup(data.text, "html.parser")

    # table with 98% width 
    table = soup.find('table', {'width': "98%"})
    # find all links in that table
    links = table.find_all('a', href=True)

    # append all links to a list 
    all_links = []
    for link in links:
        all_links.append(base_url + link.get('href'))

    # 2. Scrape each page and collect fight records
    for link in all_links:
        print(f"Now scraping: {link}")

        data = requests.get(link)
        soup = BeautifulSoup(data.text, 'html.parser')
        time.sleep(2) # Be respectful to the server

        # --- Fetch page-level data ONCE per page for efficiency ---
        h1 = soup.find("h1")
        event_name = h1.text if h1 else "Unknown Event"

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
    df = run_scraper()
    if not df.empty:
        print(f"\nSuccessfully scraped {df.shape[0]} fights.")
        print(f"Last fight card was: {df.iloc[-1]['Events']} in {df.iloc[-1]['Location']}")
        print("\nWin breakdown:")
        print(df["Who_won"].value_counts(normalize=True))
        
        # Save df to a csv file
        df.to_csv('odds_data.csv', index=False)
        print("\nData saved to odds_data.csv")
    else:
        print("Scraping complete, but no data was found.")
