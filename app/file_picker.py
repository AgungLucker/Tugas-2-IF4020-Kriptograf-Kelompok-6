from pathlib import Path

from textual import on
from textual.app import ComposeResult
from textual.containers import Horizontal, Vertical
from textual.screen import ModalScreen
from textual.widgets import Button, DirectoryTree, Input, Static


class FileTree(DirectoryTree):
    ICON_NODE_EXPANDED = ""
    ICON_NODE = ""
    ICON_FILE = ""


class FilePicker(ModalScreen[str | None]):
    BINDINGS = [("escape", "cancel", "Batal")]
    DEFAULT_CSS = """
    FilePicker { align: center middle; background: #000000 60%; }
    #picker-dialog { width: 90%; max-width: 100; height: 90%; max-height: 40;
        border: solid #ffc857; background: #111313; padding: 0 1; }
    #picker-title { height: 1; color: #ffc857; text-style: bold; }
    #picker-navigation { height: 3; }
    #picker-folder { width: 1fr; }
    #picker-up, #picker-home { width: auto; min-width: 5; height: 3; padding: 0 1; }
    #picker-tree { height: 1fr; min-height: 2; background: #111313; color: #e8e6de; }
    #picker-tree > .tree--guides { color: #555953; }
    #picker-tree > .tree--guides-selected { color: #ffc857; }
    #picker-tree > .tree--cursor, #picker-tree:focus > .tree--cursor { background: #ffc857; color: #111313; }
    #picker-name { height: 3; }
    #picker-selection { height: 1; color: #969a93; text-wrap: nowrap; text-overflow: ellipsis; }
    #picker-error { height: 1; color: #ff9285; text-wrap: nowrap; text-overflow: ellipsis; }
    #picker-actions { height: 3; align-horizontal: right; }
    #picker-cancel, #picker-confirm { width: auto; min-width: 10; height: 3; padding: 0 2; }
    #picker-confirm { background: #ffc857; color: #111313; text-style: bold; }
    """

    def __init__(self, folder: Path, *, save: bool = False, filename: str = "") -> None:
        super().__init__()
        self.folder = folder.expanduser().resolve()
        self.save = save
        self.filename = filename
        self.selected_file: Path | None = None

    def compose(self) -> ComposeResult:
        with Vertical(id="picker-dialog"):
            yield Static("Simpan hasil" if self.save else "Pilih berkas input", id="picker-title")
            with Horizontal(id="picker-navigation"):
                yield Button("Naik", id="picker-up", tooltip="Folder induk")
                yield Button("Home", id="picker-home")
                yield Input(str(self.folder), id="picker-folder", placeholder="Folder · Enter untuk membuka")
            yield FileTree(self.folder, id="picker-tree")
            name = Input(self.filename, placeholder="Nama berkas output", id="picker-name")
            name.display = self.save
            yield name
            yield Static(f"Folder: {self.folder}" if self.save else "Pilih berkas dari daftar.", id="picker-selection", markup=False)
            yield Static("", id="picker-error", markup=False)
            with Horizontal(id="picker-actions"):
                yield Button("Batal", id="picker-cancel")
                yield Button("Pilih lokasi" if self.save else "Pilih", id="picker-confirm", disabled=not self.save)

    def on_mount(self) -> None:
        self.query_one("#picker-tree").focus()

    def navigate(self, folder: Path) -> None:
        try:
            folder = folder.expanduser().resolve()
            if not folder.is_dir():
                raise ValueError("Folder tidak ditemukan.")
        except (OSError, RuntimeError, ValueError) as exc:
            self.query_one("#picker-error", Static).update(str(exc))
            return
        self.folder = folder
        self.selected_file = None
        self.query_one("#picker-folder", Input).value = str(folder)
        self.query_one("#picker-tree", DirectoryTree).path = folder
        self.query_one("#picker-confirm", Button).disabled = not self.save
        self.query_one("#picker-selection", Static).update(f"Folder: {folder}" if self.save else "Pilih berkas dari daftar.")
        self.query_one("#picker-error", Static).update("")

    @on(Input.Submitted, "#picker-folder")
    def open_folder(self, event: Input.Submitted) -> None:
        self.navigate(Path(event.value))

    @on(Button.Pressed, "#picker-up")
    def parent_folder(self) -> None:
        self.navigate(Path(self.query_one("#picker-folder", Input).value).parent)

    @on(Button.Pressed, "#picker-home")
    def home_folder(self) -> None:
        self.navigate(Path.home())

    @on(DirectoryTree.DirectorySelected, "#picker-tree")
    def select_folder(self, event: DirectoryTree.DirectorySelected) -> None:
        if self.save:
            self.folder = event.path
            self.query_one("#picker-selection", Static).update(f"Folder: {self.folder}")

    @on(DirectoryTree.FileSelected, "#picker-tree")
    def select_file(self, event: DirectoryTree.FileSelected) -> None:
        self.selected_file = event.path
        if self.save:
            self.folder = event.path.parent
            self.query_one("#picker-name", Input).value = event.path.name
            self.query_one("#picker-selection", Static).update(f"Folder: {self.folder}")
        else:
            self.query_one("#picker-selection", Static).update(str(event.path))
            self.query_one("#picker-confirm", Button).disabled = False

    @on(Button.Pressed, "#picker-confirm")
    @on(Input.Submitted, "#picker-name")
    def confirm(self) -> None:
        try:
            if self.save:
                name = self.query_one("#picker-name", Input).value.strip()
                if not name or name in (".", "..") or "/" in name or "\\" in name:
                    raise ValueError("Isi nama berkas tanpa path folder.")
                target = self.folder / name
                if target.exists():
                    raise ValueError("Berkas sudah ada. Pilih nama lain.")
            else:
                target = self.selected_file
                if target is None or not target.is_file():
                    raise ValueError("Pilih berkas yang tersedia.")
            self.dismiss(str(target))
        except (OSError, ValueError) as exc:
            self.query_one("#picker-error", Static).update(str(exc))

    @on(Button.Pressed, "#picker-cancel")
    def action_cancel(self) -> None:
        self.dismiss(None)
