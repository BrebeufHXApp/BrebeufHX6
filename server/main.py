#apply monkey path to prevent ssl library from raising recursion error
#import gevent.monkey
#gevent.monkey.patch_all()

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

@server.route("/debugging")
def debugging():
  return "true"

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

if __name__ == "__main__":
  socketIO.run(server, host="0.0.0.0")