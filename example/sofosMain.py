import os, threading, datetime, json, io
import flask
from numpy import argsort
import firebasemanager, Dictionary

absPath=os.path.dirname(__file__)

class DailyFeed(Dictionary.WordOfTheDay, Dictionary.QuoteOfTheDay):
    def __init__(self):
        super(DailyFeed, self).__init__()
        #definition -> {"--word class--":("--definition--","--examples--"), "--word class 2--":("--definition2--", "--examples2--")}
        #self.word and self.definition are None if an unknown error is preventing dictionary from accessing online data
        self.word = self.definition = None
        #quote and author are both strings
        #self.quote and self.author are None if an unknown error is preventing dictionary from accessing online data
        self.quote = self.author = None
        threading.Thread(target=self.updateFeed).start()

    def updateFeed(self):
        #set timer for a new word at 0:0:00 the next day
        def timeToNextDay():
            now = datetime.datetime.now()
            nextDay = now.replace(hour=0, minute=0, second=0, microsecond=0) + datetime.timedelta(days=1)
            delta = nextDay - now
            return delta.total_seconds()
        self.word, self.definition = self.newWord()
        self.quote, self.author = self.newQuote()
        threading.Timer(timeToNextDay(), self.updateFeed).start()
    
app = flask.Flask(__name__)

@app.route("/")
def main():
    return """
        <!DOCTYPE html>
        <html>
            <body>
                <center>
                    <img src="sofos", alt="SOFOS cloud", style="width:420px;height:420px">
                    <h1>Greetings from SOFOS server!</h1>
                <center>
            </body>
        </html>"""

@app.route("/sofos")
def sofos():
    return flask.send_file(open(os.path.join(absPath, "Data/SOFOS.png"), "rb"), mimetype="image/png")

@app.route("/newAccount", methods=["POST"])
def createAccount():
    """Create new account using provided user information. An account verification
        email is sent to the user. If the account is unverified within 5 minutes,
        the account is automatically deleted.
        Return true on success
        Return 'EmailAlreadyExists' or 'UsernameAlreadyExists' in the case of a conflict
        Return 'ValueError' if email format is wrong or password is too weak
        Return false for other unknown errors"""
    try:
        args = flask.request.json
        fName = args["fName"]
        lName = args["lName"]
        username = args["username"]
        email = args["email"]
        password = args["password"]
        return firebasemanager.create_user(username, fName, lName, email, password)
    except:return "false"

@app.route("/getUserByUsername", methods=["POST"])
def getUserByUsername():
    """Fetch user info by username.
        Return user as a json dict.
        Return 'NotFound' if username does not exist.
        Take as argument request user's username."""
    try:
        args = flask.request.json
        username = args["username"]
        _from = args["_from"]
        user = firebasemanager.get_user(username=username)
        fromUser = firebasemanager.get_user(username=_from)
        if isinstance(user, str):return user #user is an error code
        if isinstance(fromUser, str):return "false"#resquest user is invalid: access is blocked

        if not fromUser["verified"]: #user is not verified
            return json.dumps({key:user[key] for key in ["username", "bio"]})
        else:
            data = {key:user[key] for key in ["username", "bio"]}
            data["numberOfSubscribers"] = len(user["subscribers"])
            data["isSubscribed"] = fromUser["username"] in user["subscribers"]
            return json.dumps(data)
    except:return "false"

@app.route("/signin", methods=["POST"])
def signin():
    """Sign in using email or username.
        Return 'InvalidRequest' if nothing is provided.
        Return 'NotFound' if user does not exist.
        Return 'UNVERIFIED_ACCOUNT' and 'DISABLED_ACCOUNT' if needed
        Return true on success
        Return false for other errors"""
    try:
        args = flask.request.json
        username = args.get("username", None)
        email = args.get("email", None)
        password = args["password"]
        if username == email and username == None:
            return "InvalidRequest"
        elif username == None:
            return firebasemanager.signin(password, email=email)
        else:
            return firebasemanager.signin(password, username=username)
    except:return "false"

@app.route("/updateUser", methods=["POST"])
def updateUser():
    try:
        args = flask.request.json
        username = args["username"]
        data = dict(args.copy())
        del data["username"]
        firebasemanager.update_user(username, **data)
        return "true"
    except:
        return "false"
    
@app.route("/deleteUser", methods=["POST"])
def deleteUser():
    """Delete user by username.
        Return true on success.
        Return 'NotFound' if username does not exist.
        Return false for other errors"""
    try:
        return firebasemanager.delete_user(flask.request.json["username"])
    except:return "false"
   
@app.route("/forgetPassword", methods=["POST"])
def forgetPassword():
    """Request send forgot password email.
        Return true on success.
        Return 'NotFound' if username does not exist.
        Return false for other errors"""
    try:
        username = flask.request.json["username"]
        return firebasemanager.reset_password(username)
    except: return "false"

@app.route("/subscribe", methods=["POST"])
def subscribe():
    """Subscribe to another user using username.
        Return True if successfully subscribed.
        Return RequestNotVerified if requester's account is not verified.
        Return TargetNotVerified if target's account is not verified.
        Return false on internal error"""
    try:
        args = flask.request.json
        target = args["to"]
        _from = args["_from"]
        
        fromUser = firebasemanager.get_user(username=_from)
        targetUser = firebasemanager.get_user(username=target)
        if isinstance(fromUser, str) or isinstance(targetUser, str): #username is error code (probably user is not found)
            return "false"
        elif not fromUser["verified"]:
            return "RequestNotVerified"
        elif not targetUser["verified"]:
            return "TargetNotVerified"
        firebasemanager.subscribe(targetUser, fromUser)
        return "true"
    except: return "false"

@app.route("/wordOfTheDay", methods=["GET"])
def wordOfTheDay():
    """Return list of [word, definition]
    see definition format in class DailyFeed"""
    return json.dumps((feed.word, feed.definition))

@app.route("/quoteOfTheDay", methods=["GET"])
def quoteOfTheDay():
    """Return list of [author, quote]"""
    return json.dumps((feed.author, feed.quote))

@app.route("/upload/video", methods=["POST"])
def videoUpload():
    """Upload videos to online server.
        Take arguments through FLASK.REQUEST.FORM: title, topic and author(username of the one who posted)
        include files: stream for video content, thumbnail for video thumbnail
        return true on success.
        return NoFile if no upload file is supplied"""
    try:
        description = flask.request.form.get("description", "")
        title = flask.request.form["title"]
        topic = flask.request.form["topic"]
        author = flask.request.form["author"]

        if "file" in flask.request.files:
            return "NoFile"
        stream = flask.request.files["stream"].read()
        thumbnail = flask.request.files["thumbnail"].read()

        firebasemanager.new_video(title, topic, author, description, thumbnail, stream)
        return "true"
    except:return "false"

@app.route("/download/video/info", methods=["POST"])
def videoInfo():
    """Return video information in dictionnary format
        Contains keys:title, topic, author, description, views, stream
        return false if error is encountered"""
    try:
        id = flask.request.json["id"]
        info = firebasemanager.get_video_info(id)
        return json.dumps(info)
    except:return "false"

@app.route("/download/video/stream", methods=["POST"])
def videoDownload():
    """Download video stream from online server.
        return downloaded media information in ONE CHUNK (bytes format).
        return false otherwise"""
    try:
        id = flask.request.json["id"]
        stream = firebasemanager.get_video_stream(id)
        return flask.send_file(io.BytesIO(stream), mimetype="video/mp4")
    except:return "false"

@app.route("/download/thumbnail", methods=["POST"])
def thumbnailDownload():
    """Download video thumbnail from online server.
        return image bytes on success.
        else return false for unknown errors"""
    try:
        id = flask.request.json["id"]
        thumbnail = firebasemanager.get_thumbnail(id)
        return flask.send_file(io.BytesIO(thumbnail), mimetype="image/png")
    except:return "false"

@app.route("/removeVideo", methods=["POST"])
def removeVideo():
    """Delete published video from online server
        return true or false"""
    try:
        id = flask.request.json["id"]
        firebasemanager.remove_video(id)
        return "true"
    except:return "false"

if __name__ == "__main__":
    feed = DailyFeed()
    app.run(host="0.0.0.0", port=235, threaded=True)
