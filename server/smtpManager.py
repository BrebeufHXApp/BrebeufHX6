import smtplib, ssl
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.image import MIMEImage
from email.mime.base import MIMEBase

context = ssl.create_default_context()
server = smtplib.SMTP_SSL("smtp.gmail.com", 465, context=context)
server.login("brebeufhxapp@gmail.com", "dlsrgpgqosqxtmzw")
with open("sources/email.html", "rb") as file:
    html = file.read()
    file.close()
with open("sources/earth.jpg", "rb") as file:
    bgImg = file.read()
    file.close()

def sendEmail(email):
    mail=MIMEMultipart("related")
    mail["From"]="brebeufhxapp@gmail.com"
    mail["To"] = email
    mail["Subject"] = "Un nouveau email"
    mail.attach(MIMEText(html, "html", "utf-8"))
    attachment = MIMEImage(bgImg)
    attachment.add_header("Content-ID","<bgImg>")
    mail.attach(attachment)

    server.sendmail("brebeufhxapp@gmail.com", email, mail.as_string())