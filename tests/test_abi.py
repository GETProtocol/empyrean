#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
test_empyrean
----------------------------------

Tests for `empyrean` module.
"""

import pytest


from empyrean.abi import tohex
from empyrean.abi import enc_string, enc_uint256
from empyrean.abi import enc_method
from empyrean.abi import parse_signature
from empyrean.abi import encode_abi

# inspiration:
# https://github.com/ethereum/pyethereum/blob/develop/ethereum/tests/test_abi.py
# https://github.com/ethereum/tests/ABITests


class TestMethodABI:

    def test_short(self):
        assert tohex(enc_method("s()")) == b'86b714e2'

    def test_abi_example_baz(self):
        # https://github.com/ethereum/wiki/wiki/Ethereum-Contract-ABI#examples
        assert tohex(enc_method("baz(uint32,bool)")) == b'cdcd77c0'

    def test_abi_example_bar(self):
        # https://github.com/ethereum/wiki/wiki/Ethereum-Contract-ABI#examples
        assert tohex(enc_method("bar(fixed128x128[2])")) == b'ab55044d'

    def test_abi_example_sam(self):
        # https://github.com/ethereum/wiki/wiki/Ethereum-Contract-ABI#examples
        assert tohex(enc_method("sam(bytes,bool,uint256[])")) == b'a5643bf2'


class TestPrimitiveTypes:
    """ Test encoding of different type/arguments """

    def test_string_hello_world(self):
        assert tohex(enc_string("Hello, world")) == (
            b"00000000000000000000000000000000"
            b"00000000000000000000000000000020"
            b"00000000000000000000000000000000"
            b"0000000000000000000000000000000c"
            b"48656c6c6f2c20776f726c6400000000"
            b"00000000000000000000000000000000")

    def test_uint256_6(self):
        assert tohex(enc_uint256(6)) == (
            b'00000000000000000000000000000000'
            b'00000000000000000000000000000006')

    def test_uint32_69(self):
        assert tohex(enc_uint256(69)) == (
            b'00000000000000000000000000000000'
            b'00000000000000000000000000000045')


class TestABIEncode:

    def test_simple(self):
        assert tohex(encode_abi(["uint32"], [6])) == (
            b'00000000000000000000000000000000'
            b'00000000000000000000000000000006')

    def test_static_size_2(self):
        assert tohex(encode_abi(["uint32[2]"], [[6, 69]])) == (
            b'00000000000000000000000000000000'
            b'00000000000000000000000000000006'
            b'00000000000000000000000000000000'
            b'00000000000000000000000000000045')

    def test_dynamic_2_args(self):
        assert tohex(encode_abi(["uint32[]"], [[6, 69]])) == (
            b'00000000000000000000000000000000'
            b'00000000000000000000000000000020'
            b'00000000000000000000000000000000'
            b'00000000000000000000000000000002'
            b'00000000000000000000000000000000'
            b'00000000000000000000000000000006'
            b'00000000000000000000000000000000'
            b'00000000000000000000000000000045')

    # @pytest.skip("not there yet")
    def xtest_example(self):
        assert tohex(encode_abi(["uint", "uint32[]", "bytes10", bytes],
                                (0x123, [0x456, 0x789], "1234567890", "Hello, world!"))) == (
            b'0000000000000000000000000000000000000000000000000000000000000123'
            b'0000000000000000000000000000000000000000000000000000000000000080'
            b'3132333435363738393000000000000000000000000000000000000000000000'
            b'00000000000000000000000000000000000000000000000000000000000000e0'
            b'0000000000000000000000000000000000000000000000000000000000000002'
            b'0000000000000000000000000000000000000000000000000000000000000456'
            b'0000000000000000000000000000000000000000000000000000000000000789'
            b'000000000000000000000000000000000000000000000000000000000000000d'
            b'48656c6c6f2c20776f726c642100000000000000000000000000000000000000'

        )


class TestSignatureParser:

    def test_empty(self):
        assert parse_signature("method()") == ("method", [])

    def test_single_arg(self):
        assert parse_signature("method(a)") == ("method", ["a"])

    def test_multi_args(self):
        assert parse_signature("method(a,b,c)") == ("method", ["a", "b", "c"])

    def test_parse_error(self):
        with pytest.raises(ValueError):
            parse_signature("method")
