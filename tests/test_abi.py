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
from empyrean.abi import ABIType

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


@pytest.fixture(params=range(8, 264, 8))
def multiple_of_eight(request):
    return request.param


@pytest.fixture(params=range(1, 33))
def one_to_thirtytwo(request):
    return request.param


class TestUintType:

    def test_size(self, multiple_of_eight):
        assert ABIType("uint{}".format(multiple_of_eight)).size() == 32

    @pytest.mark.parametrize("size,expect",
                             [(i, i * 32) for i in (1, 2, 10, 20, 100)])
    def test_fixedarray_size(self, multiple_of_eight, size, expect):
        t = "uint{}[{}]".format(multiple_of_eight, size)
        assert ABIType(t).size() == expect

    def test_not_dynamic(self, multiple_of_eight):
        assert not ABIType("uint{}".format(multiple_of_eight)).isdynamic

    def test_enc(self, multiple_of_eight):
        t = ABIType("uint{}".format(multiple_of_eight))
        assert tohex(t.enc(0)) == \
            b'0000000000000000000000000000000000000000000000000000000000000000'
        assert tohex(t.enc(1)) == \
            b'0000000000000000000000000000000000000000000000000000000000000001'
        assert tohex(t.enc(42)) == \
            b'000000000000000000000000000000000000000000000000000000000000002a'

    def test_max(self, multiple_of_eight):
        t = ABIType("uint{}".format(multiple_of_eight))
        assert t.enc(2**multiple_of_eight - 1)

    def test_too_small(self, multiple_of_eight):
        t = ABIType("uint{}".format(multiple_of_eight))
        with pytest.raises(ValueError):
            tohex(t.enc(-1))

    def test_too_large(self, multiple_of_eight):
        t = ABIType("uint{}".format(multiple_of_eight))
        with pytest.raises(ValueError):
            tohex(t.enc(2**multiple_of_eight))

    def test_uint_unsized_array_is_dynamic(self, multiple_of_eight):
        assert ABIType("uint{}[]".format(multiple_of_eight)).isdynamic


class TestIntType:

    def test_int_size(self, multiple_of_eight):
        assert ABIType("int{}".format(multiple_of_eight)).size() == 32

    @pytest.mark.parametrize("size,expect",
                             [(i, i * 32) for i in (1, 2, 10, 20, 100)])
    def test_int_fixedarray_size(self, multiple_of_eight, size, expect):
        t = "uint{}[{}]".format(multiple_of_eight, size)
        assert ABIType(t).size() == expect

    def test_int_is_not_dynamic(self, multiple_of_eight):
        assert not ABIType("int{}".format(multiple_of_eight)).isdynamic

    def test_enc(self, multiple_of_eight):
        t = ABIType("int{}".format(multiple_of_eight))
        assert tohex(t.enc(0)) == \
            b'0000000000000000000000000000000000000000000000000000000000000000'
        assert tohex(t.enc(1)) == \
            b'0000000000000000000000000000000000000000000000000000000000000001'
        assert tohex(t.enc(42)) == \
            b'000000000000000000000000000000000000000000000000000000000000002a'

        bytes = multiple_of_eight // 8

        assert tohex(t.enc(-1)) == \
            b'00' * (32 - bytes) + b'ff' * (bytes - 1) + b'ff'
        assert tohex(t.enc(-42)) == \
            b'00' * (32 - bytes) + b'ff' * (bytes - 1) + b'd6'

    def test_too_small(self, multiple_of_eight):
        t = ABIType("int{}".format(multiple_of_eight))
        with pytest.raises(ValueError):
            tohex(t.enc(-2**(multiple_of_eight - 1) - 1))

    def test_too_large(self, multiple_of_eight):
        t = ABIType("int{}".format(multiple_of_eight))
        with pytest.raises(ValueError):
            tohex(t.enc(2**(multiple_of_eight - 1) + 1))

    def test_int_unsized_array_is_dynamic(self, multiple_of_eight):
        assert ABIType("int{}[]".format(multiple_of_eight)).isdynamic


class TestBytesType:

    def test_bytes_size(self, one_to_thirtytwo):
        assert ABIType("bytes{}".format(one_to_thirtytwo)).size() == 32

    def test_bytes_is_not_dynamic(self, one_to_thirtytwo):
        assert not ABIType("bytes{}".format(one_to_thirtytwo)).isdynamic

    def test_bytes_is_dynamic(self):
        assert ABIType("bytes").isdynamic


class TestBoolType:

    def test_bool_size(self):
        assert ABIType("bool").size() == 32

    def test_bool_is_not_dynamic(self):
        assert not ABIType("bool").isdynamic

    @pytest.mark.parametrize("falsy", [0, '', b'', [], {}, set()])
    def test_enc_false(self, falsy):
        t = ABIType("bool")
        assert tohex(t.enc(falsy)) == \
            b'0000000000000000000000000000000000000000000000000000000000000000'

    @pytest.mark.parametrize("truthy",
                             [1, -1, 'x', b'x', [1], {1}, {1: 1}, object()])
    def test_enc_true(self, truthy):
        t = ABIType("bool")
        assert tohex(t.enc(truthy)) == \
            b'0000000000000000000000000000000000000000000000000000000000000001'

    def test_bool_unsized_array_is_dynamic(self):
        assert ABIType("bool[]").isdynamic


class TestFixedType:

    def test_fixed_size(self, multiple_of_eight):
        # wrong! m+n = 256! (so 256 itself isn't a usable multiple_of_eight)
        assert ABIType("fixed{0}x{0}".format(multiple_of_eight)).size() == 32

    def test_fixed_is_not_dynamic(self, multiple_of_eight):
        assert not ABIType("fixed{0}x{0}".format(multiple_of_eight)).isdynamic

    def test_fixed_unsized_array_is_dynamic(self, multiple_of_eight):
        assert ABIType("fixed{0}x{0}[]".format(multiple_of_eight)).isdynamic


class TestSizeTypeClass:

    @pytest.mark.parametrize("size,expect",
                             [(i, i * 32) for i in (1, 2, 10, 20, 100)])
    def test_fixed_fixedarray_size2(self, multiple_of_eight, size, expect):
        t = "fixed{0}x{0}[{1}]".format(multiple_of_eight, size)
        assert ABIType(t).size() == expect


class TestDynamicTypeClass:

    def test_string_is_dynamic(self):
        assert ABIType("string").isdynamic


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
                                (0x123, [0x456, 0x789], "1234567890",
                                 "Hello, world!"))) == (
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
