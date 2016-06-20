# -*- coding: utf-8 -*-

# Standard:
# https://github.com/ethereum/wiki/wiki/JSON-RPC
# Admin:
# https://github.com/ethereum/go-ethereum/wiki/Management-APIs#personal_listaccounts


class Namespace(object):
    name = ""

    methods = ()

    def __init__(self, api):
        self.api = api

    def __call__(self, command, *args):
        return self.api.call_ns(self, command, *args)


class AdminNamespace(Namespace):
    name = "admin"


class EthNamespace(Namespace):
    name = "eth"

    GAS_DEFAULT = 90000

    def protocolVersion(self):
        return self("protocolVersion")

    def syncing(self):
        return self("syncing")

    def coinbase(self):
        return self("coinbase")

    def compileSolidity(self, code):
        return self("compileSolidity", code)

    def sendTransaction(self, _from, to=None,
                        gas=None,
                        gasPrice=None,
                        value=None,
                        data=None,
                        nonce=None):
        """
            https://github.com/ethereum/wiki/wiki/JSON-RPC#eth_sendtransaction
        """
        params = {}
        params['from'] = _from

        if to is not None:
            params['to'] = to

        if gas is not None:
            params["gas"] = hex(gas)

        if gasPrice is not None:
            params['gasPrice'] = hex(gasPrice)

        if value is not None:
            params['value'] = hex(value)

        if data is not None:
            params['data'] = data

        if nonce is not None:
            params['nonce'] = nonce

        return self("sendTransaction", params)

    def getTransactionReceipt(self, txhash):
        return self("getTransactionReceipt", txhash)

class MinerNamespace(Namespace):
    name = "miner"


class NetNamespace(Namespace):
    name = "net"

    def version(self):
        return self("version")

    def listening(self):
        return self("listening")

    def peerCount(self):
        return self("peerCount")


class ShhNamespace(Namespace):
    name = "shh"


class TxpoolNamespace(Namespace):
    name = "txpool"


class PersonalNamespace(Namespace):
    name = "personal"

    def listAccounts(self):
        return self("listAccounts")

    def unlockAccount(self, address, passphrase, timeout=300):
        return self("unlockAccount", address, passphrase, timeout)


class Web3Namespace(Namespace):
    name = "web3"

    def clientVersion(self):
        return self("clientVersion")

    def sha3(self, s):
        return self("sha3", s)
