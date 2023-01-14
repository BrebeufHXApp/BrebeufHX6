import json, threading, random, uuid
import requests
import firebase_admin
from firebase_admin import firestore, auth, storage
import smtpManager as mailbox

cred = firebase_admin.credentials.Certificate("sources/credentials.json")
app = firebase_admin.initialize_app(cred, {"storageBucket":"brebeufhxapp-f8521.appspot.com"})
authenticator = auth.Client(app)
dtbase = firestore.client()
mediadb = storage.bucket()
API_KEY = "AIzaSyAmnQRnBglx9y5n5cRMjvywODd1g519vkc"
NOT_ALLOWED_CHAR_IN_USERNAME = {"@", "'", '"'}
with open("sources/AboutTemplates.json", "r", encoding="utf-8") as file:
    aboutTemplates = json.load(file)

def createAccount(username, password, firstName, lastName, email):
    #password must be at least 6 characters long
    #username cannot contain certain characters

    def _verify_account():
        #delete user account if unverified
        try:user = getUser(username)
        except:return
        if not user["verified"]:delete_user(username)

    for char in NOT_ALLOWED_CHAR_IN_USERNAME:
        if char in username:return "INVALID_CHARACTER"

    try:authenticator.create_user(uid=username, display_name=f"{firstName} {lastName}", email=email, password=password, email_verified=False)
    except auth.EmailAlreadyExistsError:return "EMAIL_ALREADY_EXISTS"
    except auth.UidAlreadyExistsError:return "USERNAME_ALREADY_EXISTS"
    except:return "INVALID_INFO"

    #generate secure token to communicate with firebase server
    token = auth.create_custom_token(username)
    token = requests.post(f"https://identitytoolkit.googleapis.com/v1/accounts:signInWithCustomToken?key={API_KEY}",data={"token":token}).json()["idToken"]

    #create firestore document
    data = {"about":random.choice(aboutTemplates), "stats":[random.randint(0, 1000) for _ in range(3)]}
    dtbase.collection("Users").document(username).set(data)

    #send verification email
    requests.post(f"https://identitytoolkit.googleapis.com/v1/accounts:sendOobCode?key={API_KEY}",data={"requestType":"VERIFY_EMAIL","idToken":token})
    threading.Timer(300,_verify_account).start() #delete the account if not verified after 5 minutes
    return "true"

def getUser(id) -> dict:
    #get user information using username or email
    if not "@" in id: #ID provided by username
        user = authenticator.get_user(id)
    else: #ID provided by email
        user = authenticator.get_user_by_email(id)
    data = dtbase.collection("Users").document(user.uid).get().to_dict()
    return {"username":user.uid, "email":user.email, "fullName":user.display_name, "verified":user.email_verified, "disabled":user.disabled, **data}

def signIn(id, password):
    """
    INVALID_PASSWORD
    INVALID_INFO
    USER_DISABLED
    UNVERIFIED_EMAIL
    """
    try:user = getUser(id)
    except: return "INVALID_INFO"

    #verified if account is blocked
    if not user["verified"]:return "UNVERIFIED_EMAIL"
    elif user["disabled"]:return "USER_DISABLED"

    #send sign-in request
    res = requests.post(f"https://identitytoolkit.googleapis.com/v1/accounts:signInWithPassword?key={API_KEY}",data={"email":user["email"],"password":password,"returnSecureToken":True}).json()
    
    if "idToken" in res: #authentication successful; return user information in json format
        return json.dumps(user)
    return res["error"]["message"]

def resetPassword(id):
    try:
        user = getUser(id)
        requests.post(f"https://identitytoolkit.googleapis.com/v1/accounts:sendOobCode?key={API_KEY}",data={"requestType":"PASSWORD_RESET","email":user["email"]})
    except: return "INVALID_INFO"
    return "true"

def delete_user(username):
    try:
        authenticator.delete_user(username)
        dtbase.collection("Users").document(username).delete()
        return "true"
    except auth.UserNotFoundError:return "INVALID_INFO"

#accessing firebase storage to fetch medias

def newUuid():
    id = uuid.uuid4() #completely random uuid
    if mediadb.blob(f"{id}/gallery").exists(): #current id is already used
        return newUuid()
    return str(id)

def createEvent(title, organizer, description, dateTime, place, images):
    #sending email
    try:
        user = getUser(organizer)
        username = user["username"]
    except: "INVALID_INFO"
    threading.Thread(target=mailbox.sendEmail, args=(user["email"],)).start()

    id = newUuid()
    dtbase.collection("Event").document(id).set({
        "id":id,
        "title":title,
        "organizer":username,
        "description":description,
        "dateTime":dateTime,
        "place":place,
        "participants":[]
    })
    galleryBlob = mediadb.blob(f"{id}/gallery")
    galleryBlob.upload_from_file(images) 

def getEventInfo(n=5):
    #return list of event information
    events = list(dtbase.collection("Event").list_documents())
    if not events:
        return "NO_EVENT"

    random.shuffle(events)
    events = [e.get().to_dict() for e in events[:min(len(events), n)]]
    return events

def downloadEventGallery(id:str):
    return mediadb.blob(f"{id}/gallery").download_as_bytes()

def deleteEvent(id:str):
    dtbase.collection("Event").document(id).delete()
    mediadb.blob(f"{id}/gallery").delete()

def eventSignUp(event:str, user:str):
    try:
        user = getUser(user)
        username = user["username"]
    except:return "INVALID_INFO"

    #adding user data to event databse
    data = dtbase.collection("Event").document(event).get().to_dict()
    if username == data["organizer"] or username in data["participants"]:
        return "ALREADY_PARTICIPATING"
    data["participants"].append(username)
    dtbase.collection("Event").document(event).set(data)

    threading.Thread(target=mailbox.sendEmail, args=(user["email"],)).start()
    return "true"

if __name__ == "__main__":
    url = "http://192.168.1.8:5000"

    def clear():
        for event in list(dtbase.collection("Event").list_documents()):
            id = event.get().to_dict()["id"]
            deleteEvent(id)