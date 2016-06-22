import sha3
import rlp
import binascii
import math

# utils


def multiple_of_32(i):
    return math.ceil(i / 32) * 32


def tohex(b):
    return binascii.hexlify(b)


def enc_uint256(i):
    return rlp.utils.int_to_big_endian(i).rjust(32, b'\x00')


def enc_string(s):
    """ a variable length string """
    slen = len(s)
    lenpart = rlp.utils.int_to_big_endian(slen).rjust(32, b'\x00')
    stringpart = s.encode('utf8').ljust(multiple_of_32(slen), b'\x00')
    return lenpart + stringpart


def enc_method(signature):
    # signature must be "canonical", e.g. int[256] -> uint256
    methodhash = sha3.keccak_256(signature.encode("ascii")).hexdigest()
    method = methodhash[:8].encode('ascii')
    return method


def build_payload(signature, *args):
    method = enc_method(signature)
    args = enc_uint256(args[0])
    return tohex(method + args)


print(build_payload("multiply(uint256)", 6))
print(tohex(enc_string("Hello, world!")))
