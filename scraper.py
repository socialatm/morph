import requests
from bs4 import BeautifulSoup
import pandas as pd
import re
import time
import dateutil

all_links = []
location = []
date = []
events = []
f1 = []
f2 = []
winner = []
f1_odds = []
f2_odds = []
label = []
favorite = []

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
        print("Error: Invalid decimal odds. Must be a number greater than 1.0.")
        return None

    if decimal_odds >= 2.0:
        # This is an underdog or even money bet.
        american_odds = (decimal_odds - 1) * 100
    else:
        # This is a favorite.
        american_odds = -100 / (decimal_odds - 1)

    return int(round(american_odds))

def scrape_data():
    # set up page to extract table
    data = requests.get("http://www.betmma.tips/mma_betting_favorites_vs_underdogs.php?Org=1")
    soup = BeautifulSoup(data.text, 'html.parser')

    # table with 98% width 
    table = soup.find('table', {'width': "98%"})
    # find all links in that table
    links = table.find_all('a', href=True)

    # append all links to a list 
    for link in links:
        all_links.append("https://www.betmma.tips/"+link.get('href'))

    # test for one use case
    for link in all_links:
    # for link in all_links[:5]:    # use for testing
        print(f"Now scraping: {link}")

        data = requests.get(link)
        soup = BeautifulSoup(data.text, 'html.parser')
        time.sleep(2)
        # specific table with the information
        rows = soup.find_all('table', {'cellspacing': "5"})

        for row in rows:

            # check for draw, if draw, then skip
            # dictionary of won and lost
            odds = row.find_all('td', {'align': "center", 'valign': "middle"})
            # to avoid taking in draws
            if odds[0].text not in ['WON', 'LOST']:
                continue

            # --- Extract all data for the row into temporary variables first ---

            # event name
            h1 = soup.find("h1")
            event_name = h1.text

            # location and date
            h2 = soup.find("h2")
            loc, dt = None, None
            if h2 and h2.text:
                parts = h2.text.split(';', 1)
                if len(parts) == 2:
                    loc = parts[0].strip()
                    try:
                        parsed_date = dateutil.parser.parse(parts[1].strip())
                        dt = parsed_date.strftime('%Y-%m-%d')
                    except (dateutil.parser.ParserError, TypeError):
                        dt = None
                else:
                    loc = parts[0].strip()
            
            # Convert and validate odds
            try:
                dec_odds1 = float(odds[2].text.strip(" @"))
                dec_odds2 = float(odds[3].text.strip(" @"))
            except ValueError:
                continue

            if dec_odds1 == float('inf') or dec_odds2 == float('inf'):
                continue

            odds_f1_val = convert_decimal_to_american(dec_odds1)
            odds_f2_val = convert_decimal_to_american(dec_odds2)

            if odds_f1_val is None or odds_f2_val is None:
                continue

            # generate label, fighters, winner, and favorite
            odds_dict = {odds[0].text: odds_f1_val, odds[1].text: odds_f2_val}
            label_val = "underdog" if odds_dict["WON"] > odds_dict["LOST"] else "favorite"

            fighters = row.find_all('a', attrs={'href': re.compile("^fighter_profile.php")})
            f1_val = fighters[0].text
            f2_val = fighters[1].text
            winner_val = fighters[2].text
            favorite_val = f1_val if odds_f1_val < odds_f2_val else f2_val

            # --- If we've reached this point, the row is valid. Append all data at once. ---
            events.append(event_name)
            location.append(loc)
            date.append(dt)
            f1.append(f1_val); f2.append(f2_val); winner.append(winner_val)
            f1_odds.append(odds_f1_val); f2_odds.append(odds_f2_val)
            favorite.append(favorite_val); label.append(label_val)
    return None

def create_df():
    
    # creating the dataframe
    df = pd.DataFrame()
    df["Events"] = events
    df["Location"] = location
    df["Date"] = date
    df["R_fighter"] = f1
    df["B_fighter"] = f2
    df["Winner"] = winner
    df["R_odds"] = f1_odds
    df["B_odds"] = f2_odds
    df["Favorite"] = favorite
    df["Who_won"] = label
    print(f"Successfully scraped {df.shape[0]} fights and last fight card was {df.iloc[-1, :]['Events']} {df.iloc[-1, :]['Location']}")
    print(df["Who_won"].value_counts()/len(df))
    
    return df
   
scrape_data()
df = create_df()

# save df to a csv file named odds_data.csv
df.to_csv('odds_data.csv', index=False)
# df.to_csv('test.csv', index=False) # use for testing
