import firebase_admin,uuid,random,smtplib,ssl
from firebase_admin import firestore
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.image import MIMEImage

cred=firebase_admin.credentials.Certificate("/home/brebeufhx5website/brebeufhx5website/data/credentials.json")
app=firebase_admin.initialize_app(cred)
firestoredb=firestore.client()
petitionbase=firestoredb.collection("petitions")
pendingbase=firestoredb.collection("pending")
emailserver=smtplib.SMTP_SSL("smtp.gmail.com",465,context=ssl.create_default_context())
emailserver.login("brebeufhx5website@gmail.com","bhckybdgmoofbubo")
file=open("/home/brebeufhx5website/brebeufhx5website/data/email.html","rb")
html=file.read()
file.close()

def uploadPetition(title,text,author,email):
    uid=str(uuid.uuid1())
    data=dict(title=title,text=text,author=author,votes=0,emails=[],email=email)
    result="unclear"
    if result=="accepted":petitionbase.document(uid).set(data)
    else:pendingbase.document(uid).set(data)
    return result

def votePetition(uid,email):
    """Generate an html email and sent it to the voter"""
    try:petition=petitionbase.document(uid)
    except:raise ValueError("No uid found with this name")
    mail=MIMEMultipart("related")
    mail["From"]="brebeufhx5website@gmail.com"
    mail["To"]=email
    mail["Subject"]="Nouvelle pétition"
    mail.attach(MIMEText(html,"html","utf-8"))
    file=open("/home/brebeufhx5website/brebeufhx5website/data/petition.jpg","rb")
    attachment0=MIMEImage(file.read())
    attachment0.add_header("Content-ID","<petition>")
    file.close()
    mail.attach(attachment0)
    try:
        emails=petition.get().get("emails")
        if email in emails:return "already voted"
        try:emailserver.sendmail("brebeufhx5website@gmail.com",email,mail.as_string())
        except:pass
        emails.append(email)
        petition.update({"emails":emails})
        votes=petition.get().get("votes")+1
        petition.update({"votes":votes})
        return "true"
    except:return "invalid email"

def getRandomPetitions(count):
    petitions=list()
    for petition in list(petitionbase.list_documents()):
        petitions.append((petition.get().get("votes"),petition))
    random.shuffle(petitions)
    petitions.sort(key=lambda x:-x[0])
    petitions=[{**petition[1].get().to_dict(),"uid":petition[1].id} for petition in petitions]
    return petitions[:min(count,len(petitions))]

def searchPetitions(searchstring):
    keywords=searchstring.split(" ")
    petitions=list()
    for petition in list(petitionbase.list_documents()):
        petitiondict=petition.get()
        score=0
        for keyword in keywords:
            score+=3*petitiondict.get("title").lower().count(keyword.lower())
            score+=petitiondict.get("text").lower().count(keyword.lower())
        if score!=0:petitions.append((score,petition))
    petitions.sort(key=lambda x:-x[0])
    petitions=[{**petition[1].get().to_dict(),"uid":petition[1].id} for petition in petitions]
    return petitions

def publishPetition(uid):
    try:petition=pendingbase.document(uid).get().to_dict()
    except:raise ValueError("No uid found with this name")
    pendingbase.document(uid).delete()
    petitionbase.document(uid).set(petition)