# matrix 4z4 bytes
class State:
    STATE_LEN = 16

    def __init__(self, data: bytes):
        self.data = data

    @staticmethod
    def single_byte_to_single_nibbles(b: int) -> list[int]:
        return [b >> 4, b & 0xF]

    @staticmethod
    def single_nibbles_to_single_byte(hi: int, lo: int) -> int:
        return (hi << 4) | lo

    def multi_bytes_to_multi_nibbles(self) -> list[int]:
        nibbles = []
        for b in self.data:
            hi, lo = State.single_byte_to_single_nibbles(b)
            nibbles.append(hi)
            nibbles.append(lo)
        return nibbles

    @classmethod
    def multi_nibbles_to_multi_bytes(cls, nibbles: list[int]) -> "State":
        out = bytearray(cls.STATE_LEN)
        for p in range(cls.STATE_LEN):
            out[p] = cls.single_nibbles_to_single_byte(nibbles[2 * p], nibbles[2 * p + 1])
        return cls(bytes(out))

    def get_row(self, row: int) -> bytes:
        return self.data[4 * row : 4 * row + 4]

    def set_row(self, row: int, row_bytes: bytes) -> "State":
        out = bytearray(self.data)
        out[4 * row : 4 * row + 4] = row_bytes
        return State(bytes(out))

    def get_column(self, col: int) -> bytes:
        return self.data[col::4]

    def set_column(self, col: int, col_bytes: bytes) -> "State":
        out = bytearray(self.data)
        out[col::4] = col_bytes
        return State(bytes(out))