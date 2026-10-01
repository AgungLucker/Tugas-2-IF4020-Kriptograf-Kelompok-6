from .state import State

class Permutation:
    NIBBLE_LEN = 32
    PBOX = [(9 * i + 5) % 32 for i in range(NIBBLE_LEN)]

    INV_PBOX = [0] * NIBBLE_LEN
    for i, j in enumerate(PBOX):
        INV_PBOX[j] = i

    def permute_state(self, state: State) -> State:
        nibbles = state.multi_bytes_to_multi_nibbles()
        permuted_nibbles = [0] * len(nibbles)

        for i, j in enumerate(self.PBOX):
            permuted_nibbles[j] = nibbles[i]

        return State.multi_nibbles_to_multi_bytes(permuted_nibbles)

    def inverse_permute_state(self, state: State) -> State:
        permuted_nibbles = state.multi_bytes_to_multi_nibbles()
        original_nibbles = [0] * len(permuted_nibbles)

        for j, i in enumerate(self.INV_PBOX):
            original_nibbles[i] = permuted_nibbles[j]

        return State.multi_nibbles_to_multi_bytes(original_nibbles)

