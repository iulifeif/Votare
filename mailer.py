import smtplib
import ssl
import traceback
import os

server_smtp = os.environ.get("server_smtp", "smtp.zoho.com")
port_smtp = int(os.environ.get("port_smtp", 587))
password_smtp = os.environ.get("password_smtp", "")
server_mail = os.environ.get("server_mail", "")


def send_mail_list(mail_message_dict):
    try:
        # Create a secure SSL context
        context = ssl.create_default_context()
        with smtplib.SMTP(server_smtp, port_smtp) as server:
            server.set_debuglevel(1)
            server.ehlo()
            server.starttls()
            server.ehlo()
            server.login(server_mail, password_smtp)
            for email in mail_message_dict:
                message = mail_message_dict[email]
                try:
                    server.sendmail(from_addr=server_mail, to_addrs=[email], msg=message)
                except Exception:
                    print(traceback.format_exc())
    except Exception:
        print(traceback.format_exc())
