# -*- coding: utf-8 -*-

from .connectors import IPCConnector, HTTPConnector

#   --ipcapi "admin,eth,debug,miner,net,shh,txpool,personal,web3" API's offered over the IPC-RPC interface


from .methods import AdminNamespace, EthNamespace
from .methods import MinerNamespace, NetNamespace
from .methods import ShhNamespace, TxpoolNamespace
from .methods import PersonalNamespace, Web3Namespace


class API(object):
    connector_class = None

    def __init__(self, connectiondata):
        self.connector = self.connector_class(connectiondata)

        self.admin = AdminNamespace(self)
        self.eth = EthNamespace(self)
        self.miner = MinerNamespace(self)
        self.net = NetNamespace(self)
        self.shh = ShhNamespace(self)
        self.txpool = TxpoolNamespace(self)
        self.personal = PersonalNamespace(self)
        self.web3 = Web3Namespace(self)

    def _call(self, command, *args):
        # id can be used to match request/response. Makes most sense
        # in async setup
        data = dict(jsonrpc='2.0',
                    method=command,
                    params=args,
                    id=1)

        res = self.connector.invoke(data)
        # print("RES", res)
        return res

    def call_ns(self, ns, command, *args):
        nscommand = "{0}_{1}".format(ns.name, command)
        return self._call(nscommand, *args)


class IPCAPI(API):
    connector_class = IPCConnector


class HTTPAPI(API):
    connector_class = HTTPConnector
