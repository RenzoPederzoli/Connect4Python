import requests

class Comms(object):

    def __init__(self) -> None:
        self._url = 'http://127.0.0.1:5000/'
        self._auth = {
            'USERNAME' : '',
            'PASSWORD' : ''
        }
        self._gameid = ''
        self._game_obj = ''

    def __str__(self):
        return 

    def signup(self, uname, upass):
        payload = {'USERNAME':uname, 'PASSWORD':upass}
        r = requests.post(self._url+"signup", json=payload)
        if r.status_code == 200:
            self._auth['USERNAME'] = uname
            self._auth['PASSWORD'] = upass
            return r
        elif r.json()['ERR'] == 'BAD SIGNUP | USER ALREADY EXISTS': # Quick fix to handle this
            return self.login(uname, upass)
        else:
            return r

    def login(self, uname, upass):
        payload = {'USERNAME':uname, 'PASSWORD':upass}
        r = requests.post(self._url+"login", json=payload)
        if r.status_code == 200:
            self._auth['USERNAME'] = uname
            self._auth['PASSWORD'] = upass
            return r

        else:
            return r

    def startgame(self):
        r = requests.post(self._url+"startgame", json=self._auth)
        if r.status_code == 200:
            res = r.json()
            self._gameid = res['GAMEID']
            self._game_obj = res['GAME']
            return r

        else:
            return r

    #call many times to see if my turn yet or game found
    def getgame(self):
        r = requests.get(self._url+"getgame/"+self._gameid, json=self._auth)
        if r.status_code == 200:
            res = r.json()
            self._game_obj = res['GAME']
            return r
        else:
            return r

    # No logic in server to prevent move in queiing lobby
    def movegame(self, move):
        r = requests.post(self._url+"movegame/"+self._gameid, json={'CREDENTIALS':self._auth, 'MOVE':move})
        if r.status_code == 200:
            res = r.json()
            self._game_obj = res['GAME']
            return r
        else:
            return r