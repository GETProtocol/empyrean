import os
import socket
import json

import requests

from . import exceptions


class Connector(object):

    def parse_result(self, data):
        # print(data)
        if 'error' in data:
            error = data['error']
            code = error.get('code', 0)
            message = error.get('message')

            for exc in exceptions.all:
                exc.raise_if_matches(code, message)

        return data['result']


class IPCConnector(Connector):

    def __init__(self, path=None):
        self.path = path or self.generic_path()
        self.sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        self._connect()

    def generic_path(self):
        return os.path.join(os.path.expanduser("~"), ".ethereum", "geth.ipc")

    def _connect(self):
        self.sock.connect(self.path)
        self.sock.settimeout(2)

    def invoke(self, data):
        serialized = json.dumps(data)
        self.sock.sendall(serialized.encode("utf8"))
        res = self.sock.recv(10000)
        try:
            parsed_res = json.loads(res.decode("utf8"))
        except ValueError:
            raise
        return self.parse_result(parsed_res).encode('utf8')


class HTTPConnector(Connector):

    def __init__(self, url):
        self.url = url

    def invoke(self, data):
        serialized = json.dumps(data)
        r = requests.post(self.url, data=serialized)
        return self.parse_result(r.json()).encode('utf8')
