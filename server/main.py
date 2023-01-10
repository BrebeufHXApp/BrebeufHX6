import flask, flask-socketio
import firebaseManager as fbm

server = flask.Flask(__name__)
socketIO = flask_socketio.socketIO(server)

if __name__ == "__main__":
  socketIO.run(server, host="0.0.0.0")
