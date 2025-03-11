import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart


def send_email(to_email: str, subject: str, body: str,
               from_email: str, password: str,
               smtp_server: str = "smtp.gmail.com",
               smtp_port: int = 587) -> None:
    """
    Отправляет электронное письмо через SMTP-сервер.

    Параметры:
    - to_email: Почта получателя.
    - subject: Тема письма.
    - body: Содержимое письма (может быть HTML или обычным текстом).
    - from_email: Почта отправителя (должна поддерживать SMTP).
    - password: Пароль от почты отправителя или пароль приложения.
    - smtp_server: Адрес SMTP-сервера (по умолчанию для Gmail).
    - smtp_port: Порт SMTP-сервера (по умолчанию для Gmail с TLS).
    """

    # Создаем объект сообщения
    msg = MIMEMultipart()
    msg["From"] = from_email
    msg["To"] = to_email
    msg["Subject"] = subject

    # Добавляем тело письма
    msg.attach(MIMEText(body, "plain"))  # Для HTML-писем замените "plain" на "html"

    try:
        # Подключаемся к SMTP-серверу
        with smtplib.SMTP(smtp_server, smtp_port) as server:
            server.starttls()  # Шифруем соединение
            server.login(from_email, password)
            server.sendmail(from_email, to_email, msg.as_string())
        print("Письмо успешно отправлено!")

    except Exception as e:
        print(f"Ошибка при отправке письма: {e}")


# Пример использования
if __name__ == "__main__":
    send_email(
        to_email="recipient@example.com",
        subject="Тестовое письмо",
        body="Привет, это тестовое письмо из Python!",
        from_email="your_email@gmail.com",
        password="your_password"
    )