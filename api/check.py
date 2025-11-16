from utils.scrape import fetch_kaspi
from utils.emailer import send_email
import os

PRODUCT_URL = "https://kaspi.kz/shop/p/ehrmann-puding-vanil-bezlaktoznyi-1-5-200-g-102110634/?c=750000000"
TARGET_PHRASE = "В наличии"

def handler(request, response):
    try:
        html = fetch_kaspi(PRODUCT_URL)

        if isinstance(html, dict) and "error" in html:
            return response.status(500).json(html)

        if TARGET_PHRASE.lower() in html.lower():
            send_email("Товар появился!", f"Товар в наличии:\n{PRODUCT_URL}")

        return response.status(200).json({"status": "checked"})

    except Exception as e:
        return response.status(500).json({"error": str(e)})
