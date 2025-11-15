import requests
from bs4 import BeautifulSoup
import os
import json
import smtplib
from email.mime.text import MIMEText

KASPI_URL = "https://kaspi.kz/shop/p/ehrmann-puding-vanil-bezlaktoznyi-1-5-200-g-102110634/?c=750000000"

EMAIL_FROM = os.getenv("EMAIL_FROM")
EMAIL_TO = os.getenv("EMAIL_TO")
EMAIL_PASSWORD = os.getenv("EMAIL_PASSWORD")  # app password for gmail

def send_email(subject, body):
    if not EMAIL_FROM or not EMAIL_TO or not EMAIL_PASSWORD:
        print("Email settings not configured.")
        return

    msg = MIMEText(body, "plain", "utf-8")
    msg["Subject"] = subject
    msg["From"] = EMAIL_FROM
    msg["To"] = EMAIL_TO

    server = smtplib.SMTP_SSL("smtp.gmail.com", 465)
    server.login(EMAIL_FROM, EMAIL_PASSWORD)
    server.sendmail(EMAIL_FROM, EMAIL_TO, msg.as_string())
    server.quit()

def check_availability():
    headers = {
        "User-Agent": "Mozilla/5.0"
    }
    
    r = requests.get(KASPI_URL, headers=headers)
    soup = BeautifulSoup(r.text, "html.parser")

    data_block = soup.find("script", {"type": "application/ld+json"})
    if not data_block:
        return False

    data = json.loads(data_block.text)
    availability = data.get("offers", {}).get("availability", "")

    return "InStock" in availability

if __name__ == "__main__":
    in_stock = check_availability()

    if in_stock:
        subject = "Товар появился на Kaspi!"
        body = f"🎉 Товар появился в наличии!\n{KASPI_URL}"
        print(body)
        send_email(subject, body)
    else:
        print("Товара нет в наличии.")
