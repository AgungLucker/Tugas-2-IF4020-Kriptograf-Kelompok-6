from .state import State
from .sbox import SBox
from .permutation import Permutation
from .keyExpansion import KeyExpansion

class TENUN128Cipher:
    ROUND_COUNT = BLOCK_SIZE = KEY_SIZE = 16  #16 bytes

    def __init__(self, master_key: bytes):
        if len(master_key) != self.KEY_SIZE:
            raise ValueError(f"key must be {self.KEY_SIZE} bytes, got {len(master_key)} bytes")
        
        self.key_expansion = KeyExpansion(master_key)
        self.sbox = SBox()
        self.permutation = Permutation()

    def encrypt_block(self, plaintext: bytes):
        if len(plaintext) != self.BLOCK_SIZE:
            raise ValueError(f"plaintext block must be {self.BLOCK_SIZE} bytes, got {len(plaintext)} bytes")
        
        state = State(plaintext)
        round_keys = self.key_expansion.round_keys

        # 16 rounds
        for r in range(self.ROUND_COUNT):
            state = self.XOR_round_key(state, round_keys[r])
            state = self.sbox.substitute_state(state)
            state = self.permutation.permute_state(state)
            state = self.modulo_opr(state)
            state = self.rotate_opr(state, round_keys[r])

        state = self.XOR_round_key(state, round_keys[self.ROUND_COUNT])
        return state.data

    def decrypt_block(self, ciphertext: bytes):
        if len(ciphertext) != self.BLOCK_SIZE:
            raise ValueError(f"ciphertext block must be {self.BLOCK_SIZE} bytes, got {len(ciphertext)} bytes")
        
        state = State(ciphertext)
        round_keys = self.key_expansion.round_keys

        state = self.XOR_round_key(state, round_keys[self.ROUND_COUNT])

        # loop from idx 15 to 0 (16 rounds)
        for r in range(self.ROUND_COUNT - 1, -1, -1):
            state = self.inv_rotate_opr(state, round_keys[r])
            state = self.inv_modulo_opr(state)
            state = self.permutation.inverse_permute_state(state)
            state = self.sbox.inverse_substitute_state(state)
            state = self.XOR_round_key(state, round_keys[r])

        return state.data

    def XOR_round_key(self, state: State, round_key: bytes) -> State:
        return State(bytes(a ^ b for a, b in zip(state.data, round_key)))

    def modulo_opr(self, state: State) -> State:
        for col in range(4):
            a, b, c, d = state.get_column(col)
            a2 = (a + d) % 256
            b2 = (b + a2) % 256
            c2 = (c + b2) % 256
            d2 = (d + c2) % 256
            state = state.set_column(col, bytes([a2, b2, c2, d2]))

        return state

    def inv_modulo_opr(self, state: State) -> State:
        for col in range(4):
            a2, b2, c2, d2 = state.get_column(col)
            d = (d2 - c2) % 256
            c = (c2 - b2) % 256
            b = (b2 - a2) % 256
            a = (a2 - d) % 256
            state = state.set_column(col, bytes([a, b, c, d]))

        return state

    def rotate_opr(self, state: State, round_key: bytes) -> State:
        k = round_key[15] % 16

        for row in range(4):
            shift = (2*k + 1 + 8*row) % 32
            word = int.from_bytes(state.get_row(row), "big")
            rotated_word = ((word << shift) | (word >> (32 - shift))) & 0xFFFFFFFF
            state = state.set_row(row, rotated_word.to_bytes(4, "big"))

        return state

    def inv_rotate_opr(self, state: State, round_key: bytes) -> State:
        k = round_key[15] % 16

        for row in range(4):
            shift = (2*k + 1 + 8*row) % 32
            word = int.from_bytes(state.get_row(row), "big")
            rotated_word = ((word >> shift) | (word << (32 - shift))) & 0xFFFFFFFF
            state = state.set_row(row, rotated_word.to_bytes(4, "big"))

        return state
    


