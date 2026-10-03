import base64
import binascii
import secrets
import string
from pathlib import Path

from textual import events, on, work
from textual.app import App, ComposeResult
from textual.containers import Horizontal, Vertical, VerticalScroll
from textual.widgets import Button, Collapsible, Footer, Input, Label, Select, Static, TabbedContent, TabPane, TextArea

from modes import MODES
from . import service
from .file_picker import FilePicker


class TenunApp(App):
    TITLE = "TENUN-128"
    ENABLE_COMMAND_PALETTE = False
    BINDINGS = [("ctrl+q", "quit", "Keluar"), ("ctrl+r", "process", "Proses")]
    CSS = """
    Screen { background: #111313; color: #e8e6de; }
    #topbar { height: 3; border: solid #555953; padding: 0 2; margin: 0 1; }
    #brand { width: 1fr; color: #ffc857; text-style: bold; }
    #workspace { height: 1fr; padding: 1; layout: horizontal; }
    #sidebar { width: 32; height: 1fr; border: solid #555953; padding: 0 1; margin-right: 1; }
    #main { width: 1fr; height: 1fr; }
    Label { color: #e8e6de; margin-top: 1; }
    Input, Select { background: #191c1b; color: #e8e6de; border: solid #555953; }
    Input:focus { border: solid #ffc857; }
    Select { border: none; height: 3; }
    Select > SelectCurrent { background: #191c1b; border: solid #555953; }
    Select:focus > SelectCurrent { border: solid #ffc857; }
    #key, #iv { height: 5; border: solid #555953; }
    #key:focus, #iv:focus { border: solid #ffc857; }
    #key-meta, #iv-meta { height: 1; color: #969a93; }
    #key-help, #iv-help { width: 1fr; height: 1; }
    #key-length, #iv-length { width: auto; height: 1; }
    #iv-section { height: auto; }
    #key-heading, #iv-heading { height: 1; margin-top: 1; }
    #key-label, #iv-label { width: 1fr; }
    #random-key, #random-iv { width: auto; min-width: 0; height: 1; padding: 0 1; color: #ffc857; }
    Collapsible { background: transparent; border: none; padding: 0; margin-top: 1; }
    Collapsible > CollapsibleTitle { color: #969a93; padding: 0; background: transparent; }
    Collapsible > CollapsibleTitle:focus { color: #ffc857; }
    Collapsible > Contents { padding: 0; }
    Button { background: #191c1b; color: #e8e6de; border: none; text-style: none; }
    Button:focus { text-style: bold; background: #353a34; }
    #process { height: 3; width: 1fr; margin-top: 1; background: #ffc857; color: #111313; text-style: bold; }
    #process:focus, #process:hover { background: #ffda88; }
    #source { height: 1fr; min-height: 10; border: solid #555953; padding: 0 1; }
    TabPane { padding: 0; }
    ContentSwitcher { height: 1fr; }
    Tabs { background: transparent; }
    Tab { color: #969a93; background: transparent; }
    Tab.-active { color: #ffc857; text-style: bold; background: transparent; }
    Underline > .underline--bar { color: #ffc857; background: transparent; }
    Underline > .underline--background { color: #555953; background: transparent; }
    #text-input { height: 1fr; min-height: 5; }
    TextArea { background: #111313; color: #e8e6de; border: none; }
    TextArea:focus { border: tall #ffc857; }
    #result-panel { height: 1fr; min-height: 10; border: solid #555953; padding: 0 1; margin-top: 1; }
    #result-heading { height: 3; align-vertical: middle; }
    #result-title { width: 1fr; text-style: bold; }
    #reuse, #copy-result { width: auto; min-width: 0; height: 3; padding: 0 1; color: #969a93; }
    #result { height: 1fr; }
    #status { display: none; height: auto; min-height: 1; margin-top: 1; color: #969a93; }
    #status.success { color: #a8d86e; }
    #status.error { color: #ff9285; }
    Footer { background: #191c1b; color: #e8e6de; }
    Footer > .footer--key { background: #191c1b; color: #ffc857; }
    .compact #workspace { layout: vertical; overflow-y: auto; }
    .compact #sidebar { width: 1fr; height: auto; margin-right: 0; margin-bottom: 1; }
    .compact #main { width: 1fr; height: auto; }
    #source.file-active { min-height: 16; }
    .file-heading { height: 1; margin-top: 1; }
    .file-heading Label { width: 1fr; margin-top: 0; }
    #browse-input, #browse-output { width: auto; min-width: 0; height: 1; padding: 0 1; color: #ffc857; }
    .compact #source { height: 13; }
    .compact #result-panel { height: 12; }
    """

    def __init__(self):
        super().__init__()
        self.theme = "textual-dark"
        self.last_output: bytes | None = None
        self.last_operation: str | None = None
        self.last_metadata: service.Metadata | None = None
        self.encryption_iv = secrets.token_bytes(16).hex()
        self.decryption_mode: str | None = None

    def compose(self) -> ComposeResult:
        with Horizontal(id="topbar"):
            yield Static("TENUN-128", id="brand")
        with VerticalScroll(id="workspace"):
            with VerticalScroll(id="sidebar"):
                yield Label("Operasi")
                yield Select([("Enkripsi", "encrypt"), ("Dekripsi", "decrypt")], value="encrypt", allow_blank=False, id="operation")
                yield Label("Mode")
                yield Select([(mode, mode) for mode in MODES], value="CBC", allow_blank=False, id="mode")
                with Horizontal(id="key-heading"):
                    yield Static("Kunci", id="key-label")
                    yield Button("Acak baru", id="random-key")
                yield TextArea(id="key")
                with Horizontal(id="key-meta"):
                    yield Static("Hex · 32 digit", id="key-help")
                    yield Static("0 / 32", id="key-length")
                with Vertical(id="iv-section"):
                    with Horizontal(id="iv-heading"):
                        yield Static("IV / counter", id="iv-label")
                        yield Button("Acak baru", id="random-iv")
                    yield TextArea(self.encryption_iv, id="iv")
                    with Horizontal(id="iv-meta"):
                        yield Static("Hex · 32 digit", id="iv-help")
                        yield Static("32 / 32", id="iv-length")
                with Collapsible(title="Opsi lanjutan", collapsed=True, id="advanced"):
                    yield Label("Format kunci")
                    yield Select([("Hex · 32 digit", "hex"), ("Teks · 16 byte UTF-8", "text")], value="hex", allow_blank=False, id="key-format")
                    yield Label("Simpan hasil teks (opsional)")
                    yield Input(placeholder="Path berkas baru", id="text-output-path")
                yield Button("Proses", variant="primary", id="process")
            with Vertical(id="main"):
                with TabbedContent(id="source"):
                    with TabPane("Teks", id="text-tab"):
                        yield TextArea(id="text-input")
                    with TabPane("Berkas", id="file-tab"):
                        with Horizontal(classes="file-heading"):
                            yield Label("Berkas input")
                            yield Button("Pilih berkas", id="browse-input")
                        yield Input(placeholder="Path berkas input", id="input-path")
                        with Horizontal(classes="file-heading"):
                            yield Label("Berkas output")
                            yield Button("Pilih lokasi", id="browse-output")
                        yield Input(placeholder="Path berkas baru", id="output-path")
                with Vertical(id="result-panel"):
                    with Horizontal(id="result-heading"):
                        yield Static("HASIL", id="result-title")
                        yield Button("Salin", id="copy-result", disabled=True)
                        yield Button("Pakai sebagai input", id="reuse", disabled=True)
                    yield TextArea(read_only=True, id="result")
                yield Static("", id="status", markup=False)
        yield Footer()

    def on_mount(self) -> None:
        self.query_one("#source").border_title = "INPUT"
        self.screen.set_class(self.size.width < 90 or self.size.height < 34, "compact")

    def on_resize(self, event: events.Resize) -> None:
        self.screen.set_class(event.size.width < 90 or event.size.height < 34, "compact")

    @on(TabbedContent.TabActivated, "#source")
    def update_source_layout(self) -> None:
        source = self.query_one("#source", TabbedContent)
        source.set_class(source.active == "file-tab", "file-active")

    @on(Button.Pressed, "#browse-input")
    @on(Button.Pressed, "#browse-output")
    def browse_file(self, event: Button.Pressed) -> None:
        save = event.button.id == "browse-output"
        target_id = "#output-path" if save else "#input-path"
        current = self.query_one(target_id, Input).value.strip()
        source = self.query_one("#input-path", Input).value.strip()
        path = Path(current or source or Path.cwd()).expanduser().resolve()
        folder = path if path.is_dir() else path.parent
        if not folder.is_dir():
            folder = Path.cwd()
        if current:
            filename = Path(current).name
        elif self.query_one("#operation", Select).value == "encrypt":
            filename = (Path(source).name if source else "hasil") + ".tenun"
        else:
            filename = (Path(source).name.removesuffix(".tenun") if source else "hasil") + ".restored"

        def selected(value: str | None) -> None:
            if value is not None:
                self.query_one(target_id, Input).value = value

        self.push_screen(FilePicker(folder, save=save, filename=filename), selected)

    @on(Select.Changed, "#key-format")
    @on(TextArea.Changed, "#key")
    def update_key_help(self) -> None:
        if self.is_mounted:
            value = self.query_one("#key", TextArea).text
            is_hex = self.query_one("#key-format", Select).value == "hex"
            length = len("".join(value.split())) if is_hex else len(value.encode("utf-8"))
            self.query_one("#key-help", Static).update("Hex · 32 digit" if is_hex else "Teks · 16 byte UTF-8")
            self.query_one("#key-length", Static).update(f"{length} / {32 if is_hex else 16}")

    def set_status(self, text: str, *, success: bool = False, error: bool = False) -> None:
        status = self.query_one("#status", Static)
        status.update(text)
        status.display = bool(text)
        status.set_class(success, "success")
        status.set_class(error, "error")
        if self.screen.has_class("compact") and (success or error):
            status.scroll_visible(animate=False)

    @on(TextArea.Changed, "#iv")
    def update_iv_length(self) -> None:
        iv = self.query_one("#iv", TextArea)
        self.query_one("#iv-length", Static).update(f"{len(''.join(iv.text.split()))} / 32")
        if not iv.read_only:
            self.encryption_iv = iv.text

    @on(Button.Pressed, "#random-iv")
    def randomize_iv(self) -> None:
        if self.query_one("#operation", Select).value == "encrypt":
            self.encryption_iv = secrets.token_bytes(16).hex()
            self.query_one("#iv", TextArea).load_text(self.encryption_iv)

    @on(Button.Pressed, "#random-key")
    def randomize_key(self) -> None:
        if self.query_one("#key-format", Select).value == "hex":
            value = secrets.token_bytes(16).hex()
        else:
            value = "".join(secrets.choice(string.ascii_letters + string.digits) for _ in range(16))
        self.query_one("#key", TextArea).load_text(value)

    @on(Select.Changed, "#operation")
    @on(Select.Changed, "#mode")
    def update_options(self, event: Select.Changed) -> None:
        if not self.is_mounted:
            return
        decrypting = self.query_one("#operation", Select).value == "decrypt"
        mode = self.query_one("#mode", Select).value
        iv = self.query_one("#iv", TextArea)
        self.query_one("#mode", Select).disabled = decrypting
        if event.select.id == "operation":
            if decrypting:
                if not iv.read_only:
                    self.encryption_iv = iv.text
                self.decryption_mode = None
            iv.read_only = decrypting
            iv.load_text("" if decrypting else self.encryption_iv)
            if (decrypting and self.last_operation == "encrypt" and self.last_output is not None
                    and self.last_metadata is not None
                    and self.query_one("#text-input", TextArea).text == base64.b64encode(self.last_output).decode("ascii")):
                self.display_envelope_metadata(self.last_metadata)
        self.query_one("#iv-section").display = (self.decryption_mode != "ECB") if decrypting else mode != "ECB"
        self.query_one("#random-iv").display = not decrypting
        self.query_one("#iv-help", Static).update("" if decrypting else "Hex · 32 digit")

    @on(Button.Pressed, "#process")
    def action_process(self) -> None:
        if self.query_one("#process", Button).disabled:
            return
        try:
            key = service.parse_key(self.query_one("#key", TextArea).text, str(self.query_one("#key-format", Select).value))
            operation = str(self.query_one("#operation", Select).value)
            mode = str(self.query_one("#mode", Select).value)
            iv = service.parse_iv(self.query_one("#iv", TextArea).text) if operation == "encrypt" and mode != "ECB" else None
            if operation == "encrypt" and mode != "ECB" and iv is None:
                raise ValueError("Isi IV/counter 32 digit hex atau tekan Acak baru.")
            is_file = self.query_one("#source", TabbedContent).active == "file-tab"
            source = self.query_one("#input-path", Input).value.strip() if is_file else self.query_one("#text-input", TextArea).text
            output_id = "#output-path" if is_file else "#text-output-path"
            output = self.query_one(output_id, Input).value.strip()
            if is_file and (not source or not output):
                raise ValueError("Masukkan path input dan output berkas.")
            self.last_output = None
            self.query_one("#result", TextArea).load_text("")
            self.query_one("#copy-result", Button).disabled = True
            self.query_one("#reuse", Button).disabled = True
            self.query_one("#process", Button).disabled = True
            self.set_status("Memproses…")
            self.process_data(key, operation, mode, iv, is_file, source, output)
        except ValueError as exc:
            self.set_status(f"Gagal: {exc}", error=True)

    @work(thread=True, exclusive=True)
    def process_data(self, key: bytes, operation: str, mode: str, iv: bytes | None, is_file: bool, source: str, output: str) -> None:
        try:
            metadata = None
            if is_file:
                data = Path(source).expanduser().read_bytes()
            elif operation == "encrypt":
                data = source.encode("utf-8")
            else:
                data = base64.b64decode("".join(source.split()), validate=True)
            if operation == "encrypt":
                result = service.encrypt(data, key, mode, iv)
                metadata = service.inspect_verified(result, key)
            else:
                metadata = service.inspect_verified(data, key)
                result = service.decrypt(data, key)
            if output:
                service.write_new(output, result)
            if is_file:
                preview = f"Hasil tersimpan di {output}\n{len(result)} byte."
            elif operation == "encrypt":
                preview = base64.b64encode(result).decode("ascii")
            else:
                try:
                    preview = result.decode("utf-8")
                except UnicodeDecodeError:
                    preview = "[Biner · Base64]\n" + base64.b64encode(result).decode("ascii")
            self.call_from_thread(self.show_result, result if not is_file else None, operation, preview, metadata)
        except (ValueError, OSError, binascii.Error) as exc:
            self.call_from_thread(self.show_error, str(exc))

    def show_result(self, result: bytes | None, operation: str, preview: str, metadata: service.Metadata | None = None) -> None:
        self.last_output = result
        self.last_operation = operation
        self.last_metadata = metadata
        self.query_one("#result", TextArea).load_text(preview)
        self.query_one("#copy-result", Button).disabled = not bool(preview)
        if operation == "decrypt" and metadata is not None:
            self.display_envelope_metadata(metadata)
        self.set_status("Enkripsi selesai." if operation == "encrypt" else "Dekripsi selesai.", success=True)
        self.query_one("#process", Button).disabled = False
        self.query_one("#reuse", Button).disabled = result is None

    def display_envelope_metadata(self, metadata: service.Metadata) -> None:
        self.decryption_mode = metadata.mode
        self.query_one("#mode", Select).value = metadata.mode
        iv = self.query_one("#iv", TextArea)
        iv.read_only = True
        iv.load_text(metadata.iv.hex() if metadata.iv is not None else "")
        self.query_one("#iv-section").display = metadata.iv is not None

    def show_error(self, message: str) -> None:
        if self.query_one("#operation", Select).value == "decrypt":
            self.decryption_mode = None
            self.query_one("#iv", TextArea).load_text("")
            self.query_one("#iv-section").display = True
        self.set_status(f"Gagal: {message}", error=True)
        self.query_one("#process", Button).disabled = False

    @on(Button.Pressed, "#copy-result")
    def copy_result(self) -> None:
        text = self.query_one("#result", TextArea).text
        if text:
            self.copy_to_clipboard(text)
            self.notify("Hasil disalin.")

    @on(Button.Pressed, "#reuse")
    def reuse_result(self) -> None:
        if self.last_output is None:
            return
        if self.last_operation == "encrypt":
            text = base64.b64encode(self.last_output).decode("ascii")
            self.query_one("#operation", Select).value = "decrypt"
        else:
            try:
                text = self.last_output.decode("utf-8")
            except UnicodeDecodeError:
                self.set_status("Hasil biner: gunakan tab Berkas.", error=True)
                return
            self.query_one("#operation", Select).value = "encrypt"
        self.query_one("#text-input", TextArea).load_text(text)
        if self.last_operation == "encrypt" and self.last_metadata is not None:
            self.display_envelope_metadata(self.last_metadata)
        self.query_one("#source", TabbedContent).active = "text-tab"
        self.query_one("#text-output-path", Input).value = ""
        self.set_status("Hasil dipindahkan ke input.")
