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


class BaseType:

    def __init__(self, type):
        self.type = type
        self.bits = self.getbits()

    def getbits(self):
        spec = re.search("(\d+)x?(\d+)?", self.type)
        if spec:
            groups = spec.groups()
            if groups[1]:
                return int(groups[0]) + int(groups[1])
            return int(groups[0])
        return 0


class UIntType(BaseType):

    def enc(self, i):
        if i < 0 or i >= 2**self.bits:
            raise ValueError(
                "Value out of range for uint{}: {}".format(self.bits, i))
        return rlp.utils.int_to_big_endian(i).rjust(32, b'\x00')

    def dec(self, data):
        # force into number of bits?
        return decode_int(data[:32]), 32


class IntType(BaseType):

    def dec(self, data):
        unsigned = decode_int(data[:32])
        if unsigned >= 2 ** (self.bits - 1):
            return unsigned - 2 ** self.bits, 32
        return unsigned, 32

    def enc(self, i):
        if i < -2 ** (self.bits - 1) or i >= 2 ** (self.bits - 1):
            raise ValueError(
                "Value out of range for int{}: {}".format(self.bits, i))
        return rlp.utils.int_to_big_endian(i % 2 ** self.bits).rjust(32, b'\x00')


class BoolType(BaseType):

    def enc(self, i):
        v = 1 if i else 0
        return rlp.utils.int_to_big_endian(v).rjust(32, b'\x00')

    def dec(self, data):
        """ strictly speaking this will also return \xff * 32 as bool
            though the specification only mentions 1 as true value """
        return bool(decode_int(data[:32])), 32


class FixedType(BaseType):

    def __init__(self, type):
        super().__init__(type)
        self.high = 0
        self.low = 256

        spec = re.search("(\d+)x?(\d+)?", self.type)
        if spec:
            groups = spec.groups()
            if groups[1]:
                self.high = int(groups[0])
                self.low = int(groups[1])

        if self.high % 8 or self.low % 8:
            raise ValueError(
                "high+low must be between 0 .. 256 and divisible by 8")

    def enc(self, i):
        if self.bits <= 0 or self.bits > 256:
            raise ValueError(
                "high+low must be between 0 .. 256 and divisible by 8")

        if i < -2 ** (self.high - 1) or i >= 2 ** (self.high - 1):
            raise ValueError("Value out of range for fixed{}x{}: {}".format(
                self.high, self.low, i))

        float_point = i * 2 ** self.low
        fixed_point = int(float_point)
        value = fixed_point % 2 ** 256
        return rlp.utils.int_to_big_endian(value).rjust(32, b'\x00')

    def dec(self, data):
        i = decode_int(data[:32])
        if i >= 2 ** (self.bits - 1):
            i -= 2 ** self.bits
        return i / 2 ** self.low, 32


class UFixedType(FixedType):

    def enc(self, i):

        if self.bits <= 0 or self.bits > 256:
            raise ValueError(
                "high+low must be between 0 .. 256 and divisible by 8")

        if i < 0 or i >= 2 ** self.high:
            raise ValueError("Value out of range for ufixed{}x{}: {}".format(
                self.high, self.low, i))

        float_point = i * 2 ** self.low
        fixed_point = int(float_point)
        return rlp.utils.int_to_big_endian(fixed_point).rjust(32, b'\x00')

    def dec(self, data):
        return decode_int(data[:32]) / 2 ** self.low, 32


class BytesType(BaseType):
    def __init__(self, type):
        super().__init__(type)
        self.size = self.bits

    def enc(self, b):
        """ size can be between 1 .. 32 or 0 (dynamic)"""
        if self.size == 0:  # dynamic string
            return rlp.utils.int_to_big_endian(len(b)).rjust(32, b'\x00') + \
                b.ljust(multiple_of_32(len(b)), b'\x00')

        if len(b) > 32:
            raise ValueError("Byte string is longer than 32 bytes")
        if len(b) > self.size:
            raise ValueError(
                "Byte string is larger than defined {}".format(self.size))
        remainder = 32 - len(b)
        return b + b'\x00' * remainder

    def dec(self, data):
        if self.size == 0:
            self.size = decode_int(data[:lentype.size()])
            bytesdata = data[lentype.size():lentype.size() +
                             multiple_of_32(self.size)]
            return bytesdata.rstrip(b'\x00'), lentype.size() + multiple_of_32(self.size)

        return data[:self.size].rstrip(b'\x00'), 32


class StringType(BytesType):

    def enc(self, b):
        return super().enc(b.encode('utf8'))

    def dec(self, data):
        bytes, len = super().dec(data)
        return bytes.decode('utf8'), len

class AddressType(UIntType):
    def __init__(self, type):
        super().__init__(type)
        self.bits = 160

decoders = dict(
    int=IntType,
    uint=UIntType,
    fixed=FixedType,
    ufixed=UFixedType,
    bool=BoolType,
    bytes=BytesType,
    string=StringType,
    address=AddressType
)


def parse_signature(signature):
    """ parse method(type, type, type) into method and types.
        types are not normalized """

    try:
        method, *rest, _ = re.split("[(),]", signature)
    except ValueError:  # didn't get the expected amount of items
        raise

    args = [x for x in rest if x]

    return method, args


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
        self.basetype = re.match("^([a-z]+)(\d+)?", type).group(1)
        self.decoder = decoders.get(self.basetype)(type)

        if '[' in self.type:
            self.isarray = True
            _, scount, _ = re.split(r'[\[\]]', type)
            if scount == '':
                self.count = 0
                self.isdynamic = True
            else:
                self.count = int(scount)

    def size(self):
        return self.count * 32

    def primitive_enc(self, value):
        if self.type.startswith("address"):
            return self.decoder.enc(value, 160)

        if self.type.startswith("uint"):
            return self.decoder.enc(value)
        if self.type.startswith("int"):
            return self.decoder.enc(value)
        if self.type.startswith("bool"):
            return self.decoder.enc(value)
        if self.type.startswith("bytes"):
            # in the case of bytes size is bytes, not self.bits
            return self.decoder.enc(value)
        if self.type.startswith("string"):
            # in the case of string size is bytes, not self.bits
            return self.decoder.enc(value)
        if self.type.startswith("ufixed"):
            return self.decoder.enc(value)
        if self.type.startswith("fixed"):
            return self.decoder.enc(value)
        raise TypeError("Unknown type {}".format(self.type))

    def primitive_dec(self, data):
        if self.type.startswith("address"):
            return self.decoder.dec(data)

        if self.type.startswith("uint"):
            return self.decoder.dec(data)
        if self.type.startswith("int"):
            return self.decoder.dec(data)
        if self.type.startswith("bool"):
            return self.decoder.dec(data)
        if self.type.startswith("bytes"):
            # again, with bytes self.bits is actually number of bytes
            return self.decoder.dec(data)
        if self.type.startswith("string"):
            # again, with string self.bits is actually number of bytes
            return self.decoder.dec(data)
        if self.type.startswith("ufixed"):
            return self.decoder.dec(data)
        if self.type.startswith("fixed"):
            return self.decoder.dec(data)

        raise TypeError("Unknown (decoding) type {}".format(self.type))

    def enc(self, value):
        res = b""

        if self.isdynamic:
            if self.isarray:
                res += lentype.enc(len(value))
                for array_value in value:
                    res += self.primitive_enc(array_value)
            if self.type == "bytes":
                return self.decoder.enc(value)
            if self.type == "string":
                return self.decoder.enc(value)
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
                    if not data[pos:]:
                        raise ValueError(
                            "Ran out of data. Wrong signature perhaps?")
                    val, bytesread = self.primitive_dec(data[pos:])
                    res.append(val)
                    pos += bytesread
                return res
            if self.type == "bytes":
                return self.decoder.dec(data)[0]
            if self.type == "string":
                return self.decoder.dec(data)[0]
        elif self.isarray:
            res = []
            for i in range(self.count):
                if not data[pos:]:
                    raise ValueError(
                        "Ran out of data. Wrong signature perhaps?")
                val, bytesread = self.primitive_dec(data[pos:])
                res.append(val)
                pos += bytesread
            return res
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
    if data.startswith(b"0x"):
        data = data[2:]
    data = binascii.unhexlify(data)
    decoded = []

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
