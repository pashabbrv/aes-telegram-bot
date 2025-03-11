from dotenv import load_dotenv
import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# Загрузка констант из .env
load_dotenv()
from_email = os.getenv('SENDER_EMAIL')
password = os.getenv('PASSWORD_EMAIL')

# Параметры SMTP сервера (Google)
smtp_server = 'smtp.gmail.com'
smtp_port = 587


def send_email(to_email: str, subject: str, body: str) -> None:
    """
    Отправляет электронное письмо через SMTP-сервер.

    Параметры:
    - to_email: Почта получателя.
    - subject: Тема письма.
    - body: Содержимое письма (может быть HTML или обычным текстом).
    """
    global smtp_server
    global smtp_port

    # Создание объекта сообщения
    msg = MIMEMultipart()
    msg["From"] = from_email
    msg["To"] = to_email
    msg["Subject"] = subject

    # Добавление тела письма
    msg.attach(MIMEText(body, "plain"))

    try:
        # Подключаемся к SMTP-серверу
        with smtplib.SMTP(smtp_server, smtp_port) as server:
            server.starttls()  # Шифрование соединения
            server.login(from_email, password)
            server.sendmail(from_email, to_email, msg.as_string())
        print("Письмо успешно отправлено!")
        return True

    except Exception as e:
        print(f"Ошибка при отправке письма: {e}")
        return False


# Пример использования
if __name__ == "__main__":
    send_email(
        to_email="your_mail@mail.ru",
        subject="Тестовое письмо",
        body="Привет, это тестовое письмо из Python!",
    )