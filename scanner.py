import json
import socket
import requests
import time
import simplejson
import ping3


def measure_ping_time(server_ip):
    rtt = ping3.ping(server_ip)
    if rtt is not None:
        return round(rtt * 1000, 2)
    else:
        return None


def read(sock, n):
    A = b''
    while len(A) < n:
        A += sock.recv(n - len(A))
    return A


def read_varint(sock, remaining=0):
    A = 0
    for B in range(5):
        C = ord(sock.recv(1))
        A |= (C & 127) << 7 * B
        if not C & 128:
            return remaining - (B + 1), A


def read_header(sock, compression=False):
    B = sock
    C, A = read_varint(B)
    if compression:
        A, C = read_varint(B, A)
    A, D = read_varint(B, A)
    return A, D


def get_status(addr, port=25565):
    start_time = time.perf_counter()
    sock = socket.create_connection((addr, port), 0.7)
    end_time = time.perf_counter()
    ping = round((end_time - start_time) * 1000, 2)
    sock.send(b"\x06\x00\x00\x00\x00\x00\x01")
    sock.send(b"\x01\x00")
    length, _ = read_header(sock)
    length, _ = read_varint(sock, length)
    data = json.loads(read(sock, length))
    data['ping'] = ping
    return data


def update_country(ip):
    try:
        country = requests.get(f"https://geolocation-db.com/json/{ip}&position=true").json()['country_name']
    except simplejson.errors.JSONDecodeError or requests.exceptions.RetryError:
        country = None
    return country


def update_players(data, advanced):
    try:
        online_players = data['players']['online']
    except KeyError:
        online_players = 0
    try:
        max_online_players = data['players']['max']
    except KeyError:
        max_online_players = 20
    if advanced:
        if 'sample' in data['players']:
            players = data['players']['sample']
            return {'online': online_players, 'max': max_online_players, 'players': players}
        else:
            return {'online': online_players, 'max': max_online_players, 'players': None}
    else:
        return {'online': online_players, 'max': max_online_players, 'players': None}


def update_version(data):
    try:
        version = data['version']['name']
        return version
    except KeyError:
        pass
    except TypeError:
        pass


def update_motd(data):
    try:
        motd = data['description']['text']
        if motd == '':
            motd = data['description']['extra'][0]['text']
    except:
        try:
            motd = data['description']['extra'][0]['text']
        except:
            try:
                motd = data['description']
            except:
                motd = 'Non compatible motd'
    return motd


def join_server(ip, port):
    requests.get(f'http://localhost:25567/connect?ip={ip}&port={port}')
    time.sleep(1)
    while "net.minecraft.class_412" in requests.get(f'http://localhost:25567/getScreen').text:
        time.sleep(.3)
    time.sleep(3)
    r = requests.get(f'http://localhost:25567/getDisconnectReason')
    if r.text != 'Not on a DisconnectedScreen':
        if 'white' in r.text or 'White' in r.text:
            requests.get(f'http://localhost:25567/disconnect')
            return True
    r = requests.get(f'http://localhost:25567/getScreen')
    if r.status_code == 404:
        requests.get(f'http://localhost:25567/disconnect')
        return False
    requests.get(f'http://localhost:25567/disconnect')


def update_shodon(ip):
    try:
        result = requests.get(f'https://internetdb.shodan.io/{ip}')
    except requests.exceptions.RetryError:
        return None
    if result.status_code == 200:
        return result.text


async def compile_data(ip, port, data, advanced, join, shodon):
    compiled_data = {}
    if data != 'Offline' and data != 'Connection reset' and data != 'Connection refused' and data != 'Type error':
        compiled_data["version"] = update_version(data)
        compiled_data["motd"] = update_motd(data)
        compiled_data["players"] = update_players(data, advanced)
        compiled_data["ping"] = data['ping']
        if advanced:
            compiled_data["type"] = None
            compiled_data["country"] = update_country(ip)
            compiled_data["plugin"] = None
        if join:
            compiled_data["join"] = join_server(ip, port)
        if shodon:
            compiled_data["shodan"] = update_shodon(ip)
    else:
        compiled_data = {"version": None, "motd": None, "players": None, "ping": None, "type": None, "country": None, "plugin": None, "rcon": None, "join": None, "shodan": None}

    return compiled_data


async def get_data(ip, port=25565):
    try:
        r = get_status(ip, port)
    except TimeoutError:
        r = 'Offline'
    except ConnectionResetError:
        r = 'Connection reset'
    except ConnectionRefusedError:
        r = 'Connection refused'
    except TypeError:
        r = 'Type error'
    return r


async def get(ip, port, advanced=True, join=False, shodon=True):
    try:
        data = await get_data(ip, port)
        return await compile_data(ip, port, data, advanced, join, shodon)
    except TimeoutError:
        return {"version": None, "motd": None, "players": None, "ping": None, "type": None, "country": None, "plugin": None, "rcon": None, "join": None, "shodan": None}
    except ConnectionResetError:
        return {"version": None, "motd": None, "players": None, "ping": None, "type": None, "country": None, "plugin": None, "rcon": None, "join": None, "shodan": None}
    except ConnectionRefusedError:
        return {"version": None, "motd": None, "players": None, "ping": None, "type": None, "country": None, "plugin": None, "rcon": None, "join": None, "shodan": None}
    except TypeError:
        return {"version": None, "motd": None, "players": None, "ping": None, "type": None, "country": None, "plugin": None, "rcon": None, "join": None, "shodan": None}
