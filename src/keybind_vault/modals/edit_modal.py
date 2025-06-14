from textual.app import ComposeResult
from textual.containers import Grid
from textual.screen import ModalScreen
from textual.widgets import Label, Input, Button

from vault_types import Mode


class EditScreen(ModalScreen[str | tuple[str, str]]):
    CSS_PATH = "styles/edit.tcss"

    def __init__(self, mode: Mode, first: str, second: str = None) -> None:
        super().__init__()
        self.mode = mode
        self.first = first
        self.second = second

    def compose(self) -> ComposeResult:
        is_category = self.mode == Mode.CATEGORY
        label_text = f"Edit {self.mode.value}"
        children = [
            Label(label_text, id="hint"),
            Input(self.first, id="input", disabled=False),
        ]

        if not is_category:
            children.append(Input(self.second, id="description", disabled=False))

        children += [
            Button("Confirm", variant="primary", id="confirm"),
            Button("Cancel", id="cancel"),
        ]

        yield Grid(*children, id="edit-dialog")

    def on_mount(self) -> None:
        # 12 17
        self.query_one("#dialog").styles.height = (
            12 if self.mode == Mode.CATEGORY else 17
        )

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "cancel":
            self.dismiss(None)
        else:
            input = self.query_one("#input", Input)

            if self.mode == Mode.CATEGORY:
                self.dismiss(input.value)
            else:
                description = self.query_one("#description", Input)
                self.dismiss((input.value, description.value))
