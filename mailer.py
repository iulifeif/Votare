import smtplib
import ssl
import traceback
import os
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

server_smtp = os.environ.get("server_smtp", "smtp.zoho.com")
port_smtp = int(os.environ.get("port_smtp", 587))
password_smtp = os.environ.get("password_smtp", "")
server_mail = os.environ.get("server_mail", "")


def send_mail_list(mail_message_dict):
    try:
        with smtplib.SMTP(server_smtp, port_smtp) as server:
            # server.set_debuglevel(1)
            server.ehlo()
            server.starttls()
            server.ehlo()
            server.login(server_mail, password_smtp)
            for email in mail_message_dict:
                body = "<a href='{}'>Vote here!</a>".format(mail_message_dict[email])
                mime_content = MIMEMultipart()
                mime_content['From'] = server_mail
                mime_content['To'] = email
                mime_content['Subject'] = "Votare ASII"
                mime_content.attach(MIMEText(body, 'html'))
                message = mime_content.as_string()
                try:
                    server.sendmail(server_mail, email, message)
                except Exception:
                    print(traceback.format_exc())
    except Exception:
        print(traceback.format_exc())
