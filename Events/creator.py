import requests

title = input("Title: ")
dateTime = input("date@time (2023-01-14 @ 17:30:00): ")
organizer = "Eco person" #input("Organizer: ")
place = input("Place: ")
description = input("Description: ")
file = input("file: ")

data = {
    "title":title,
    "description":description,
    "dateTime":dateTime,
    "organizer":organizer,
    "place":place
}

if requests.post(
    "http://192.168.1.8:5000/createEvent", data=data,
    files={"gallery":open(file, "rb")}).text == "true":
    print("Success")
else:print("failed")
