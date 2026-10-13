from pathlib import Path

import pytest
from textual.widgets import DirectoryTree, Input, Static, TabbedContent, TextArea

from app import service
from app.file_picker import FilePicker
from app.tui import TenunApp
from test_tui import KEY, process


async def test_file_picker_selects_input_and_output_then_encrypts(tmp_path):
    source = tmp_path / "pesan demo é.txt"
    source.write_bytes(b"Demo file picker")
    destination = tmp_path / "hasil"
    destination.mkdir()
    app = TenunApp()
    async with app.run_test(size=(100, 40)) as pilot:
        app.query_one("#key", TextArea).load_text(KEY.hex())
        app.query_one("#source", TabbedContent).active = "file-tab"
        app.query_one("#input-path", Input).value = str(source)
        await pilot.pause()
        await pilot.click("#browse-input")
        await pilot.pause()
        assert isinstance(app.screen, FilePicker)
        tree = app.screen.query_one("#picker-tree", DirectoryTree)
        await tree.reload()
        node = next(node for node in tree.root.children if node.data.path == source)
        tree.select_node(node)
        await pilot.pause()
        await pilot.click("#picker-confirm")
        await pilot.pause()
        assert app.query_one("#input-path", Input).value == str(source)
        await pilot.click("#browse-output")
        await pilot.pause()
        assert app.screen.query_one("#picker-name", Input).value == source.name + ".tenun"
        tree = app.screen.query_one("#picker-tree", DirectoryTree)
        await tree.reload()
        node = next(node for node in tree.root.children if node.data.path == destination)
        tree.select_node(node)
        await pilot.pause()
        app.screen.query_one("#picker-name", Input).value = "hasil.tenun"
        await pilot.click("#picker-confirm")
        await pilot.pause()
        output = destination / "hasil.tenun"
        assert app.query_one("#output-path", Input).value == str(output)
        assert not output.exists()
        await process(app, pilot)
        assert service.decrypt(output.read_bytes(), KEY) == source.read_bytes()


@pytest.mark.parametrize("size", [(100, 40), (50, 20)])
async def test_file_picker_cancel_navigation_and_overwrite_guard(tmp_path, size):
    existing = tmp_path / "existing.bin"
    existing.write_bytes(b"Keep me")
    app = TenunApp()
    async with app.run_test(size=size) as pilot:
        results = []
        app.push_screen(FilePicker(tmp_path, save=True, filename=existing.name), results.append)
        await pilot.pause()
        await pilot.click("#picker-confirm")
        await pilot.pause()
        assert isinstance(app.screen, FilePicker)
        assert "sudah ada" in str(app.screen.query_one("#picker-error", Static).render())
        assert existing.read_bytes() == b"Keep me"
        app.screen.query_one("#picker-name", Input).value = "../outside.bin"
        app.screen.query_one("#picker-name", Input).focus()
        await pilot.press("enter")
        await pilot.pause()
        assert "tanpa path" in str(app.screen.query_one("#picker-error", Static).render())
        app.screen.query_one("#picker-folder", Input).value = str(tmp_path / "missing")
        app.screen.query_one("#picker-folder", Input).focus()
        await pilot.press("enter")
        assert "tidak ditemukan" in str(app.screen.query_one("#picker-error", Static).render())
        app.screen.query_one("#picker-folder", Input).value = str(tmp_path)
        await pilot.click("#picker-up")
        await pilot.pause()
        assert Path(app.screen.query_one("#picker-folder", Input).value) == tmp_path.parent
        await pilot.press("escape")
        await pilot.pause()
        assert results == [None]


async def test_file_picker_cancel_keeps_paths_and_suggests_decrypt_name(tmp_path):
    app = TenunApp()
    async with app.run_test(size=(100, 40)) as pilot:
        app.query_one("#source", TabbedContent).active = "file-tab"
        source = str(tmp_path / "pesan.txt.tenun")
        app.query_one("#input-path", Input).value = source
        app.query_one("#operation").value = "decrypt"
        await pilot.pause()
        await pilot.click("#browse-output")
        await pilot.pause()
        assert app.screen.query_one("#picker-name", Input).value == "pesan.txt.restored"
        await pilot.click("#picker-cancel")
        await pilot.pause()
        assert app.query_one("#output-path", Input).value == ""
        assert app.query_one("#input-path", Input).value == source
