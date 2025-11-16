import os
import json
from http.server import BaseHTTPRequestHandler
import requests
from bs4 import BeautifulSoup
import smtplib
from email.mime.text import MIMEText

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
def send_email(product_url, availability_text):
    EMAIL_FROM = os.environ.get("EMAIL_FROM")
    EMAIL_TO = os.environ.get("EMAIL_TO")
    EMAIL_PASS = os.environ.get("EMAIL_PASS")

    if not EMAIL_FROM or not EMAIL_TO or not EMAIL_PASS:
        print("[send_email] Email переменные не заданы")
        return {"email_error": "Email переменные не заданы"}

    msg = MIMEText(f"Товар появился на Kaspi!\nСтатус: {availability_text}\nСсылка: {product_url}")
    msg["Subject"] = "🔔 Kaspi Checker: Товар в наличии!"
    msg["From"] = EMAIL_FROM
    msg["To"] = EMAIL_TO

    try:
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(EMAIL_FROM, EMAIL_PASS)
            server.sendmail(EMAIL_FROM, EMAIL_TO, msg.as_string())
        print("[send_email] Email отправлен")
    except Exception as e:
        print(f"[send_email] Ошибка при отправке email: {e}")
        return {"email_error": str(e)}

# --- Основная логика ---
def check_availability():
    try:
        product_url = "https://kaspi.kz/shop/p/ehrmann-slivki-10-100-ml-100230406/?c=750000000"
        SCRAPER_API_KEY = os.environ.get("SCRAPER_API_KEY")
        if not SCRAPER_API_KEY:
            return {"error": "SCRAPER_API_KEY не задан!"}

        # ScraperAPI с рендерингом JS
        scraper_url = f"https://api.scraperapi.com/?api_key={SCRAPER_API_KEY}&render=true&url={product_url}"

        try:
            r = requests.get(scraper_url, timeout=20)
            r.raise_for_status()
            soup = BeautifulSoup(r.text, "html.parser")
        except Exception as e:
            return {"error": f"Ошибка ScraperAPI: {str(e)}"}

        # --- Парсинг наличия товара ---
        availability_text = ""
        available = False

        el = soup.select_one(".sellers-table__in-stock")
        if el:
            availability_text = el.get_text(strip=True).lower()
            available = any(word in availability_text for word in ["в наличии", "есть", "выбрать"])
        else:
            availability_text = "Статус товара не найден"

        was_available = read_log()

        email_result = None
        if available and not was_available:
            email_result = send_email(product_url, availability_text)
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
        return {"error": f"Unexpected error: {str(e)}"}

# --- Vercel Serverless Handler ---
class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        try:
            result = check_availability()

            self.send_response(200)
            self.send_header('Content-Type', 'application/json; charset=utf-8')
            self.end_headers()

            self.wfile.write(json.dumps(result, ensure_ascii=False).encode('utf-8'))

        except Exception as e:
            self.send_response(500)
            self.send_header('Content-Type', 'application/json; charset=utf-8')
            self.end_headers()

            self.wfile.write(json.dumps({"error": str(e)}, ensure_ascii=False).encode('utf-8'))
