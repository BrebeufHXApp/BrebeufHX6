import io, json
import flask, flask_socketio
import firebaseManager as fbm

#https://brebeufhxapp.onrender.com
#testing server: requests.post(f"{url}/signIn", data={"id":"user", "password":"123456"}).text
server = flask.Flask(__name__)
socketIO = flask_socketio.SocketIO(server)

def send(route, data, sid):
  socketIO.emit(route, data=data, room=sid)

#---------------------Server---------------------
@server.route("/")
def main():
  return """<center><h1>BrebeufHXApp</h1></center>"""

@server.route("/createAccount", methods=["POST"])
def createAccount():
  data = flask.request.form
  username = data.get("username")
  password = data.get("password")
  firstName = data.get("firstName")
  lastName = data.get("lastName")
  email = data.get("email")
  return fbm.createAccount(username, password, firstName, lastName, email)

@server.route("/signIn", methods=["POST"])
def signIn():
  data = flask.request.form
  id = data.get("id")
  password = data.get("password")
  return fbm.signIn(id, password)

@server.route("/resetPassword")
def resetPassword():
  return fbm.resetPassword(flask.request.form.get("id"))

#---------------------Events Management---------------------

@server.route("/createEvent", methods=["POST"])
def createEvent():
  try:
    title = flask.request.form["title"]
    description = flask.request.form.get("description", "")
    dateTime = flask.request.form["dateTime"]
    organiser = flask.request.form["organizer"]
    place = flask.request.form["place"]
  except:return "INVALID_INFO"

  images = flask.request.files["gallery"]
  fbm.createEvent(title, organiser, description, dateTime, place, images)
  return "true"

@server.route("/download/eventInfo", methods=["POST"])
def getEventInfo():
  n = int(flask.request.form.get("n", 5))
  res = fbm.getEventInfo(n=n)

  if isinstance(res, str): #response is an error code
    return res
  return json.dumps(res)

@server.route("/download/gallery", methods=["POST"])
def downloadGallery():
  id = flask.request.form["id"]
  gallery = fbm.downloadEventGallery(id)
  return flask.send_file(io.BytesIO(gallery), download_name="gallery.zip")

@server.route("/participate")
def participate():
  eventID = flask.request.form["eventID"]
  userID = flask.request.form["userID"]
  return fbm.eventSignUp(eventID, userID)

if __name__ == "__main__":
  socketIO.run(server, host="0.0.0.0")