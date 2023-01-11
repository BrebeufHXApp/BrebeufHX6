import os,requests,io,threading,datetime,uuid
import firebase_admin
from firebase_admin import auth,storage,firestore

#initialize firebase functions and variables
absPath=os.path.dirname(__file__)
API_KEY="AIzaSyCpMPnVdaU1iYpfn2GRZc2ejMIdF4tKbAg"
cred=firebase_admin.credentials.Certificate(os.path.join(absPath,"Data/credentials.json")) #initialize firebase functions
app=firebase_admin.initialize_app(cred,{"storageBucket":"ourworld-a3ab0.appspot.com"})
db=storage.bucket()
firestoredb=firestore.client()
authenticator=auth.Client(app)

def create_user(username:str,firstname:str,lastname:str,email:str,password:str)->str:
    """create a new user
        Store a list of user's subscribers and their bio"""
    try:authenticator.create_user(uid=username,display_name=f"{firstname} {lastname}",email=email,password=password,email_verified=False)
    except auth.EmailAlreadyExistsError:return "EmailAlreadyExists"
    except auth.UidAlreadyExistsError:return "UsernameAlreadyExists"
    except ValueError:return "ValueError"
    data=dict(bio="",subscribers=[],subscriptions=[],posts=[])
    firestoredb.collection("Users").document(username).set(data)
    token=auth.create_custom_token(username)
    token=requests.post(f"https://identitytoolkit.googleapis.com/v1/accounts:signInWithCustomToken?key={API_KEY}",data={"token":token}).json()["idToken"]
    requests.post(f"https://identitytoolkit.googleapis.com/v1/accounts:sendOobCode?key={API_KEY}",data={"requestType":"VERIFY_EMAIL","idToken":token})
    def _verify_account():
        user=get_user(username=username)
        if user=="NotFound":return
        if not user["verified"]:delete_user(username)
    threading.Timer(300,_verify_account).start() #delete the account if not verified after 5 minutes
    return "true"

def get_user(**kwargs):
    """Get user information. Take username or email as argument(specify).
        Return user as a dict on success.
        Else, return a string error code."""
    try:
        if "email" in kwargs:user=authenticator.get_user_by_email(kwargs["email"])
        elif "username" in kwargs:user=authenticator.get_user(kwargs["username"])
        else:raise ValueError("Must have at least one argument from the following: username, email.")
    except auth.UserNotFoundError:return "NotFound"
    data=firestoredb.collection("Users").document(user.uid).get().to_dict()
    return dict(username=user.uid,name=user.display_name,email=user.email,verified=user.email_verified,disabled=user.disabled,**data)

def signin(password:str,**kwargs)->str:
    """Signin with username or email. This function only checks the validity of the credentials."""
    if "email" in kwargs:user=get_user(email=kwargs["email"])
    elif "username" in kwargs:user=get_user(username=kwargs["username"])
    else:raise ValueError("Must have at least one argument from the following: username, email.")
    if isinstance(user, str): #error encountered while retrieving user data. Return error code as a string.
        return user
    if not user["verified"]:return "UNVERIFIED_ACCOUNT"
    elif user["disabled"]:return "DISABLED_ACCOUNT"
    result=requests.post(f"https://identitytoolkit.googleapis.com/v1/accounts:signInWithPassword?key={API_KEY}",data={"email":user["email"],"password":password,"returnSecureToken":True}).json()
    if "idToken" in result:return "true"
    else:return result["error"]["message"]

def reset_password(username:str)->str:
    """Request a reset password link"""
    user=get_user(username=username)
    if isinstance(user, str): #error encountered while retrieving user data. Return error code as a string.
        return user
    requests.post(f"https://identitytoolkit.googleapis.com/v1/accounts:sendOobCode?key={API_KEY}",data={"requestType":"PASSWORD_RESET","email":user["email"]})
    return "true"

def update_user(username:str,**kwargs)->str:
    """Update user information (only those stored in firestore)"""
    user=get_user(username=username)
    if isinstance(user, str): #error encountered while retrieving user data. Return error code as a string.
        return user
    data=dict((key,user[key]) for key in ["bio","subscribers","subscriptions","posts"])
    for item in kwargs:
        assert item in data
        data[item]=kwargs[item]
    firestoredb.collection("Users").document(username).set(data)
    return "true"

def delete_user(username:str)->str:
    """delete a user"""
    try:
        authenticator.delete_user(username)
        firestoredb.collection("Users").document(username).delete()
        return "true"
    except auth.UserNotFoundError:return "NotFound"

def subscribe(targetUser:dict, fromUser:dict):
    """Internal function
        Add fromUser to targetUser's subscriber list"""
    if fromUser["username"] in targetUser["subscribers"]: #do nothing if user is already subscribed
        return
    targetUser["subscribers"].append(fromUser["username"])
    fromUser["subscriptions"].append(targetUser["username"])
    firestoredb.collection("Users").document(targetUser["username"]).set({key:targetUser[key] for key in ["bio","subscribers","subscriptions","posts"]})
    firestoredb.collection("Users").document(fromUser["username"]).set({key:fromUser[key] for key in ["bio","subscribers","subscriptions","posts"]})

"""
Accessing firebase for storing and retreving posts
Divide Firebase online collection into 3 categories:document, video, image
"""
def new_uuid():
    id=uuid.uuid4()#completely random uuid
    if db.blob(f"{id}/stream").exists():#current id is already used
        return new_uuid()
    return str(id)

def new_video(title:str,topic:str,author:str,description:str,thumbnail:bytes,stream:bytes):
    id=new_uuid()#generate id for video
    firestoredb.collection("Video").document(id).set({
        "id":id,
        "title":title,
        "topic":topic,
        "author":author,
        "description":description,
        "date_published":datetime.datetime.now().strftime("%y%m%d"),
        "views":0
    })
    video_blob=db.blob(f"{id}/stream")
    thumbnail_blob=db.blob(f"{id}/thumbnail")
    video_blob.upload_from_string(io.BytesIO(stream).read())
    thumbnail_blob.upload_from_string(io.BytesIO(thumbnail).read())

def increment_view(info:dict):
    info["views"]+=1
    firestoredb.collection("Video").document(info["id"]).set(info)

def get_thumbnail(id:str):
    thumbnail=db.blob(f"{id}/thumbnail").download_as_bytes()
    return thumbnail

def get_video_info(id:str):
    info=firestoredb.collection("Video").document(id).get().to_dict()
    return info

def get_video_stream(id:str):
    info=firestoredb.collection("Video").document(id).get().to_dict()
    increment_view(info)
    video=db.blob(f"{id}/stream").download_as_bytes()
    return video

def remove_video(id:str):
    firestoredb.collection("Video").document(id).delete()
    db.blob(f"{id}/stream").delete()
    db.blob(f"{id}/thumbnail").delete()