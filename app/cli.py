import argparse
import base64
import binascii
from getpass import getpass
from pathlib import Path
import sys

from modes import MODES
from . import service


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="TENUN-128 — enkripsi teks dan berkas dengan lima mode.")
    commands = parser.add_subparsers(dest="command")
    commands.add_parser("tui", help="Buka antarmuka terminal Textual")
    for command in ("encrypt", "decrypt"):
        sub = commands.add_parser(command)
        source = sub.add_mutually_exclusive_group(required=True)
        source.add_argument("-i", "--input", type=Path, help="Berkas input biner")
        source.add_argument("--text", help="Teks UTF-8 untuk enkripsi / envelope Base64 untuk dekripsi")
        sub.add_argument("-o", "--output", type=Path, help="Berkas baru; wajib untuk input berkas")
        sub.add_argument("--key", help="Kunci; jika kosong diminta melalui prompt tersembunyi")
        sub.add_argument("--key-format", choices=("hex", "text"), default="hex")
        if command == "encrypt":
            sub.add_argument("--mode", choices=MODES, default="CBC")
            sub.add_argument("--iv", default="", help="IV/counter 32 digit hex; kosong = acak")
    args = parser.parse_args(argv)
    if args.command in (None, "tui"):
        from .tui import TenunApp
        TenunApp().run()
        return 0
    if args.input is not None and args.output is None:
        parser.error("Input berkas memerlukan --output.")
    try:
        key = service.parse_key(args.key if args.key is not None else getpass("Kunci 128-bit: "), args.key_format)
        if args.input is not None:
            data = args.input.expanduser().read_bytes()
        elif args.command == "encrypt":
            data = args.text.encode("utf-8")
        else:
            data = base64.b64decode("".join(args.text.split()), validate=True)
        if args.command == "encrypt":
            result = service.encrypt(data, key, args.mode, service.parse_iv(args.iv))
        else:
            result = service.decrypt(data, key)
        if args.output is not None:
            service.write_new(args.output, result)
            print(f"Berhasil: {len(result)} byte → {args.output}", file=sys.stderr)
        elif args.command == "encrypt":
            print(base64.b64encode(result).decode("ascii"))
        else:
            sys.stdout.buffer.write(result)
        return 0
    except (ValueError, OSError, binascii.Error, EOFError) as exc:
        print(f"Gagal: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
