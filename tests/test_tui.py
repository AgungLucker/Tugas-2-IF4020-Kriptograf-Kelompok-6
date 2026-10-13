import base64

import pytest
from textual.widgets import Button, Collapsible, Input, Select, Static, TabbedContent, TextArea

from app import service
from app.tui import TenunApp
from modes import MODES

KEY = bytes(range(16))


async def process(app, pilot):
    button = app.query_one("#process", Button)
    button.scroll_visible(animate=False)
    await pilot.pause()
    await pilot.click("#process")
    await app.workers.wait_for_complete()
    await pilot.pause()


@pytest.mark.parametrize("mode", MODES)
async def test_tui_text_roundtrip(mode):
    app = TenunApp()
    async with app.run_test(size=(110, 65)) as pilot:
        app.query_one("#key", TextArea).load_text(KEY.hex())
        app.query_one("#mode", Select).value = mode
        app.query_one("#text-input", TextArea).load_text("Halo Diky é\n")
        iv = app.query_one("#iv", TextArea).text
        await process(app, pilot)
        result = app.query_one("#result", TextArea).text
        metadata = service.inspect_verified(base64.b64decode(result), KEY)
        assert metadata.iv == (None if mode == "ECB" else bytes.fromhex(iv))
        assert service.decrypt(base64.b64decode(result), KEY) == "Halo Diky é\n".encode()
        await pilot.click("#reuse")
        await pilot.pause()
        assert app.query_one("#operation", Select).value == "decrypt"
        assert app.query_one("#iv", TextArea).read_only
        assert app.query_one("#iv", TextArea).text == ("" if mode == "ECB" else iv)
        assert app.query_one("#iv-section").display == (mode != "ECB")
        assert app.query_one("#mode", Select).value == mode
        await process(app, pilot)
        assert app.query_one("#result", TextArea).text == "Halo Diky é\n"
        assert app.query_one("#iv", TextArea).text == ("" if mode == "ECB" else iv)
        assert app.query_one("#iv-section").display == (mode != "ECB")
        assert not app.query_one("#random-iv").display


async def test_tui_file_small_terminal_and_wrong_key(tmp_path):
    source = tmp_path / "input.bin"
    output = tmp_path / "output.tenun"
    restored = tmp_path / "restored.bin"
    source.write_bytes(bytes(range(256)))
    app = TenunApp()
    async with app.run_test(size=(80, 24)) as pilot:
        app.query_one("#key", TextArea).load_text(KEY.hex())
        app.query_one("#source", TabbedContent).active = "file-tab"
        app.query_one("#input-path", Input).value = str(source)
        app.query_one("#output-path", Input).value = str(output)
        await process(app, pilot)
        assert output.exists()
        app.query_one("#operation", Select).value = "decrypt"
        app.query_one("#input-path", Input).value = str(output)
        app.query_one("#output-path", Input).value = str(restored)
        app.query_one("#key", TextArea).load_text(bytes(16).hex())
        await process(app, pilot)
        assert not restored.exists()
        assert "integritas gagal" in str(app.query_one("#status", Static).render())
        app.query_one("#key", TextArea).load_text(KEY.hex())
        await process(app, pilot)
        assert restored.read_bytes() == source.read_bytes()


async def test_tui_validation():
    app = TenunApp()
    async with app.run_test(size=(100, 65)) as pilot:
        await process(app, pilot)
        assert not app.query_one("#process", Button).disabled
        assert "Gagal" in str(app.query_one("#status", Static).render())


async def test_tui_advanced_options_and_text_output(tmp_path):
    output = tmp_path / "text.tenun"
    unused_file_output = tmp_path / "unused.tenun"
    app = TenunApp()
    async with app.run_test(size=(120, 40)) as pilot:
        advanced = app.query_one("#advanced", Collapsible)
        assert advanced.collapsed
        await pilot.click("#advanced > CollapsibleTitle")
        await pilot.pause()
        assert not advanced.collapsed
        app.query_one("#key-format", Select).value = "text"
        app.query_one("#key", TextArea).load_text("0123456789abcdef")
        app.query_one("#iv", TextArea).load_text(bytes(range(16)).hex())
        app.query_one("#text-output-path", Input).value = str(output)
        app.query_one("#output-path", Input).value = str(unused_file_output)
        app.query_one("#text-input", TextArea).load_text("Pesan uji")
        advanced.collapsed = True
        await process(app, pilot)
        envelope = output.read_bytes()
        key = b"0123456789abcdef"
        assert service.decrypt(envelope, key) == b"Pesan uji"
        assert service.inspect_verified(envelope, key).iv == bytes(range(16))
        assert not unused_file_output.exists()
        assert "16 byte" in str(app.query_one("#key-help", Static).render())
        assert app.query_one("#status").has_class("success")
        await pilot.click("#reuse")
        await pilot.pause()
        assert app.query_one("#text-output-path", Input).value == ""
        await process(app, pilot)
        assert app.query_one("#result", TextArea).text == "Pesan uji"


@pytest.mark.parametrize("size", [(120, 40), (80, 24), (50, 20)])
async def test_tui_layout_resize_and_file_fields(size):
    app = TenunApp()
    async with app.run_test(size=size) as pilot:
        assert app.screen.has_class("compact") == (size[0] < 90 or size[1] < 34)
        assert not app.query_one("#output-path", Input).is_on_screen
        app.query_one("#source", TabbedContent).active = "file-tab"
        await pilot.pause()
        output = app.query_one("#output-path", Input)
        output.scroll_visible(animate=False)
        await pilot.pause()
        assert output.is_on_screen
        assert output.region.bottom <= app.query_one("#source").region.bottom
        assert output.region.bottom <= app.query_one("#workspace").content_region.bottom
        await pilot.resize_terminal(120, 40)
        await pilot.pause()
        assert not app.screen.has_class("compact")
        assert app.query_one("#sidebar").region.right < app.query_one("#source").region.x


async def test_tui_key_length_tracks_edits_and_format():
    app = TenunApp()
    async with app.run_test(size=(120, 40)) as pilot:
        key = app.query_one("#key", TextArea)
        counter = app.query_one("#key-length", Static)
        assert "0 / 32" in str(counter.render())
        key.focus()
        await pilot.press("a", "b", "c", "d")
        assert "4 / 32" in str(counter.render())
        await pilot.press("backspace")
        assert "3 / 32" in str(counter.render())
        key.load_text("0001020304050607\n08090a0b0c0d0e0f")
        await pilot.pause()
        assert "32 / 32" in str(counter.render())
        await process(app, pilot)
        assert service.decrypt(base64.b64decode(app.query_one("#result", TextArea).text), KEY) == b""
        key.load_text("a" * 33)
        await pilot.pause()
        assert "33 / 32" in str(counter.render())
        app.query_one("#key-format", Select).value = "text"
        key.load_text("é" * 8)
        await pilot.pause()
        assert "16 / 16" in str(counter.render())
        key.load_text("é" * 7)
        await pilot.pause()
        assert "14 / 16" in str(counter.render())


async def test_tui_explicit_random_iv_and_repeated_encryption(monkeypatch):
    generated = iter([bytes(range(16)), bytes(range(16, 32))])
    monkeypatch.setattr("app.tui.secrets.token_bytes", lambda size: next(generated))
    app = TenunApp()
    async with app.run_test(size=(120, 40)) as pilot:
        iv = app.query_one("#iv", TextArea)
        initial = bytes(range(16)).hex()
        assert iv.text == initial
        assert "32 / 32" in str(app.query_one("#iv-length", Static).render())
        app.query_one("#key", TextArea).load_text(KEY.hex())
        app.query_one("#text-input", TextArea).load_text("Demo IV")
        await process(app, pilot)
        first = app.query_one("#result", TextArea).text
        await process(app, pilot)
        assert app.query_one("#result", TextArea).text == first
        assert iv.text == initial
        await pilot.click("#random-iv")
        await pilot.pause()
        assert iv.text == bytes(range(16, 32)).hex()
        await process(app, pilot)
        second = app.query_one("#result", TextArea).text
        assert second != first
        assert service.inspect_verified(base64.b64decode(second), KEY).iv == bytes(range(16, 32))
        app.query_one("#mode", Select).value = "ECB"
        await pilot.pause()
        assert not app.query_one("#iv-section").display
        app.query_one("#mode", Select).value = "CBC"
        await pilot.pause()
        assert iv.text == bytes(range(16, 32)).hex()
        iv.load_text("")
        await pilot.pause()
        assert "0 / 32" in str(app.query_one("#iv-length", Static).render())
        await process(app, pilot)
        assert "Acak baru" in str(app.query_one("#status", Static).render())


async def test_tui_decrypt_reads_verified_iv_and_restores_encryption_iv():
    app = TenunApp()
    envelope_iv = bytes(range(16))
    envelope = service.encrypt(b"Demo", KEY, "CTR", envelope_iv)
    async with app.run_test(size=(120, 40)) as pilot:
        original = app.query_one("#iv", TextArea).text
        app.query_one("#key", TextArea).load_text(KEY.hex())
        app.query_one("#mode", Select).value = "ECB"
        app.query_one("#operation", Select).value = "decrypt"
        app.query_one("#text-input", TextArea).load_text(base64.b64encode(envelope).decode())
        await pilot.pause()
        iv = app.query_one("#iv", TextArea)
        assert iv.read_only
        assert iv.text == ""
        assert app.query_one("#iv-section").display
        await process(app, pilot)
        assert iv.text == envelope_iv.hex()
        assert app.query_one("#mode", Select).value == "CTR"
        assert "32 / 32" in str(app.query_one("#iv-length", Static).render())

        app.query_one("#text-input", TextArea).load_text(base64.b64encode(envelope[:-1] + bytes([envelope[-1] ^ 1])).decode())
        await process(app, pilot)
        assert iv.text == ""
        assert "integritas gagal" in str(app.query_one("#status", Static).render())
        app.query_one("#operation", Select).value = "encrypt"
        await pilot.pause()
        assert not iv.read_only
        assert iv.text == original
        assert app.query_one("#random-iv").display


@pytest.mark.parametrize("key_format", ["hex", "text"])
async def test_tui_random_key_matches_format_and_roundtrips(key_format):
    app = TenunApp()
    async with app.run_test(size=(120, 40)) as pilot:
        app.query_one("#key-format", Select).value = key_format
        await pilot.pause()
        iv = app.query_one("#iv", TextArea).text
        await pilot.click("#random-key")
        await pilot.pause()
        value = app.query_one("#key", TextArea).text
        key = service.parse_key(value, key_format)
        assert len(key) == 16
        assert len(value) == (32 if key_format == "hex" else 16)
        assert f"{len(value)} / {len(value)}" in str(app.query_one("#key-length", Static).render())
        assert app.query_one("#iv", TextArea).text == iv
        app.query_one("#text-input", TextArea).load_text("Demo kunci acak")
        await process(app, pilot)
        assert app.query_one("#key", TextArea).text == value
        result = app.query_one("#result", TextArea).text
        assert service.decrypt(base64.b64decode(result), key) == b"Demo kunci acak"
        await pilot.click("#reuse")
        await pilot.pause()
        await process(app, pilot)
        assert app.query_one("#result", TextArea).text == "Demo kunci acak"


async def test_tui_reuse_uses_result_iv_after_configuration_changes():
    app = TenunApp()
    async with app.run_test(size=(120, 40)) as pilot:
        app.query_one("#key", TextArea).load_text(KEY.hex())
        await process(app, pilot)
        original_iv = app.query_one("#iv", TextArea).text
        new_iv = bytes(range(16)).hex()
        app.query_one("#iv", TextArea).load_text(new_iv)
        app.query_one("#mode", Select).value = "CTR"
        await pilot.pause()
        await pilot.click("#reuse")
        await pilot.pause()
        assert app.query_one("#iv", TextArea).text == original_iv
        assert app.query_one("#mode", Select).value == "CBC"
        app.query_one("#operation", Select).value = "encrypt"
        await pilot.pause()
        assert app.query_one("#iv", TextArea).text == new_iv


async def test_tui_copy_result_preserves_ciphertext_and_plaintext(monkeypatch):
    app = TenunApp()
    copied = []
    monkeypatch.setattr(app, "copy_to_clipboard", copied.append)
    async with app.run_test(size=(120, 40)) as pilot:
        button = app.query_one("#copy-result", Button)
        assert button.disabled
        app.query_one("#key", TextArea).load_text(KEY.hex())
        plaintext = "Demo salin é\nBaris kedua\n"
        app.query_one("#text-input", TextArea).load_text(plaintext)
        await process(app, pilot)
        ciphertext = app.query_one("#result", TextArea).text
        assert not button.disabled
        await pilot.click("#copy-result")
        await pilot.pause()
        assert copied == [ciphertext]
        assert service.decrypt(base64.b64decode(copied[0]), KEY) == plaintext.encode()
        await pilot.click("#reuse")
        await pilot.pause()
        await process(app, pilot)
        await pilot.click("#copy-result")
        await pilot.pause()
        assert copied == [ciphertext, plaintext]
