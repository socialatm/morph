
# MMA Odds Scraper

This Python script scrapes historical MMA fight data, including betting odds, from [betmma.tips](http://www.betmma.tips/). It is designed to be run periodically to collect new fight results and append them to a local CSV file, `odds_data.csv`.

## Features

- **Fetches Event Data**: Scrapes all UFC fight events listed on the site.
- **Detailed Fight Scraping**: For each event, it scrapes individual fight details: fighters, winner, and decimal odds.
- **Odds Conversion**: Converts decimal odds to the more common American odds format (e.g., -110, +150).
- **Structured Output**: Saves the collected data into a clean, structured `odds_data.csv` file.
- **Incremental Scraping**: On subsequent runs, the script reads the existing `odds_data.csv` to identify and skip events that have already been processed. This saves time, avoids duplicate data, and reduces server load.

## Requirements

- Python 3.x
- The script requires the following Python libraries:
  - `requests`
  - `beautifulsoup4`
  - `pandas`
  - `python-dateutil`

You can install all dependencies using `pip`:

```bash
pip install requests beautifulsoup4 pandas python-dateutil
```

It is highly recommended to use a Python virtual environment to manage project dependencies.

## Usage

1.  Clone or download the repository.
2.  Install the required libraries as described above.
3.  Run the script from your terminal:

```bash
python scraper.py
```

The script will print its progress to the console, indicating if it's reading existing data and which new events it is currently scraping.

Upon completion, it will create or update the `odds_data.csv` file in the same directory.

## Output Data (`odds_data.csv`)

The script generates a CSV file with the following columns:

| Column      | Description                                                                 | Example                               |
|-------------|-----------------------------------------------------------------------------|---------------------------------------|
| `Events`    | The name of the event.                                                      | `UFC Fight Night: Lewis vs. Nascimento` |
| `Location`  | The city and state/country where the event took place.                      | `St. Louis, Missouri, USA`            |
| `Date`      | The date of the event in `YYYY-MM-DD` format.                               | `2024-05-11`                          |
| `R_fighter` | The name of the fighter in the "Red Corner" (listed first on the site).     | `Derrick Lewis`                       |
| `B_fighter` | The name of the fighter in the "Blue Corner" (listed second on the site).   | `Rodrigo Nascimento`                  |
| `Winner`    | The name of the fighter who won the match.                                  | `Derrick Lewis`                       |
| `R_odds`    | The American odds for the Red Corner fighter.                               | `-155`                                |
| `B_odds`    | The American odds for the Blue Corner fighter.                              | `135`                                 |
| `Favorite`  | The name of the fighter who was the betting favorite (lower negative odds). | `Derrick Lewis`                       |
| `Who_won`   | A label indicating if the 'favorite' or 'underdog' won the fight.           | `favorite`                            |


## Disclaimer

- This script is for educational and personal use only.
- Web scraping may be against the terms of service of some websites. Please use this script responsibly.
- The script includes a 2-second delay between requests to be respectful of the website's servers and to minimize server load.
- The structure of the target website may change over time, which could break the scraper. If it stops working, the script's parsing logic may need to be updated to match the new site structure.
