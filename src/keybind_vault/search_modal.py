from textual.app import ComposeResult
from textual.containers import Grid
from textual.screen import ModalScreen
from textual.widgets import Label, Input, Button

from blank_validator import Blank
from vault_types import Mode, KeybindField


class SearchScreen(ModalScreen[str]):
    CSS_PATH = "styles/search.tcss"

    def __init__(self, mode: Mode, keybind_field: KeybindField = None):
        super().__init__()
        self.mode = mode
        self.keybind_field = keybind_field

    def compose(self) -> ComposeResult:
        if self.keybind_field is None:
            text = f"Search {self.mode.value} by name"
        else:
            text = f"Search {self.mode.value} by {self.keybind_field.value}"

        yield Grid(
            Label(text, id="hint"),
            Input(placeholder="Search...", id="input", validators=[Blank()]),
            Button("Search", variant="primary", id="quit"),
            Button("Cancel", id="cancel"),
            id="dialog",
        )

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "cancel":
            self.dismiss(None)
        else:
            input = self.query_one(Input)
            self.dismiss(input.value)
