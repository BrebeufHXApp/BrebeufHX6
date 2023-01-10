import firebase_admin
from firebase_admin import firestore

cred = firebase_admin.credentials.Certificate("credentials.json")
app = firebase_admin.initialize_app(cred)