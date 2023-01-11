import json, threading
import requests
import firebase_admin
from firebase_admin import firestore, auth

cred = firebase_admin.credentials.Certificate("credentials.json")
app = firebase_admin.initialize_app(cred)
authenticator = auth.Client(app)
API_KEY = "AIzaSyAmnQRnBglx9y5n5cRMjvywODd1g519vkc"
NOT_ALLOWED_CHAR_IN_USERNAME = {"@", "'", '"'}

def createAccount(username, password, firstName, lastName, email):
    #password must be at least 6 characters long
    #username cannot contain certain characters

    def _verify_account():
        #delete user account if unverified
        try:user = getUser(username=username)
        except:return
        if not user["verified"]:delete_user(username)

    for char in NOT_ALLOWED_CHAR_IN_USERNAME:
        if char in username:return "InvalidCharacter"

    try:authenticator.create_user(uid=username, display_name=f"{firstName} {lastName}", email=email, password=password, email_verified=False)
    except auth.EmailAlreadyExistsError:return "EmailAlreadyExists"
    except auth.UidAlreadyExistsError:return "UsernameAlreadyExists"

    #generate secure token to communicate with firebase server
    token = auth.create_custom_token(username)
    token = requests.post(f"https://identitytoolkit.googleapis.com/v1/accounts:signInWithCustomToken?key={API_KEY}",data={"token":token}).json()["idToken"]

    #send verification email
    requests.post(f"https://identitytoolkit.googleapis.com/v1/accounts:sendOobCode?key={API_KEY}",data={"requestType":"VERIFY_EMAIL","idToken":token})
    threading.Timer(300,_verify_account).start() #delete the account if not verified after 5 minutes
    return "true"

def getUser(**kwargs) -> dict:
    #get user information using username or email
    if "email" in kwargs:
        user = authenticator.get_user_by_email(kwargs["email"])
    elif "username" in kwargs:
        user=authenticator.get_user(kwargs["username"])
    else:
        raise ValueError("Invalid information")
    return {"username":user.uid, "email":user.email, "verified":user.email_verified, "disabled":user.disabled}

def signIn(id, password):
    """
    INVALID_PASSWORD
    INVALID_INFO
    USER_DISABLED
    UNVERIFIED_EMAIL
    """
    try:
        if not "@" in id: #ID provided by username
            user = getUser(username=id)
            email = user["email"]
        else: #ID provided by email
            email = id
            user = getUser(email=email)
    except: return "INVALID_INFO"

    #verified if account is blocked
    if not user["verified"]:return "UNVERIFIED_EMAIL"
    elif user["disabled"]:return "USER_DISABLED"

    #send sign-in request
    res = requests.post(f"https://identitytoolkit.googleapis.com/v1/accounts:signInWithPassword?key={API_KEY}",data={"email":email,"password":password,"returnSecureToken":True}).json()
    
    if "idToken" in res: #authentication successful; return user information in json format
        return json.dumps(user)
    return res["error"]["message"]

def delete_user(username):
    try:
        authenticator.delete_user(username)
        return "true"
    except auth.UserNotFoundError:return "INVALID_INFO"