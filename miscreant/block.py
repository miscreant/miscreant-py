"""block.py: A 128-bit block (i.e. for AES)"""

from struct import (pack, unpack)

from cryptography.hazmat.primitives.ciphers import Cipher
from typing import Optional, Union

from . import ct

# Size of an AES block in bytes
SIZE = 16

# Minimal irreducible polynomial for a 128-bit block size
R = 0x87

def _validate_bytes_or_bytearray(value):
    # type: (Union[bytearray, bytes]) -> bytearray
    if isinstance(value, bytes):
        value = bytearray(value)
    elif not isinstance(value, bytearray):
        raise TypeError("value must be bytes or bytearray")

    if len(value) != SIZE:
        raise ValueError("value must be 16-bytes")

    return value

class Block(object):
    """128-bit AES blocks"""

    def __init__(self, data=None):
        # type: (Union[bytearray, bytes, None]) -> None
        if data is None:
            self.data = bytearray(SIZE)
        else:
            self.data = _validate_bytes_or_bytearray(data)

    def clear(self):
        # type: () -> None
        """Reset the value of this block to all zeroes"""
        for i in range(SIZE):
            self.data[i] = 0

    def copy(self, other_block):
        # type: (Block) -> None
        """Copy the contents of another block into this block"""
        if not isinstance(other_block, Block):
            raise TypeError("can only copy from other Blocks")

        self.data[:] = other_block.data

    def clone(self):
        # type: () -> Block
        """Make another block with the same contents as this block"""
        other = Block()
        other.copy(self)
        return other

    def dbl(self):
        # type: () -> None
        """Double a value over GF(2^128):

        a<<1 if firstbit(a)=0
        (a<<1) xor (0**120)10000111 if firstbit(a)=1
        """

        overflow = 0
        words = unpack(b"!LLLL", self.data)
        output_words = []

        for word in reversed(words):
            new_word = (word << 1) & 0xFFFFFFFF
            new_word |= overflow
            overflow = int((word & 0x80000000) >= 0x80000000)
            output_words.append(new_word)

        self.data = bytearray(pack(b"!LLLL", *reversed(output_words)))
        self.data[-1] ^= ct.select(overflow, R, 0)

    def encrypt(self, cipher):
        # type: (Cipher) -> None
        """Encrypt this block in-place with the given cipher"""

        # TODO: more efficient in-place encryption options?
        encryptor = cipher.encryptor()
        self.data = bytearray(encryptor.update(bytes(self.data)) + encryptor.finalize())

    def xor_in_place(self, value):
        # type: (Union[Block, bytearray, bytes]) -> None
        """XOR the given data into the current block in-place"""

        if isinstance(value, Block):
            value = value.data
        else:
            value = _validate_bytes_or_bytearray(value)

        for i in range(SIZE):
            self.data[i] ^= value[i]
