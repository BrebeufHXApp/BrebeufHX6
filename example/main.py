import flask, json
from flask_cors import CORS
import firebasemanager,sdmxmanager

app = flask.Flask(__name__)
CORS(app)

@app.route("/uploadPetition", methods=["POST"])
def uploadPetition():
    """Upload new petition for official review.
        Include title, body and author(optional)"""
    try:
        args = flask.request.json
        title = args["title"]
        body = args["text"]
        author = args.get("author", "Anonyme")
        email = args["email"]
        result=firebasemanager.uploadPetition(title,body,author,email)
        return result
    except Exception as e:
        return str(e)

@app.route("/votePetition", methods=["GET", "POST"])
def votePetition():
    """Vote to show your support for a petition. Can return 'invalid email' or 'already voted' """
    try:
        args = flask.request.json
        uid = args["uid"]
        email=args["email"]
        message=firebasemanager.votePetition(uid,email)
        return message
    except Exception as e:
        return str(e)

@app.route("/getRandomPetitions", methods=["GET", "POST"])
def getRandomPetitions():
    """Download a number of petitions from online database, sorted in order of votes."""
    try:
        args = flask.request.json
        count = args["count"]
        petitions=firebasemanager.getRandomPetitions(int(count))
        return json.dumps(petitions)
    except Exception as e:
        return str(e)

@app.route("/searchPetitions",methods=["GET","POST"])
def searchPetitions():
    """Search petitions relevent to you. This input is a string of words separated by spaces"""
    try:
        args = flask.request.json
        searchstring = args["searchstring"]
        targets=firebasemanager.searchPetitions(searchstring)
        return json.dumps(targets)
    except Exception as e:
        return str(e)

@app.route("/publishPetition",methods=["GET","POST"])
def publishPetition():
    """Move a petition to the published folder. Not to be implemented in frontend."""
    try:
        args = flask.request.json
        uid = args["uid"]
        firebasemanager.publishPetition(uid)
        return "true"
    except Exception as e:
        return str(e)

@app.route("/countries", methods=["GET", "POST"])
def countries():
    """Get list of all countries in database."""
    try:
        return json.dumps(sdmxmanager.countries)
    except Exception as e:
        return str(e)

@app.route("/getIndicatorsByCountry", methods=["POST"])
def getIndicatorsByCountry():
    """Fetch indicators in a specific country from server. Values may be UNKNOWN, which is represented by an x"""
    try:
        args = flask.request.json
        country = args["country"]
        return json.dumps(sdmxmanager.indicators[country])
    except Exception as e:
        return str(e)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=235, threaded=True)
