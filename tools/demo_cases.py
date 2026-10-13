import argparse
import json
from pathlib import Path

from app import service
from modes import MODES

KEY = bytes(range(16))
IV = bytes(range(16, 32))


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True, help="Direktori hasil baru")
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=False)
    samples = {"text.txt": "TENUN-128 — Halo Diky!\nBaris kedua.\n".encode("utf-8"), "binary.bin": bytes(range(256)) + b"\x00\xff\x00"}
    report = []
    for name, plaintext in samples.items():
        service.write_new(args.output / name, plaintext)
        for mode in MODES:
            envelope = service.encrypt(plaintext, KEY, mode, None if mode == "ECB" else IV)
            ciphertext_path = args.output / f"{name}.{mode.lower()}.tenun"
            restored_path = args.output / f"{name}.{mode.lower()}.restored"
            service.write_new(ciphertext_path, envelope)
            service.decrypt_file(ciphertext_path, restored_path, KEY)
            roundtrip = restored_path.read_bytes() == plaintext
            tampered = bytearray(envelope)
            tampered[-1] ^= 1
            try:
                service.decrypt(bytes(tampered), KEY)
                tampering_rejected = False
            except service.IntegrityError:
                tampering_rejected = True
            report.append({"input": name, "mode": mode, "plaintext_bytes": len(plaintext), "envelope_bytes": len(envelope), "roundtrip_equal": roundtrip, "tampering_rejected": tampering_rejected})
    output = {"purpose": "Correctness/integrity demo; fixed public test key and IV, not security analysis", "key_hex": KEY.hex(), "iv_hex": IV.hex(), "cases": report}
    service.write_new(args.output / "results.json", (json.dumps(output, indent=2) + "\n").encode())
    if not all(case["roundtrip_equal"] and case["tampering_rejected"] for case in report):
        raise SystemExit("Demo verification failed")
    print(f"{len(report)} kasus berhasil → {args.output / 'results.json'}")


if __name__ == "__main__":
    main()
