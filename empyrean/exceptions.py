
# https://github.com/ethereum/wiki/wiki/JSON-RPC-Error-Codes-Improvement-Proposal


class JSONRPCException(Exception):
    code_high = -100000
    code_low = 100000

    def __init__(self, code, message):
        self.code = code
        self.message = message

    def __str__(self):
        return "code {0}: {1}".format(self.code, self.message)

    @classmethod
    def raise_if_matches(cls, code, message):
        if cls.code_low <= code <= cls.code_high:
            raise cls(code, message)


class ParseError(JSONRPCException):
    """ -32700 """
    code_high = -32700
    code_low = -32700


class InvalidRequest(JSONRPCException):
    """ -32600 """
    code_high = -32600
    code_low = -32600


class MethodNotFound(JSONRPCException):
    """ -32601 """
    code_high = -32601
    code_low = -32601


class InvalidParams(JSONRPCException):
    """ -32602 """
    code_high = -32602
    code_low = -32602


class InternalError(JSONRPCException):
    """ -32603 """
    code_high = -32603
    code_low = -32603


class ServerError(JSONRPCException):
    """ -32000 .. -32099 """
    code_high = -32000
    code_low = -32099


# Make sure JSONRPCException is last so it can match by default

all = (ServerError, InternalError, InvalidParams, MethodNotFound,
       InvalidRequest, ParseError, JSONRPCException)
