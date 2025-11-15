import os
import requests
import smtplib
from email.mime.text import MIMEText

KASPI_PRODUCT_ID = "102110634"  # с вашего URL
API_ENDPOINT = f"https://some.kaspi.api/path/products/{KASPI_PRODUCT_ID}"  # пример

EMAIL_FROM = os.getenv("EMAIL_FROM")
EMAIL_TO = os.getenv("EMAIL_TO")
EMAIL_PASSWORD = os.getenv("EMAIL_PASSWORD")

def send_email(subject, body):
    if not EMAIL_FROM or not EMAIL_TO or not EMAIL_PASSWORD:
        print("Email settings not configured.")
        return

    msg = MIMEText(body, "plain", "utf‑8")
    msg["Subject"] = subject
    msg["From"] = EMAIL_FROM
    msg["To"] = EMAIL_TO

    server = smtplib.SMTP_SSL("smtp.gmail.com", 465)
    server.login(EMAIL_FROM, EMAIL_PASSWORD)
    server.sendmail(EMAIL_FROM, EMAIL_TO, msg.as_string())
    server.quit()

def check_availability():
    headers = {
        "User‑Agent": "Mozilla/5.0",
        # возможно нужен API‑ключ или авторизация
        #"Authorization": "Bearer YOUR_TOKEN_HERE"
    }

    r = requests.get(API_ENDPOINT, headers=headers)
    if r.status_code != 200:
        print("Ошибка запроса:", r.status_code, r.text)
        return False

    data = r.json()
    # Примерное имя поля — нужно выяснить:
    available = data.get("available") or data.get("in_stock") or data.get("offers", {}).get("availability")

    return bool(available)

if __name__ == "__main__":
    if check_availability():
        subject = "Товар появился на Kaspi!"
        body = f"🎉 Товар появился в наличии!\nhttps://kaspi.kz/shop/p/ehrmann-puding-vanil-bezlaktoznyi-1-5-200-g-102110634/?c=750000000"
        print(body)
        send_email(subject, body)
    else:
        print("Товара нет в наличии.")
