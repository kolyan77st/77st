import os
import requests
from bs4 import BeautifulSoup
import smtplib
from email.mime.text import MIMEText
from fastapi import FastAPI

# Файл для лога
LOG_FILE = "/tmp/was_available.txt"

def read_log():
    try:
        with open(LOG_FILE, "r") as f:
            return f.read().strip() == "true"
    except:
        return False

def write_log(value: bool):
    with open(LOG_FILE, "w") as f:
        f.write("true" if value else "false")

def send_email(product_url):
    EMAIL_FROM = os.environ.get("EMAIL_FROM")
    EMAIL_TO = os.environ.get("EMAIL_TO")
    EMAIL_PASS = os.environ.get("EMAIL_PASS")

    msg = MIMEText(f"Товар теперь в наличии:\n{product_url}")
    msg["Subject"] = "Товар появился на Kaspi!"
    msg["From"] = EMAIL_FROM
    msg["To"] = EMAIL_TO

    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
        server.login(EMAIL_FROM, EMAIL_PASS)
        server.sendmail(EMAIL_FROM, EMAIL_TO, msg.as_string())

def handler():
    product_url = "https://kaspi.kz/shop/p/ehrmann-puding-vanil-bezlaktoznyi-1-5-200-g-102110634/?c=750000000"
    SCRAPER_API_KEY = os.environ.get("SCRAPER_API_KEY")

    scraper_url = f"https://api.scraperapi.com/?api_key={SCRAPER_API_KEY}&url={product_url}"

    r = requests.get(scraper_url)
    soup = BeautifulSoup(r.text, "html.parser")

    # Проверка наличия товара
    availability_text = ""
    el = soup.select_one("div.product__header .status")
    if el:
        availability_text = el.get_text(strip=True).lower()
    else:
        el2 = soup.select_one(".sellers-table__in-stock")
        if el2:
            availability_text = el2.get_text(strip=True).lower()

    available = any(x in availability_text for x in ["в наличии", "есть", "доступно"])

    # Лог в /tmp
    was_available = read_log()

    # Email только один раз
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

# FastAPI app для Vercel
app = FastAPI()

@app.get("/api/check")
def check_api():
    return handler()
