import flask, flask_socketio
import firebaseManager as fbm

server = flask.Flask(__name__)
socketIO = flask_socketio.SocketIO(server)

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

if __name__ == "__main__":
  socketIO.run(server, host="0.0.0.0")