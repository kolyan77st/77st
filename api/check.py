import os
import requests
from bs4 import BeautifulSoup
import smtplib
from email.mime.text import MIMEText
from fastapi import FastAPI

LOG_FILE = "/tmp/was_available.txt"

# --- Работа с логом ---
def read_log() -> bool:
    try:
        with open(LOG_FILE, "r") as f:
            return f.read().strip().lower() == "true"
    except FileNotFoundError:
        return False
    except Exception as e:
        print(f"[read_log] Ошибка: {e}")
        return False

def write_log(value: bool):
    try:
        with open(LOG_FILE, "w") as f:
            f.write("true" if value else "false")
    except Exception as e:
        print(f"[write_log] Ошибка: {e}")

# --- Отправка email ---
def send_email(product_url):
    EMAIL_FROM = os.environ.get("EMAIL_FROM")
    EMAIL_TO = os.environ.get("EMAIL_TO")
    EMAIL_PASS = os.environ.get("EMAIL_PASS")

    if not EMAIL_FROM or not EMAIL_TO or not EMAIL_PASS:
        print("[send_email] Email переменные не заданы")
        return {"email_error": "Email переменные не заданы"}

    msg = MIMEText(f"Товар появился на Kaspi:\n{product_url}")
    msg["Subject"] = "Kaspi Checker: Товар в наличии!"
    msg["From"] = EMAIL_FROM
    msg["To"] = EMAIL_TO

    try:
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(EMAIL_FROM, EMAIL_PASS)
            server.sendmail(EMAIL_FROM, EMAIL_TO, msg.as_string())
        print("[send_email] Email отправлен")
    except Exception as e:
        print(f"[send_email] Ошибка: {e}")
        return {"email_error": str(e)}

# --- Основная логика ---
def handler():
    try:
        product_url = "https://kaspi.kz/shop/p/ehrmann-puding-vanil-bezlaktoznyi-1-5-200-g-102110634/?c=750000000"
        SCRAPER_API_KEY = os.environ.get("SCRAPER_API_KEY")
        if not SCRAPER_API_KEY:
            return {"error": "SCRAPER_API_KEY не задан!"}

        scraper_url = f"https://api.scraperapi.com/?api_key={SCRAPER_API_KEY}&url={product_url}"

        # --- Запрос к ScraperAPI ---
        try:
            r = requests.get(scraper_url, timeout=15)
            r.raise_for_status()
            soup = BeautifulSoup(r.text, "html.parser")
        except Exception as e:
            return {"error": f"Ошибка ScraperAPI: {str(e)}"}

        # --- Парсинг наличия товара ---
        availability_text = ""
        try:
            el = soup.select_one("div.product__header .status")
            if el:
                availability_text = el.get_text(strip=True).lower()
            else:
                el2 = soup.select_one(".sellers-table__in-stock")
                if el2:
                    availability_text = el2.get_text(strip=True).lower()
        except Exception as e:
            print(f"[handler] Ошибка парсинга HTML: {e}")

        available = any(x in availability_text for x in ["в наличии", "есть", "доступно"])
        was_available = read_log()

        email_result = None
        if available and not was_available:
            email_result = send_email(product_url)
            write_log(True)
        elif not available and was_available:
            write_log(False)

        return {
            "available": available,
            "was_available": was_available,
            "statusText": availability_text,
            "email_result": email_result
        }

    except Exception as e:
        return {"error": f"Unexpected error in handler: {str(e)}"}

# --- FastAPI ---
app = FastAPI()

@app.get("/api/check")
def check_api():
    try:
        return handler()
    except Exception as e:
        return {"error": f"Unexpected error in API: {str(e)}"}
