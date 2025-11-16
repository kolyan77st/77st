import os
import requests
from bs4 import BeautifulSoup
import smtplib
from email.mime.text import MIMEText
from fastapi import FastAPI

LOG_FILE = "/tmp/was_available.txt"

def read_log() -> bool:
    """Читает состояние товара из файла, безопасно обрабатывает отсутствие файла."""
    try:
        with open(LOG_FILE, "r") as f:
            return f.read().strip().lower() == "true"
    except FileNotFoundError:
        return False
    except Exception as e:
        print(f"Ошибка чтения файла {LOG_FILE}: {e}")
        return False

def write_log(value: bool):
    """Записывает состояние товара в файл."""
    try:
        with open(LOG_FILE, "w") as f:
            f.write("true" if value else "false")
    except Exception as e:
        print(f"Ошибка записи файла {LOG_FILE}: {e}")

def send_email(product_url):
    """Отправка email уведомления, ошибки не ломают функцию."""
    EMAIL_FROM = os.environ.get("EMAIL_FROM")
    EMAIL_TO = os.environ.get("EMAIL_TO")
    EMAIL_PASS = os.environ.get("EMAIL_PASS")

    if not EMAIL_FROM or not EMAIL_TO or not EMAIL_PASS:
        print("Email переменные окружения не заданы!")
        return

    msg = MIMEText(f"Товар появился на Kaspi:\n{product_url}")
    msg["Subject"] = "Kaspi Checker: Товар в наличии!"
    msg["From"] = EMAIL_FROM
    msg["To"] = EMAIL_TO

    try:
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(EMAIL_FROM, EMAIL_PASS)
            server.sendmail(EMAIL_FROM, EMAIL_TO, msg.as_string())
        print("Email отправлен!")
    except Exception as e:
        print(f"Ошибка при отправке email: {e}")

def handler():
    """Основная функция проверки товара, безопасная к ошибкам."""
    product_url = "https://kaspi.kz/shop/p/ehrmann-puding-vanil-bezlaktoznyi-1-5-200-g-102110634/?c=750000000"
    SCRAPER_API_KEY = os.environ.get("SCRAPER_API_KEY")
    if not SCRAPER_API_KEY:
        return {"error": "SCRAPER_API_KEY не задан!"}

    scraper_url = f"https://api.scraperapi.com/?api_key={SCRAPER_API_KEY}&url={product_url}"

    # Запрос к ScraperAPI
    try:
        r = requests.get(scraper_url, timeout=15)
        r.raise_for_status()
        soup = BeautifulSoup(r.text, "html.parser")
    except Exception as e:
        return {"error": f"Ошибка при запросе ScraperAPI: {str(e)}"}

    # Парсинг наличия товара
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
        print(f"Ошибка парсинга HTML: {e}")

    available = any(x in availability_text for x in ["в наличии", "есть", "доступно"])
    was_available = read_log()

    # Логика уведомления
    if available and not was_available:
        send_email(product_url)
        write_log(True)
    elif not available and was_available:
        write_log(False)

    return {
        "available": available,
        "was_available": was_available,
        "statusText": availability_text
    }

# FastAPI
app = FastAPI()

@app.get("/api/check")
def check_api():
    """Эндпоинт для cron-job.org"""
    try:
        return handler()
    except Exception as e:
        # Любые неожиданные ошибки возвращаем в JSON
        return {"error": f"Unexpected error: {str(e)}"}
