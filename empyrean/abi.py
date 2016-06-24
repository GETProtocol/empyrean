import sha3
import rlp
import binascii
import math

# utils


def multiple_of_32(i):
    return (math.ceil(i / 32)) * 32


def tohex(b):
    return binascii.hexlify(b)


def enc_uint256(i):
    return rlp.utils.int_to_big_endian(i).rjust(32, b'\x00')

"""
    Dynamic types (such as string) don't get encoded directly but
    get appended to the end. Their offset within the entire string
    gets inserted in stead.

    E.g. <static type><static type><offset 1><static type><dynamic type>
    where offset 1 is the len of all parts up to <dynamic type>

    so there's a static part (possibly containing offsets of dynamic
    arguments) and a dynamic part
"""
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


# print(build_payload("multiply(uint256)", 6))
# print(tohex(enc_string("Hello, world!")))
