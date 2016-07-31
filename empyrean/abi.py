import re
import sha3
import rlp
import binascii
import math

# utils


def multiple_of_32(i):
    return (math.ceil(i / 32)) * 32


def tohex(b):
    return binascii.hexlify(b)


def enc_uint256(i, bits=256):
    if i < 0 or i >= 2**bits:
        raise ValueError("Value out of range for uint{}: {}".format(bits, i))
    return rlp.utils.int_to_big_endian(i).rjust(32, b'\x00')


def enc_int256(i, bits=256):
    if i < -2 ** (bits - 1) or i >= 2 ** (bits - 1):
        raise ValueError("Value out of range for int{}: {}".format(bits, i))
    return rlp.utils.int_to_big_endian(i % 2 ** bits).rjust(32, b'\x00')


def enc_bool(i):
    v = 1 if i else 0
    return rlp.utils.int_to_big_endian(v).rjust(32, b'\x00')


def parse_signature(signature):
    """ parse method(type,type,type) into method and types.
        types are not normalized """

    try:
        method, *rest, _ = re.split("[(),]", signature)
    except ValueError:  # didn't get the expected amount of items
        raise

    args = [x for x in rest if x]

    return method, args


def enc_string(s):
    """ a variable length string """

    slen = len(s)
    static = b''
    dynamic = b''

    # 32 being the len of its own encoding
    static = rlp.utils.int_to_big_endian(32).rjust(32, b'\x00')
    lenpart = rlp.utils.int_to_big_endian(slen).rjust(32, b'\x00')
    stringpart = s.encode('utf8').ljust(multiple_of_32(slen), b'\x00')

    dynamic = lenpart + stringpart
    return static + dynamic


def enc_method(signature):
    # signature must be "canonical", e.g. int[256] -> uint256
    methodhash = sha3.keccak_256(signature.encode("ascii")).digest()
    method = methodhash[:4]
    return method


def build_payload(signature, *args):
    method = enc_method(signature)
    args = enc_uint256(args[0])
    return tohex(method + args)


class ABIType:

    def __init__(self, type):
        self.type = type
        self.count = 1
        self.isdynamic = self.type in ('string', 'bytes')
        self.isarray = False
        self.bits = self.getbits()

        if '[' in self.type:
            self.isarray = True
            _, scount, _ = re.split(r'[\[\]]', type)
            if scount == '':
                self.count = 0
                self.isdynamic = True
            else:
                self.count = int(scount)

    def getbits(self):
        spec = re.search("(\d+)x?(\d+)?", self.type)
        if spec:
            groups = spec.groups()
            if groups[1]:
                return int(groups[0]) + int(groups[1])
            return int(groups[0])
        return 0

    def size(self):
        return self.count * 32

    def primitive_enc(self, value):
        if self.type.startswith("uint"):
            return enc_uint256(value, self.bits)
        if self.type.startswith("int"):
            return enc_int256(value, self.bits)
        if self.type == "bool":
            return enc_bool(value)
        raise TypeError("Unknown type {}".format(self.type))

    def enc(self, value):
        res = b""

        if self.isdynamic:
            if self.isarray:
                res += lentype.enc(len(value))
                for array_value in value:
                    res += self.primitive_enc(array_value)
            # else handle string, bytes
        elif self.isarray:

            for array_index in range(self.count):
                res += self.primitive_enc(value[array_index])
        else:
            res += self.primitive_enc(value)

        return res

lentype = ABIType("uint256")


def encode_abi(signature, args):
    head = b""
    tail = b""
    headsize = 0

    assert len(signature) == len(args)
    for type, arg in zip(signature, args):
        type = ABIType(type)

        if type.isdynamic:
            headsize += 32
            head += lentype.enc(headsize + len(tail))
            tail += type.enc(arg)
        else:
            headsize += type.size()
            head += type.enc(arg)
    return head + tail


# print(build_payload("multiply(uint256)", 6))
# print(tohex(enc_string("Hello, world!")))
