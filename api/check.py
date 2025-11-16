import os
import json
from http.server import BaseHTTPRequestHandler
import requests
from bs4 import BeautifulSoup
from email.mime.text import MIMEText
import smtplib


PRODUCT_URL = "https://kaspi.kz/shop/p/ehrmann-puding-vanil-bezlaktoznyi-1-5-200-g-102110634/?c=750000000"


def send_email(status_text):
    EMAIL_FROM = os.environ.get("EMAIL_FROM")
    EMAIL_TO = os.environ.get("EMAIL_TO")
    EMAIL_PASS = os.environ.get("EMAIL_PASS")

    if not EMAIL_FROM or not EMAIL_TO or not EMAIL_PASS:
        return {"email": "Email переменные окружения не заданы"}

    msg = MIMEText(f"Товар появился!\n\nСтатус: {status_text}\n\nСсылка: {PRODUCT_URL}")
    msg["Subject"] = "Kaspi Checker: Товар в наличии!"
    msg["From"] = EMAIL_FROM
    msg["To"] = EMAIL_TO

    try:
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(EMAIL_FROM, EMAIL_PASS)
            server.sendmail(EMAIL_FROM, EMAIL_TO, msg.as_string())
        return {"email": "sent"}
    except Exception as e:
        return {"email_error": str(e)}


def parse_kaspi(html):
    soup = BeautifulSoup(html, "html.parser")

    # === Проверка meta-тега (самый правильный вариант) ===
    meta = soup.find("meta", {"property": "product:availability"})
    if meta:
        content = meta.get("content", "").lower()
        if content == "in stock":
            return True, "in stock"
        return False, content

    # === Проверка JSON-LD ===
    for script in soup.find_all("script", {"type": "application/ld+json"}):
        try:
            data = json.loads(script.string.strip())
            if isinstance(data, dict) and data.get("@type") == "Product":
                offers = data.get("offers", [])
                if isinstance(offers, dict):
                    offers = [offers]

                for o in offers:
                    avail = o.get("availability", "").lower()
                    if "instock" in avail:
                        return True, "in stock"
                    if "outofstock" in avail:
                        return False, "out of stock"
        except:
            pass

    # === Проверка window.digitalData ===
    for script in soup.find_all("script"):
        if script.string and "digitalData" in script.string:
            if '"stock":0' in script.string:
                return False, "stock: 0"
            if '"stock":' in script.string:
                return True, "stock > 0"

    return False, "no availability info"


def check():
    SCRAPER_API_KEY = os.environ.get("SCRAPER_API_KEY")
    if not SCRAPER_API_KEY:
        return {"error": "SCRAPER_API_KEY не задан"}

    scraper_url = f"https://api.scraperapi.com/?api_key={SCRAPER_API_KEY}&render=true&url={PRODUCT_URL}"

    try:
        r = requests.get(scraper_url, timeout=25)
        r.raise_for_status()
    except Exception as e:
        return {"error": f"ScraperAPI error: {str(e)}"}

    available, status_text = parse_kaspi(r.text)

    if available:
        send_email(status_text)

    return {
        "available": available,
        "status": status_text,
        "product": PRODUCT_URL,
    }


class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        result = check()
        self.send_response(200)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.end_headers()
        self.wfile.write(json.dumps(result, ensure_ascii=False).encode("utf-8"))
