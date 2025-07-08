import requests
from bs4 import BeautifulSoup
import pandas as pd
import re
import time

all_links = []
location = []
events = []
f1 = []
f2 = []
winner = []
f1_odds = []
f2_odds = []
label = []
favorite = []

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

            # event name
            h1 = soup.find("h1")
            # location and date
            h2 = soup.find("h2")
            
            events.append(h1.text)
            location.append(h2.text)

            odds_f1 = float(odds[2].text.strip(" @"))
            odds_f2 = float(odds[3].text.strip(" @"))

            f1_odds.append(odds_f1)
            f2_odds.append(odds_f2)

            # how to generate label
            odds_dict = {}
            odds_dict[odds[0].text] = odds_f1
            odds_dict[odds[1].text] = odds_f2 

            if odds_dict["WON"] > odds_dict["LOST"]:
                label.append("Underdog")
            else:
                label.append("Favorite")

            if odds_f1 > odds_f2:
                favorite.append("f2")
            else:
                favorite.append("f1")

            fighters = row.find_all('a', attrs={'href': re.compile("^fighter_profile.php")})
            f1.append(fighters[0].text)
            f2.append(fighters[1].text)
            winner.append(fighters[2].text)
    return None

def create_df():
    
    # creating dataframe
    df = pd.DataFrame()
    df["Events"] = events
    df["Location"] = location
    df["Fighter1"] = f1
    df["Fighter2"] = f2
    df["Winner"] = winner
    df["fighter1_odds"] = f1_odds
    df["fighter2_odds"] = f2_odds
    df["Favorite"] = favorite
    df["Label"] = label
    print(f"Successfully scraped {df.shape[0]} fights and last fight card was {df.iloc[-1, :]['Events']} {df.iloc[-1, :]['Location']}")
    print(df["Label"].value_counts()/len(df))
    
    return df
   
scrape_data()
df = create_df()

# save df to a csv file named odds_data.csv
df.to_csv('odds_data.csv', index=False)
