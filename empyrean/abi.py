import re
import sha3
import rlp
import binascii
import math

# utils


def decode_int(data):
    return rlp.sedes.big_endian_int.deserialize(data.lstrip(b"\x00"))


def multiple_of_32(i):
    return (math.ceil(i / 32)) * 32


def tohex(b):
    return binascii.hexlify(b)


def enc_uint256(i, bits=256):
    if i < 0 or i >= 2**bits:
        raise ValueError("Value out of range for uint{}: {}".format(bits, i))
    return rlp.utils.int_to_big_endian(i).rjust(32, b'\x00')


def dec_uint256(data, bits=256):
    # force into number of bits?
    return decode_int(data[:32]), 32


def dec_int256(data, bits=256):
    unsigned = decode_int(data[:32])
    if unsigned >= 2 ** (bits - 1):
        return unsigned - 2 ** bits, 32
    return unsigned, 32


def enc_int256(i, bits=256):
    if i < -2 ** (bits - 1) or i >= 2 ** (bits - 1):
        raise ValueError("Value out of range for int{}: {}".format(bits, i))
    return rlp.utils.int_to_big_endian(i % 2 ** bits).rjust(32, b'\x00')


def enc_bool(i):
    v = 1 if i else 0
    return rlp.utils.int_to_big_endian(v).rjust(32, b'\x00')


def enc_ufixed(i, bits, low, high):

    if bits <= 0 or bits > 256:
        raise ValueError(
            "high+low must be between 0 .. 256 and divisible by 8")

    if high % 8 or low % 8:
        raise ValueError(
            "high+low must be between 0 .. 256 and divisible by 8")

    if i < 0 or i >= 2 ** high:
        raise ValueError("Value out of range for ufixed{}x{}: {}".format(
            high, low, i))

    float_point = i * 2 ** low
    fixed_point = int(float_point)
    return rlp.utils.int_to_big_endian(fixed_point).rjust(32, b'\x00')


def enc_bytes_dynamic(b):
    """ dynamic bytes string """
    return rlp.utils.int_to_big_endian(len(b)).rjust(32, b'\x00') + \
        b.ljust(multiple_of_32(len(b)), b'\x00')


def enc_bytes(b, size):
    """ size can be between 1 .. 32 or 0 (dynamic)"""
    if size == 0:  # dynamic string
        return rlp.utils.int_to_big_endian(len(b)).rjust(32, b'\x00') + \
            b.ljust(multiple_of_32(len(b)), b'\x00')

    if len(b) > 32:
        raise ValueError("Byte string is longer than 32 bytes")
    if len(b) > size:
        raise ValueError("Byte string is larger than defined {}".format(size))
    remainder = 32 - len(b)
    return b + b'\x00' * remainder


def parse_signature(signature):
    """ parse method(type, type, type) into method and types.
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

    def getlowhigh(self):
        spec = re.search("(\d+)x?(\d+)?", self.type)
        if spec:
            groups = spec.groups()
            if groups[1]:
                return int(groups[0]), int(groups[1])
        return 0, 256

    def size(self):
        return self.count * 32

    def primitive_enc(self, value):
        # XXX tests!
        if self.type == "address":
            return enc_uint256(value, 160)

        if self.type.startswith("uint"):
            return enc_uint256(value, self.bits)
        if self.type.startswith("int"):
            return enc_int256(value, self.bits)
        if self.type == "bool":
            return enc_bool(value)
        if self.type.startswith("bytes"):
            # in the case of bytes size is bytes, not self.bits
            return enc_bytes(value, self.bits)
        if self.type.startswith("ufixed"):
            low, high = self.getlowhigh()
            return enc_ufixed(value, self.bits, low, high)
        raise TypeError("Unknown type {}".format(self.type))

    def primitive_dec(self, data):
        if self.type.startswith("uint"):
            return dec_uint256(data, self.bits)
        if self.type.startswith("int"):
            return dec_int256(data, self.bits)
        raise TypeError("Unknown (decoding) type {}".format(self.type))

    def enc(self, value):
        res = b""

        if self.isdynamic:
            if self.isarray:
                res += lentype.enc(len(value))
                for array_value in value:
                    res += self.primitive_enc(array_value)
            if self.type == "bytes":
                return enc_bytes_dynamic(value)
            # TODO: string
        elif self.isarray:

            for array_index in range(self.count):
                res += self.primitive_enc(value[array_index])
        else:
            res += self.primitive_enc(value)

        return res

    def dec(self, data):
        """ fetch value from data. In the case of dynamic types, data
            will also hold the rest of the tail since the called won't
            know where it ends """
        pos = 0
        if self.isdynamic:
            if self.isarray:
                res = []
                count = decode_int(data[:lentype.size()])
                pos += lentype.size()
                for i in range(count):
                    val, bytesread = self.primitive_dec(data[pos:])
                    res.append(val)
                    pos += bytesread
                return res
        elif self.isarray:
            for i in range(self.count):
                val, bytesread = self.primitive_dec(data[:pos])
                res.append(val)
                pos += bytesread
        else:
            return self.primitive_dec(data)[0]


lentype = ABIType("uint256")


class StaticArg:

    def __init__(self, val):
        self.val = val

    def head(self, headsize):
        return self.val

    def tail(self):
        return b''


class DynamicArg(StaticArg):

    def __init__(self, val, tailoffset):
        super().__init__(val)
        self.tailoffset = tailoffset

    def head(self, headsize):
        return lentype.enc(headsize + self.tailoffset)

    def tail(self):
        return self.val


def encode_abi(signature, args):
    """ Encode a number of arguments given a specific signature.

        E.g. encode_abi(["uint32[]"], [[6, 69]])
    """
    parts = []
    headsize = 0
    tailsize = 0

    assert len(signature) == len(args)

    for type, arg in zip(signature, args):
        type = ABIType(type)
        encoded = type.enc(arg)

        if type.isdynamic:
            headsize += 32
            parts.append(DynamicArg(encoded, tailsize))
            tailsize += len(encoded)
        else:
            headsize += type.size()
            parts.append(StaticArg(encoded))

    return b"".join(a.head(headsize) for a in parts) + \
           b"".join(a.tail() for a in parts)


def build_payload(signature, *args):
    m, a = parse_signature(signature)
    method = enc_method(signature)
    args = encode_abi(a, args)
    return tohex(method + args)


def decode_abi(signature, data):
    """
        Decode the ("abi serialized) result data from a call() invocation
    """
    decoded = []

    data = binascii.unhexlify(data)

    offset = 0
    for type in signature:
        type = ABIType(type)
        if type.isdynamic:
            start = decode_int(data[offset:offset + 32])
            decoded.append(type.dec(data[start:]))
            offset += lentype.size()
        else:
            val = data[offset:offset + type.size()]
            decoded.append(type.dec(val))
            offset += type.size()

    return decoded
