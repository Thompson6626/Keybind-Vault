from textual.app import ComposeResult
from textual.containers import Grid
from textual.screen import ModalScreen
from textual.widgets import Label, Button

from vault_types import Mode


class DeleteScreen(ModalScreen[bool]):
    CSS_PATH = "styles/delete.tcss"

    def __init__(self, mode: Mode) -> None:
        super().__init__()
        self.mode = mode

    def compose(self) -> ComposeResult:
        yield Grid(
            Label(
                f"Are you sure you want to delete this {'category' if self.mode == Mode.CATEGORY else 'keybind'}?",
                id="question",
            ),
            Button("Delete", variant="error", id="quit"),
            Button("Cancel", variant="primary", id="cancel"),
            id="dialog",
        )

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "cancel":
            self.dismiss(False)
        else:
            self.dismiss(True)
