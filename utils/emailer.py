import smtplib
import os
from email.mime.text import MIMEText

EMAIL_USER = "kolyan77st@gmail.com"
EMAIL_PASS = "fnjs pgka lxhj oyga"
EMAIL_TO = "KZJ78@yandex.kz"

def send_email(subject, text):
    msg = MIMEText(text)
    msg["Subject"] = subject
    msg["From"] = EMAIL_USER
    msg["To"] = EMAIL_TO

    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
        server.login(EMAIL_USER, EMAIL_PASS)
        server.sendmail(EMAIL_USER, EMAIL_TO, msg.as_string())
