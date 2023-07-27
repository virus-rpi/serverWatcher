import os
import inspect
import time
import asyncio
from scanner import get
from win10toast import ToastNotifier

current_dir = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
toast = ToastNotifier()


def notify(title, text):
    toast.show_toast("Watchtower: " + title, text, duration=5, threaded=True)


class eye:
    _instance = None

    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = super().__new__(cls, *args, **kwargs)
        return cls._instance

    @classmethod
    def restart(cls):
        cls._instance = None

    def __init__(self):
        self.onlinelist = []
        self.db = {}

        try:
            with open('watchlist') as f:
                self.watchlist = f.readlines()
        except FileNotFoundError:
            self.watchlist = {"TheClick.mcserver.us": 25565}

        while True:
            self.update()
            time.sleep(5)

    def update(self):
        if not self.watchlist:
            return
        for i in self.watchlist.keys():
            i = i.strip()
            if i:
                self.check_server(i, self.watchlist[i])

    def check_server(self, ip, port=25565):
        if ip in self.db:
            data_prev = self.db[ip]
        else:
            self.db[ip] = {"version": None, "motd": None,
                           "players": {"max": 0, "online": 0, "players": [{"name": None}]}, "ping": None, "type": None,
                           "country": None, "plugin": None, "rcon": None, "join": None, "shodan": None}
            data_prev = self.db[ip]
        data_new = asyncio.run(get(ip, port, False, False, False))
        self.db[ip] = data_new

        if data_prev['version'] != data_new['version']:
            print(f"Server {ip}: Version changed: {data_prev['version']} -> {data_new['version']}")
            notify(ip, f"Version changed: {data_prev['version']} -> {data_new['version']}")

        if data_prev['players']['max'] != data_new['players']['max']:
            print(f"Server {ip}: Max players changed: {data_prev['players']['max']} -> {data_new['players']['max']}")
            notify(ip, f"Max players changed: {data_prev['players']['max']} -> {data_new['players']['max']}")

        if data_prev['players']['online'] != data_new['players']['online']:
            print(
                f"Server {ip}: Online players changed: {data_prev['players']['online']} -> {data_new['players']['online']}"
            )
            notify(ip, f"Online players changed: {data_prev['players']['online']} -> {data_new['players']['online']}")

        # prev_players = set([entry['name'] for entry in data_prev['players']['players']])
        # new_players = set([entry['name'] for entry in data_new['players']['players']])
        # players_added = new_players - prev_players
        # players_removed = prev_players - new_players

        # if players_added and list(players_added)[0] != None:
        # print(f"Server {ip}: {len(players_added)} players joined: {', '.join(players_added)}")

        # if players_removed and list(players_removed)[0] != None:
        # print(f"Server {ip}: {len(players_removed)} players left: {', '.join(players_removed)}")

        # if data_prev['shodan'] != data_new['shodan']:
        #     print(f"Server {ip}: Shodan info changed: {data_prev['shodan']} -> {data_new['shodan']}")

        # if data_prev['country'] != data_new['country']:
        #     print(f"Server {ip}: Country changed: {data_prev['country']} -> {data_new['country']}")
        #     changed = True

        if data_prev['motd'] != data_new['motd']:
            print(f"Server {ip}: Motd changed: {data_prev['motd']} -> {data_new['motd']}")
            notify(ip, f"Motd changed: {data_prev['motd']} -> {data_new['motd']}")



if __name__ == "__main__":
    eye().restart()
