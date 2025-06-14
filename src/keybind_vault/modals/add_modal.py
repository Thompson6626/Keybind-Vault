from textual.app import ComposeResult
from textual.containers import Grid
from textual.screen import ModalScreen
from textual.widgets import Button, Input, Label

from vault_types import Mode


class AddScreen(ModalScreen[tuple[str, str] | str]):
    CSS_PATH = "styles/add.tcss"

    def __init__(self, mode: Mode) -> None:
        super().__init__()
        self.mode = mode

    def compose(self) -> ComposeResult:
        is_category = self.mode == Mode.CATEGORY
        label_text = "Add category" if is_category else "Add keybind"
        children = [
            Label(label_text, id="label-help"),
            Input(
                placeholder="Name" if is_category else "Keys",
                id="input",
                disabled=False,
            ),
        ]

        if not is_category:
            children.append(
                Input(placeholder="Description", id="description", disabled=False)
            )

        children += [
            Button("Add", variant="primary", id="add"),
            Button("Cancel", id="cancel"),
        ]

        yield Grid(*children, id="add-dialog")

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
