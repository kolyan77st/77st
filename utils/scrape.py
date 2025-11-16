import os
import requests

SCRAPER_API_KEY = "1dce65ac856e10799e7642538823c786"

def fetch_kaspi(url):
    api_url = (
        "https://api.scraperapi.com/"
        "?api_key=" + SCRAPER_API_KEY +
        "&url=" + url +
        "&country=KZ"
        "&render=true"
        "&premium=true"
        "&timeout=60000"
    )

    try:
        r = requests.get(api_url, timeout=65)
        r.raise_for_status()
        return r.text

    except Exception as e:
        return {"error": f"ScraperAPI error: {str(e)}"}    
