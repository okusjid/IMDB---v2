# IMDb Actor Data Extractor

This project is a web scraper designed to extract actor data, including personal information like birth dates, cities, and official websites from IMDb full cast pages. The tool uses Python libraries such as `requests`, `BeautifulSoup`, and `Selenium` to navigate through IMDb pages, collect actor details, and save the extracted data into a JSON file.

## Features

- **Extract Actor Information**: Fetches details like name, image URL, birth date, birth city, spouse, height, and official websites for actors listed on a movie or show’s IMDb full cast page.
- **Saves Data to JSON**: The extracted actor data is saved to a JSON file, allowing easy access and further processing.
- **Handles Pagination and Dynamic Content**: Utilizes Selenium to handle dynamic web pages and scrolling where necessary.
- **Efficient Data Processing**: Processes actor data in batches to optimize performance and minimize memory usage.

## Installation

### Prerequisites

Make sure you have the following tools installed:
- **Python 3.x**
- **pip** (Python package installer)
- **ChromeDriver** for Selenium (ensure it matches your Chrome version).

### Python Libraries

Install the required Python libraries by running:

```bash
pip install requests beautifulsoup4 selenium
```
# IMDb Actor Scraper Setup

## Selenium ChromeDriver Setup

1. **Download ChromeDriver**: Download the ChromeDriver from [here](https://sites.google.com/chromium.org/driver/downloads) and place it in your system's PATH.

## Usage

### 1. Configure IMDb URL
- Update the IMDb URL in the `main()` function for the movie or TV show you want to scrape.

### 2. Run the Script
- To run the scraper, execute the following command:
    ```bash
    python play.py
    ```

This will open a browser instance, navigate to the IMDb full cast page, extract the actor data, and save it to a JSON file.

## Output File

The extracted actor data will be saved in `actor_data.json` in the following format:

```json
{
    "name": "Actor Name",
    "image_url": "https://image-link",
    "url": "https://www.imdb.com/name/actor_id",
    "personal_details": {
        "born": "Month Day, Year",
        "born_city": "City, State, Country",
        "height": "Height",
        "spouse": "Spouse Name",
        "official_sites": [
            {
                "site_name": "Instagram",
                "site_link": "https://instagram.com/actorprofile"
            }
        ]
    }
}
```
