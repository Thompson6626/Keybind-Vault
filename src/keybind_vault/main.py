import asyncio
from typing import Optional

from textual import on
from textual.app import App, ComposeResult
from textual.containers import Horizontal
from textual.coordinate import Coordinate
from textual.theme import Theme
from textual.widgets import Header, Footer, DataTable, ListView, ListItem, Label

from keybind_vault.db import (
    Category,
    KeyBind,
    get_categories,
    get_keybinds_by_category,
    insert_category,
    insert_keybind,
    initialize,
    delete_category,
    delete_keybind,
    update_category,
    update_keybind,
)

from keybind_vault.modals import (
    SearchScreen,
    EditScreen,
    DeleteScreen,
    AddScreen,
    KeybindField,
    Mode,
)


COLUMNS = ("Keys", "Description")


class KeybindVaultApp(App):
    """A Textual app to manage manage keybinds."""

    CSS_PATH = "styles/styles.tcss"

    # Keybinds to create, update ,delete on both the listview and datatable
    BINDINGS = [
        ("d", "toggle_dark", "Toggle dark mode"),
        ("s", "search", "Search"),  # By name, keys and/or descriptions
        ("a", "add", "Add"),
        ("e", "edit", "Edit"),
        ("x", "delete", "Delete"),
        ("g", "remove_filter", "Remove filter"),
    ]

    obsidian_night_theme = Theme(
        name="obsidian_night",
        primary="#61AFEF",  # Muted sky blue (links, highlights)
        secondary="#C678DD",  # Soft purple (secondary accents)
        accent="#98C379",  # Muted green (UI action highlights)
        foreground="#ABB2BF",  # Warm gray text
        background="#1E1E2E",  # Deep navy-charcoal background
        success="#98C379",  # Same muted green
        warning="#E5C07B",  # Soft gold (gentle but noticeable)
        error="#E06C75",  # Calm red (not overly aggressive)
        surface="#2A2E3E",  # Slightly elevated surface
        panel="#3B404C",  # Used for sidebars, panels
        dark=True,
        variables={
            "block-cursor-text-style": "reverse",
            "footer-key-foreground": "#61AFEF",
            "input-selection-background": "#61AFEF 25%",
        },
    )

    def compose(self) -> ComposeResult:
        self.list_view = ListView(id="categories")
        self.list_view.styles.opacity = 0

        self.data_table = DataTable(id="keybinds", zebra_stripes=True)
        self.data_table.styles.opacity = 0

        self.current_categories: dict[int, str] = {}
        self.current_keybinds: dict[str, tuple[str, str]] = {}

        yield Header(show_clock=True)
        yield Horizontal(self.list_view, self.data_table)
        yield Footer()

    async def on_mount(self) -> None:
        # Register the theme
        self.register_theme(self.obsidian_night_theme)

        categories = await get_categories()
        list_items = [
            ListItem(
                Label(category.name, classes="category-item"), id=f"id-{category.id}"
            )
            for category in categories
        ]
        self.current_categories = {
            category.id: category.name for category in categories
        }

        await self.list_view.extend(list_items)

        self.list_view.styles.animate(
            "opacity", value=1, duration=0.7, easing="in_out_quart"
        )

        general_keybinds = await get_keybinds_by_category(1)

        self.data_table.add_columns(*COLUMNS)

        for keybind in general_keybinds:
            key_id = str(keybind.id)
            self.current_keybinds[key_id] = (keybind.keys, keybind.description)
            self.data_table.add_row(keybind.keys, keybind.description, key=key_id)

        self.data_table.styles.animate(
            "opacity", value=1, duration=0.7, easing="in_out_quart"
        )

    def action_toggle_dark(self) -> None:
        """An action to toggle dark mode."""
        self.theme = (
            "textual-dark" if self.theme == "textual-light" else "textual-light"
        )

    @on(ListView.Highlighted)
    async def change_category(self):
        category = self.list_view.highlighted_child

        if category is None:
            return

        self.data_table.clear()
        self.data_table.styles.opacity = 0

        new_keybinds = await get_keybinds_by_category(int(category.id.split("-")[-1]))
        self.current_keybinds = {}

        for keybind in new_keybinds:
            key_str = str(keybind.id)
            self.current_keybinds[key_str] = (keybind.keys, keybind.description)
            self.data_table.add_row(
                keybind.keys, keybind.description, key=str(keybind.id)
            )

        self.data_table.styles.animate(
            "opacity", value=1, duration=0.5, easing="in_out_quart"
        )

    async def action_search(self):
        focused = self.screen.focused

        highlighted_col_index = self.data_table.cursor_column

        async def search_cat(result: str | None) -> None:
            if not result:
                await self.reset_displayed_categories()
                return

            await self.list_view.clear()

            # Re-making ListItems objects because reusing causes a display bug
            matching_items = [
                ListItem(Label(category, classes="category-item"), id=f"id-{id}")
                for id, category in self.current_categories.items()
                if category.startswith(result)
            ]

            await self.list_view.extend(matching_items)

        async def search_keyb(result: str | None) -> None:
            if not result:
                self.reset_displayed_keybinds()
                return

            if highlighted_col_index not in (0, 1):
                return

            self.data_table.clear()
            for keyb_key, keyb in self.current_keybinds.items():
                if result.lower() in keyb[highlighted_col_index].lower():
                    self.data_table.add_row(keyb[0], keyb[1], key=keyb_key)

        if focused == self.list_view:
            await self.push_screen(SearchScreen(Mode.CATEGORY), search_cat)
        elif focused == self.data_table:
            await self.push_screen(
                SearchScreen(
                    Mode.KEYBIND,
                    KeybindField.KEYS
                    if highlighted_col_index == 0
                    else KeybindField.DESCRIPTION,
                ),
                search_keyb,
            )

    async def action_remove_filter(self) -> None:
        await self.reset_displayed_categories()
        self.reset_displayed_keybinds()

    async def reset_displayed_categories(self) -> None:
        await self.list_view.clear()

        # Re-making ListItems objects because reusing causes a display bug
        items = [
            ListItem(Label(category, classes="category-item"), id=f"id-{id}")
            for id, category in self.current_categories.items()
        ]
        await self.list_view.extend(items)

    def reset_displayed_keybinds(self) -> None:
        self.data_table.clear()

        for keyb_key, keyb in self.current_keybinds.items():
            self.data_table.add_row(keyb[0], keyb[1], key=keyb_key)

    async def action_add(self) -> None:
        focused = self.screen.focused

        async def add_cat(result: str | None) -> None:
            if result is None:
                return

            category: Category | None = await insert_category(result)
            if not category:
                self.notify(
                    f"Category '{result}' could not be added. Please check for duplicates or try again.",
                    title="Add Category Failed",
                    severity="error",
                )
                return

            new_list_item = ListItem(
                Label(category.name, classes="category-item"),
                id=f"id-{category.id}",
            )
            new_list_item.styles.opacity = 0

            self.current_categories[category.id] = category.name

            await self.list_view.append(new_list_item)

            new_list_item.styles.animate(
                "opacity", value=1, duration=0.7, easing="in_out_quart"
            )

            self.notify(
                f"Category '{category.name}' was successfully added.",
                title="Category Added",
                severity="information",
            )

        async def add_keyb(result: tuple[str, str] | None) -> None:
            if result is None:
                return

            highlighted = self.list_view.highlighted_child
            if not highlighted:
                return

            category_id = int(highlighted.id.split("-")[-1])
            keybind: Optional[KeyBind] = await insert_keybind(
                result[0], result[1], category_id
            )
            if not keybind:
                self.notify(
                    "Failed to add keybind. Ensure it's not a duplicate.",
                    title="Add Keybind Failed",
                    severity="error",
                )
                return

            self.data_table.add_row(
                keybind.keys, keybind.description, key=str(keybind.id)
            )

            self.notify(
                f"Keybind '{keybind.keys}' was successfully added.",
                title="Keybind Added",
                severity="information",
            )

        if focused == self.list_view:
            await self.push_screen(AddScreen(Mode.CATEGORY), add_cat)
        elif focused == self.data_table:
            await self.push_screen(AddScreen(Mode.KEYBIND), add_keyb)

    async def action_delete(self) -> None:
        focused = self.screen.focused

        async def delete_cat(result: bool | None) -> None:
            if not result:
                return

            highlighted = self.list_view.highlighted_child

            category_id = int(highlighted.id.split("-")[-1])

            success = await delete_category(category_id)

            if not success:
                return

            self.current_categories.pop(category_id)

            async def delete():
                await highlighted.remove()

                self.notify(
                    "Category deleted successfully.",
                    title="Category Deleted",
                    severity="information",
                )

            highlighted.styles.animate(
                "opacity",
                value=0.0,
                duration=1,
                on_complete=delete,
                easing="in_out_quart",
            )

        async def delete_keyb(result: bool | None) -> None:
            if not result:
                return

            highlighted = self.list_view.highlighted_child
            if not highlighted:
                return

            category_id = int(highlighted.id.split("-")[-1])

            highlighted_row_index = self.data_table.cursor_row
            highlighted_row = None

            for i, row in enumerate(self.data_table.ordered_rows):
                if i == highlighted_row_index:
                    highlighted_row = row
                    break

            if not highlighted_row:
                return

            success = await delete_keybind(int(highlighted_row.key.value), category_id)

            if not success:
                return

            self.data_table.remove_row(highlighted_row.key)
            self.notify(
                "Keybind deleted successfully.",
                title="Keybind Deleted",
                severity="information",
            )

        if focused == self.list_view:
            await self.push_screen(DeleteScreen(Mode.CATEGORY), delete_cat)
        elif focused == self.data_table:
            await self.push_screen(DeleteScreen(Mode.KEYBIND), delete_keyb)

    async def action_edit(self):
        focused = self.screen.focused

        async def edit_cat(result: str | None) -> None:
            if not result:
                return

            highlighted = self.list_view.highlighted_child

            if not highlighted:
                return

            category_id = int(highlighted.id.split("-")[-1])

            category_res = await update_category(result, category_id)

            if category_res is None:
                return

            self.current_categories[category_id] = category_res.name

            label = highlighted.query_one(Label)
            label.styles.opacity = 0

            def update():
                label.update(category_res.name)

                self.notify(
                    f"Category renamed to '{category_res.name}'.",
                    title="Category Updated",
                    severity="information",
                )

            label.styles.animate(
                "opacity",
                value=1,
                duration=0.7,
                easing="in_out_quart",
                on_complete=update,
            )

        async def edit_keyb(result: tuple[str, str] | None) -> None:
            if not result:
                return

            highlighted_cat = self.list_view.highlighted_child
            if not highlighted_cat:
                return

            category_id = int(highlighted_cat.id.split("-")[-1])

            row_index = self.data_table.cursor_row
            if row_index is None:
                return

            row = self.data_table.ordered_rows[row_index]

            keybind_id = int(row.key.value)

            updated_keybind = await update_keybind(
                keybind_id=keybind_id,
                keys=result[0],
                description=result[1],
                category_id=category_id,
            )

            if updated_keybind:
                self.data_table.remove_row(row.key)
                self.data_table.add_row(
                    updated_keybind.keys,
                    updated_keybind.description,
                    key=str(updated_keybind.id),
                )
                self.notify(
                    f"Keybind '{updated_keybind.keys}' updated successfully.",
                    title="Keybind Updated",
                    severity="information",
                )
            else:
                self.notify(
                    "Failed to update keybind. Please try again.",
                    title="Update Failed",
                    severity="warning",
                )
                return

            self.data_table.cursor_coordinate = Coordinate(row_index, 0)

        if focused == self.list_view:
            highlighted = self.list_view.highlighted_child

            await self.push_screen(
                EditScreen(Mode.CATEGORY, highlighted.query_one(Label).renderable),
                edit_cat,
            )
        elif focused == self.data_table:
            row_index = self.data_table.cursor_row
            if row_index is None:
                return

            row = self.data_table.get_row_at(row_index)
            await self.push_screen(EditScreen(Mode.KEYBIND, row[0], row[1]), edit_keyb)


def main() -> None:
    asyncio.run(initialize())
    app = KeybindVaultApp()
    app.run()


if __name__ == "__main__":
    main()
