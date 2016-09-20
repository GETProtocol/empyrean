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
from empyrean.abi import decode_abi

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

    def test_encode_abi(self, multiple_of_eight):
        type = "uint{}".format(multiple_of_eight)
        assert tohex(encode_abi([type], [0])) == \
            b'0000000000000000000000000000000000000000000000000000000000000000'
        assert tohex(encode_abi([type], [1])) == \
            b'0000000000000000000000000000000000000000000000000000000000000001'
        assert tohex(encode_abi([type], [42])) == \
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

    def test_encode_abi(self, multiple_of_eight):
        type = "int{}".format(multiple_of_eight)
        assert tohex(encode_abi([type], [0])) == \
            b'0000000000000000000000000000000000000000000000000000000000000000'
        assert tohex(encode_abi([type], [1])) == \
            b'0000000000000000000000000000000000000000000000000000000000000001'
        assert tohex(encode_abi([type], [42])) == \
            b'000000000000000000000000000000000000000000000000000000000000002a'

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

    def test_enc(self, one_to_thirtytwo):
        t = ABIType("bytes{}".format(one_to_thirtytwo))
        assert tohex(t.enc(b'\x00')) == \
            b'0000000000000000000000000000000000000000000000000000000000000000'
        assert tohex(t.enc(b'\x01')) == \
            b'0100000000000000000000000000000000000000000000000000000000000000'
        assert tohex(t.enc(b'\xff')) == \
            b'ff00000000000000000000000000000000000000000000000000000000000000'
        assert tohex(t.enc(b'A')) == \
            b'4100000000000000000000000000000000000000000000000000000000000000'
        # assert tohex(t.enc(b'ABC')) == \
        #     b'4142430000000000000000000000000000000000000000000000000000000000'

    def test_encode_abi(self, one_to_thirtytwo):
        t = "bytes{}".format(one_to_thirtytwo)

        assert tohex(encode_abi([t], [b'\x00'])) == \
            b'0000000000000000000000000000000000000000000000000000000000000000'
        assert tohex(encode_abi([t], [b'\x01'])) == \
            b'0100000000000000000000000000000000000000000000000000000000000000'
        assert tohex(encode_abi([t], [b'\xff'])) == \
            b'ff00000000000000000000000000000000000000000000000000000000000000'
        assert tohex(encode_abi([t], [b'A'])) == \
            b'4100000000000000000000000000000000000000000000000000000000000000'

    def test_larger_than_32(self):
        t = ABIType("bytes{}".format(one_to_thirtytwo))
        with pytest.raises(ValueError):
            t.enc(b'A' * 33)

    def test_not_too_large(self, one_to_thirtytwo):
        t = ABIType("bytes{}".format(one_to_thirtytwo))
        t.enc(b'A' * one_to_thirtytwo)

    def test_too_large(self, one_to_thirtytwo):
        t = ABIType("bytes{}".format(one_to_thirtytwo))
        with pytest.raises(ValueError):
            t.enc(b'A' * (one_to_thirtytwo + 1))

    def test_bytes_is_not_dynamic(self, one_to_thirtytwo):
        assert not ABIType("bytes{}".format(one_to_thirtytwo)).isdynamic

    def test_bytes_is_dynamic(self):
        assert ABIType("bytes").isdynamic

    def test_enc_bytes(self):
        t = ABIType("bytes")
        assert tohex(t.enc(b'Hello World How Are you?'
                           b' 123456789012345678901234567890')) == (
            b"00000000000000000000000000000000"
            b"00000000000000000000000000000037"
            b"48656c6c6f20576f726c6420486f7720"
            b"41726520796f753f2031323334353637"
            b"38393031323334353637383930313233"
            b"34353637383930000000000000000000")

    def test_enc_bytes_encode_abi(self):
        res = encode_abi(["bytes"], [b'Hello World How Are you? '
                                     b'123456789012345678901234567890'])
        assert tohex(res) == (
            b"00000000000000000000000000000000"
            b"00000000000000000000000000000020"
            b"00000000000000000000000000000000"
            b"00000000000000000000000000000037"
            b"48656c6c6f20576f726c6420486f7720"
            b"41726520796f753f2031323334353637"
            b"38393031323334353637383930313233"
            b"34353637383930000000000000000000")


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

    def test_encode_abi(self):
        assert tohex(encode_abi(["bool"], [True])) == \
            b'0000000000000000000000000000000000000000000000000000000000000001'

        assert tohex(encode_abi(["bool"], [False])) == \
            b'0000000000000000000000000000000000000000000000000000000000000000'

    def test_bool_unsized_array_is_dynamic(self):
        assert ABIType("bool[]").isdynamic


class TestUFixedType:

    def test_fixed_size(self, multiple_of_eight):
        # wrong! m+n = 256! (so 256 itself isn't a usable multiple_of_eight)
        assert ABIType("fixed{0}x{0}".format(multiple_of_eight)).size() == 32

    def test_fixed_is_not_dynamic(self, multiple_of_eight):
        assert not ABIType("fixed{0}x{0}".format(multiple_of_eight)).isdynamic

    def test_fixed_unsized_array_is_dynamic(self, multiple_of_eight):
        assert ABIType("fixed{0}x{0}[]".format(multiple_of_eight)).isdynamic

    @pytest.mark.parametrize("size,expect",
                             [(i, i * 32) for i in (1, 2, 10, 20, 100)])
    def test_fixed_fixedarray_size2(self, multiple_of_eight, size, expect):
        t = "fixed{0}x{0}[{1}]".format(multiple_of_eight, size)
        assert ABIType(t).size() == expect

    def test_enc(self):
        t = ABIType("ufixed128x128")

        assert tohex(t.enc(1.1)) == \
            b"00000000000000000000000000000001199999999999a0000000000000000000"
        t = ABIType("ufixed64x64")

        assert tohex(t.enc(1.1)) == \
            b"000000000000000000000000000000000000000000000001199999999999a000"


class TestStringType:

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

    def test_multiple_dynamics(self):
        res = tohex(encode_abi(
            ["uint256[]", "uint256[]", "uint256[]"], [[1], [1, 2], [1, 2, 3]]))
        assert res == (
            b'0000000000000000000000000000000000000000000000000000000000000060'
            b'00000000000000000000000000000000000000000000000000000000000000a0'
            b'0000000000000000000000000000000000000000000000000000000000000100'
            b'0000000000000000000000000000000000000000000000000000000000000001'
            b'0000000000000000000000000000000000000000000000000000000000000001'
            b'0000000000000000000000000000000000000000000000000000000000000002'
            b'0000000000000000000000000000000000000000000000000000000000000001'
            b'0000000000000000000000000000000000000000000000000000000000000002'
            b'0000000000000000000000000000000000000000000000000000000000000003'
            b'0000000000000000000000000000000000000000000000000000000000000001'
            b'0000000000000000000000000000000000000000000000000000000000000002'
            b'0000000000000000000000000000000000000000000000000000000000000003'
        )

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


class TestABIDecode:

    def test_decode_single_uint256(self):
        data = \
            b'0000000000000000000000000000000000000000000000000000000000000003'
        assert decode_abi(["uint256"], data) == [3]

    def test_decode_single_uint256_max(self):
        data = \
            b'ffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff'
        assert decode_abi(["uint256"], data) == [2 ** 256 - 1]

    def test_decode_double_uint256(self):
        data = (
            b'0000000000000000000000000000000000000000000000000000000000000003'
            b'0000000000000000000000000000000000000000000000000000000000000020'
        )
        assert decode_abi(["uint256", "uint256"], data) == [3, 32]

    def test_decode_dynamic_uint256_dynamic_array(self):
        data = (
            b'0000000000000000000000000000000000000000000000000000000000000020'
            b'0000000000000000000000000000000000000000000000000000000000000003'
            b'000000000000000000000000000000000000000000000000000000000000001d'
            b'000000000000000000000000000000000000000000000000000000000000001f'
            b'0000000000000000000000000000000000000000000000000000000000000026')
        assert decode_abi(["uint256[]"], data) == [[29, 31, 38]]

    def test_decode_dynamic_uint256_static_array(self):
        data = (
            b'000000000000000000000000000000000000000000000000000000000000001d'
            b'000000000000000000000000000000000000000000000000000000000000001f'
            b'0000000000000000000000000000000000000000000000000000000000000026')
        assert decode_abi(["uint256[3]"], data) == [[29, 31, 38]]

    def test_decode_single_int256_minus_one(self):
        data = \
            b'ffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff'
        assert decode_abi(["int256"], data) == [-1]

    def test_decode_single_int256_plus_one(self):
        data = \
            b'0000000000000000000000000000000000000000000000000000000000000001'
        assert decode_abi(["int256"], data) == [1]

    def test_decode_single_int256_max_pos(self):
        data = \
            b"7fffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff"
        assert decode_abi(["int256"], data) == [2 ** 255 - 1]

    def test_decode_single_int256_max_neg(self):
        data = \
            b'8000000000000000000000000000000000000000000000000000000000000000'
        assert decode_abi(["int256"], data) == [- (2 ** 255)]

    def test_decode_int256_dynamic_array(self):
        data = (
            b'0000000000000000000000000000000000000000000000000000000000000020'
            b'0000000000000000000000000000000000000000000000000000000000000005'
            b'8000000000000000000000000000000000000000000000000000000000000000'
            b'fffffffffffffffffffffffffffffffffffffffffffffffffffffffffffe7961'
            b'ffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff'
            b'000000000000000000000000000000000000000000000000000000000001869f'
            b'7fffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff'
        )
        assert decode_abi(["int256[]"], data) == [
            [-2**255, -99999, -1, 99999, 2**255 - 1]]

    def test_decode_int256_static_array(self):
        pass
        data = (
            b'8000000000000000000000000000000000000000000000000000000000000000'
            b'fffffffffffffffffffffffffffffffffffffffffffffffffffffffffffe7961'
            b'ffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff'
            b'000000000000000000000000000000000000000000000000000000000001869f'
            b'7fffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff'
        )
        assert decode_abi(["int256[5]"], data) == [
            [-2**255, -99999, -1, 99999, 2**255 - 1]]

    def test_decode_bool_true(self):
        data = \
            b'0000000000000000000000000000000000000000000000000000000000000001'
        assert decode_abi(["bool"], data) == [True]

    def test_decode_bool_false(self):
        data = \
            b'0000000000000000000000000000000000000000000000000000000000000000'
        assert decode_abi(["bool"], data) == [False]

    def test_decode_bool_dynamic_array(self):
        data = (
            b'0000000000000000000000000000000000000000000000000000000000000020'
            b'0000000000000000000000000000000000000000000000000000000000000003'
            b'0000000000000000000000000000000000000000000000000000000000000001'
            b'0000000000000000000000000000000000000000000000000000000000000000'
            b'0000000000000000000000000000000000000000000000000000000000000001'
        )
        assert decode_abi(["bool[]"], data) == [[True, False, True]]

    def test_decode_bool_static_array(self):
        data = (
            b'0000000000000000000000000000000000000000000000000000000000000001'
            b'0000000000000000000000000000000000000000000000000000000000000000'
            b'0000000000000000000000000000000000000000000000000000000000000001'
        )
        assert decode_abi(["bool[3]"], data) == [[True, False, True]]

    # bytes

    def test_decode_bytes_10(self):
        data = b"48656c6c6f000000000000000000000000000000000000000000000000000000"
        assert decode_abi(["bytes10"], data) == [b"Hello"]

    def test_decode_bytes_dynamic(self):
        data = (
            b'0000000000000000000000000000000000000000000000000000000000000020'
            b'0000000000000000000000000000000000000000000000000000000000000005'
            b'48656c6c6f000000000000000000000000000000000000000000000000000000'
        )
        assert decode_abi(["bytes"], data) == [b"Hello"]

    def test_decode_bytes_dynamic_array(self):
        """ Not sure if bytes[] or even bytes[5] is supported at this moment """
        data = (
            b'0000000000000000000000000000000000000000000000000000000000000020'
            b'0000000000000000000000000000000000000000000000000000000000000005'
            b'48656c6c6f000000000000000000000000000000000000000000000000000000'
            b'576f726c64000000000000000000000000000000000000000000000000000000'
            b'486f770000000000000000000000000000000000000000000000000000000000'
            b'4172650000000000000000000000000000000000000000000000000000000000'
            b'596f750000000000000000000000000000000000000000000000000000000000'
        )
        assert decode_abi(["bytes32[]"], data) == [
            [b"Hello", b"World", b"How", b"Are", b"You"]]
    # misc

    def test_handle_wrong_signature(self):
        """ treating fixed array data as dynamic may give very strange results """
        data = (
            b'000000000000000000000000000000000000000000000000000000000000001d'
            b'000000000000000000000000000000000000000000000000000000000000001f'
            b'0000000000000000000000000000000000000000000000000000000000000026')
        with pytest.raises(ValueError):
            decode_abi(["uint256[]"], data)


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
