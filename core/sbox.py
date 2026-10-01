from .state import  State

class SBox:
    # Tabel sbox 1-D (map substitute key->value)
    SBOX = [0xA, 0x9, 0xB, 0x4, 0x5, 0xE, 0x3, 0xD, 0xC, 0xF, 0x6, 0x0, 0x7, 0x2, 0x1, 0x8]

    INV_SBOX = [0] * 16
    for i, j in enumerate(SBOX):
        INV_SBOX[j] = i

    def substitute_byte(self, b: int) -> int:
        hi, lo = State.single_byte_to_single_nibbles(b)
        return State.single_nibbles_to_single_byte(self.SBOX[hi], self.SBOX[lo])

    def inverse_substitute_byte(self, b: int) -> int:
        hi, lo = State.single_byte_to_single_nibbles(b)
        return State.single_nibbles_to_single_byte(self.INV_SBOX[hi], self.INV_SBOX[lo])

    def substitute_state(self, state: State) -> State:
        return State(bytes(self.substitute_byte(b) for b in state.data))


    def inverse_substitute_state(self, state: State) -> State:
        return State(bytes(self.inverse_substitute_byte(b) for b in state.data))
