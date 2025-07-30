import smtplib

from email.mime.text import MIMEText

from celery_app import celery

from config import FROM_EMAIL, EMAIL_HOST_USER, EMAIL_HOST_PASSWORD, EMAIL_HOST, EMAIL_PORT, QUEUE


@celery.task(queue=QUEUE)
def send_mail(topic: str, message: str, to_email: str):
    msg = MIMEText(message)
    msg['Subject'] = topic
    msg['From'] = FROM_EMAIL
    msg['To'] = to_email
    try:
        with smtplib.SMTP_SSL(EMAIL_HOST, EMAIL_PORT) as server:
            server.login(EMAIL_HOST_USER, EMAIL_HOST_PASSWORD)
            server.send_message(msg)
    except Exception as e:
        print('Mail error:', str(e))
