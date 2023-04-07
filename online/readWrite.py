import requests
import json
import pickle
import base64

class Credentials:
    def __init__(self, username, password):
        self.username = username
        self.password = password

def wakeUpServer():
    r = requests.get("https://programming-club-games.gaioc.repl.co/")
    return r.status_code

def getData(userid, password):

    inData = {"username":userid, "password":password}

    r = requests.post(f"https://programming-club-games.gaioc.repl.co/verify/{userid}", data=inData)
    return (1 if r.status_code != 201 else json.loads(r.text))

def saveData(userid, password, game, saveSlot, data):

    inData = {"username":userid, "password":password, "game":game, "saveSlot":saveSlot, "data":data}
    r = requests.post(f"https://programming-club-games.gaioc.repl.co/save/{userid}", data=inData)
    return (1 if r.status_code != 201 else 0)

def prepareData(data):
    return base64.b64encode(pickle.dumps(data))
def decodePickle(pickled):
    print(pickled, base64.b64decode(pickled), pickle.loads(base64.b64decode(pickled)))
    return pickle.loads(base64.b64decode(pickled))
