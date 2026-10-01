class KeyExpansion:
    # 16 round + 1 whitening
    ROUND_COUNT = 17
    KEY_LEN = 16
    CONSTANT = 0x9E3779B9

    def __init__(self, key: bytes):
        self.key = key
        self.round_keys = self.generate_round_keys()

    def generate_round_keys(self):
        b = bytearray(self.key)
        round_keys = []
        for r in range(1, self.ROUND_COUNT + 1):
            constant_r = (r * self.CONSTANT) % (2**32)
            constant_r_bytes = constant_r.to_bytes(4, "big")

            # XOR first 4 bytes
            for i in range(4):
                b[i] ^= constant_r_bytes[i]

            # Proses diulang 2 kali
            for _ in range(2):
                for i in range(self.KEY_LEN):
                    val = (b[i] + b[i-1]) % 256
                    rotated_byte = ((val << 3) | (val >> 5)) & 0xFF
                    b[i] = rotated_byte ^ b[(i+5) % self.KEY_LEN]

            round_keys.append(bytes(b))

        return round_keys

            
