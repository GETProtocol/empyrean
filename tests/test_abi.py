#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
test_empyrean
----------------------------------

Tests for `empyrean` module.
"""

import pytest


from empyrean.abi import tohex
from empyrean.abi import enc_string
from empyrean.abi import enc_method

# inspiration: https://github.com/ethereum/pyethereum/blob/develop/ethereum/tests/test_abi.py

class TestMethodABI(object):

    @classmethod
    def setup_class(cls):
        pass

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

    @classmethod
    def teardown_class(cls):
        pass


class TestString(object):
    def test_hello_world(self):
        assert tohex(enc_string("Hello, world")) == (
               b"00000000000000000000000000000000"
               b"00000000000000000000000000000020"
               b"00000000000000000000000000000000"
               b"0000000000000000000000000000000c"
               b"48656c6c6f2c20776f726c6400000000"
               b"00000000000000000000000000000000")
