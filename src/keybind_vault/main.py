import asyncio
from typing import Optional

from textual import on
from textual.app import App, ComposeResult
from textual.containers import Horizontal
from textual.coordinate import Coordinate
from textual.reactive import reactive
from textual.widgets import Header, Footer, DataTable, ListView, ListItem, Label

from add_modal import AddScreen
from db import (
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
from search_modal import SearchScreen
from delete_modal import DeleteScreen
from edit_modal import EditScreen
from vault_types import KeybindField
from vault_types import Mode


COLUMNS = ("Keys", "Description")


class KeybindVaultApp(App):
    """A Textual app to manage manage keybinds."""

    CSS_PATH = "styles/styles.tcss"

    # Keybinds to create, update ,delete on both the listview and datatable (perhaps merge both into 1)
    BINDINGS = [
        ("d", "toggle_dark", "Toggle dark mode"),
        ("s", "search", "Search"),  # By name, keys and/or descriptions
        ("tab", "toggle_focus", "Switch focus"),
        ("a", "add", "Add"),
        ("e", "edit", "Edit"),
        ("x", "delete", "Delete"),
    ]

    # Focus index: 0 = ListView, 1 = DataTable
    focused = reactive(0)

    def compose(self) -> ComposeResult:
        yield Header()
        yield Horizontal(
            ListView(id="categories"), DataTable(id="keybinds", zebra_stripes=True)
        )
        yield Footer()

    async def on_mount(self) -> None:
        categories = await get_categories()
        list_view = self.query_one(ListView)

        for category in categories:
            await list_view.append(
                ListItem(
                    Label(category.name, classes="category-item"),
                    id=f"id-{category.id}",
                )
            )

        table = self.query_one(DataTable)

        general_keybinds = await get_keybinds_by_category(1)
        table.add_columns(*COLUMNS)
        for keybind in general_keybinds:
            table.add_row(keybind.keys, keybind.description, key=str(keybind.id))

    def action_toggle_dark(self) -> None:
        """An action to toggle dark mode."""
        self.theme = (
            "textual-dark" if self.theme == "textual-light" else "textual-light"
        )

    @on(ListView.Highlighted)
    async def change_category(self):
        categories_list = self.query_one(ListView)
        category = categories_list.highlighted_child

        if category is None:
            return

        table = self.query_one(DataTable)
        table.clear()

        new_keybinds = await get_keybinds_by_category(int(category.id.split("-")[-1]))

        for keybind in new_keybinds:
            table.add_row(keybind.keys, keybind.description, key=str(keybind.id))

    def action_toggle_focus(self) -> None:
        """Toggle focus between the list view and the data table."""
        self.focused = 1 - self.focused
        if self.focused == 0:
            self.query_one(ListView).focus()
        else:
            self.query_one(DataTable).focus()

    def action_search(self):
        list_view = self.query_one(ListView)
        data_table = self.query_one(DataTable)
        focused = self.screen.focused

        highlighted_col = data_table.cursor_column

        async def search_cat(result: str | None) -> None:
            if not result:
                return

            matching_items = [
                item
                for item in list_view.children
                if item.query_one(Label).renderable.startswith(result)
            ]

            await list_view.clear()
            await list_view.extend(*matching_items)

        async def search_keyb(result: str | None) -> None:
            if not result:
                return

            # Determine which column is highlighted (selected by cursor)
            highlighted_col_index = data_table.cursor_column
            if highlighted_col_index is None:
                return

            # Build list of matching rows
            matching_rows = []
            for row_key in data_table.rows.keys():
                row = data_table.get_row(row_key)
                cell = row[highlighted_col_index]
                if (
                    result.lower() in str(cell.value).lower()
                ):  # case-insensitive contains
                    matching_rows.append((row_key, row))

            # Clear and repopulate table with only matching rows
            data_table.clear()

            for _, row in matching_rows:
                data_table.add_row(*[cell.value for cell in row])

        if focused == list_view:
            self.push_screen(SearchScreen(Mode.CATEGORY), search_cat)
        elif focused == data_table:
            self.push_screen(
                SearchScreen(
                    Mode.KEYBIND,
                    KeybindField.KEYS
                    if highlighted_col == 0
                    else KeybindField.DESCRIPTION,
                ),
                search_keyb,
            )

    def action_add(self) -> None:
        list_view = self.query_one(ListView)
        data_table = self.query_one(DataTable)
        focused = self.screen.focused

        async def add_cat(result: str | None) -> None:
            if result is None:
                return

            category: Category | None = await insert_category(result)
            if not category:
                return

            await list_view.append(
                ListItem(
                    Label(category.name, classes="category-item"),
                    id=f"id-{category.id}",
                )
            )

        async def add_keyb(result: tuple[str, str] | None) -> None:
            if result is None:
                return

            highlighted = list_view.highlighted_child
            if not highlighted:
                return  # Optional: feedback for no selected category

            category_id = int(highlighted.id.split("-")[-1])
            keybind: Optional[KeyBind] = await insert_keybind(
                result[0], result[1], category_id
            )
            if not keybind:
                return

            data_table.add_row(keybind.keys, keybind.description, key=str(keybind.id))

        if focused == list_view:
            self.push_screen(AddScreen(Mode.CATEGORY), add_cat)
        elif focused == data_table:
            self.push_screen(AddScreen(Mode.KEYBIND), add_keyb)

    def action_delete(self) -> None:
        list_view = self.query_one(ListView)
        data_table = self.query_one(DataTable)
        focused = self.screen.focused

        async def delete_cat(result: bool | None) -> None:
            if not result:
                return

            highlighted = list_view.highlighted_child

            category_id = int(highlighted.id.split("-")[-1])

            await delete_category(category_id)

            for i, list_item in enumerate(list_view.children):
                if list_item.id == highlighted.id:
                    await list_view.pop(i)
                    break

        async def delete_keyb(result: bool | None) -> None:
            if not result:
                return

            highlighted = list_view.highlighted_child
            if not highlighted:
                return

            category_id = int(highlighted.id.split("-")[-1])

            highlighted_row_index = data_table.cursor_row
            highlighted_row = None

            for i, row in enumerate(data_table.ordered_rows):
                if i == highlighted_row_index:
                    highlighted_row = row
                    break

            if not highlighted_row:
                return

            await delete_keybind(int(highlighted_row.key.value), category_id)
            data_table.remove_row(highlighted_row.key)

        if focused == list_view:
            highlighted = list_view.highlighted_child

            self.push_screen(DeleteScreen(Mode.CATEGORY), delete_cat)
        elif focused == data_table:
            self.push_screen(DeleteScreen(Mode.KEYBIND), delete_keyb)

    def action_edit(self):
        list_view = self.query_one(ListView)
        data_table = self.query_one(DataTable)
        focused = self.screen.focused

        async def edit_cat(result: str | None) -> None:
            if not result:
                return

            highlighted = list_view.highlighted_child

            if not highlighted:
                return

            category_id = int(highlighted.id.split("-")[-1])

            category_res = await update_category(result, category_id)

            label = highlighted.query_one(Label)
            label.update(category_res.name)

        async def edit_keyb(result: tuple[str, str] | None) -> None:
            if not result:
                return

            highlighted_cat = list_view.highlighted_child
            if not highlighted_cat:
                return

            category_id = int(highlighted_cat.id.split("-")[-1])

            row_index = data_table.cursor_row
            if row_index is None:
                return

            row = data_table.ordered_rows[row_index]

            keybind_id = int(row.key.value)

            updated_keybind = await update_keybind(
                keybind_id=keybind_id,
                keys=result[0],
                description=result[1],
                category_id=category_id,
            )

            if updated_keybind:
                data_table.remove_row(row.key)
                data_table.add_row(
                    updated_keybind.keys,
                    updated_keybind.description,
                    key=str(updated_keybind.id),
                )

            data_table.cursor_coordinate = Coordinate(row_index, 0)

        if focused == list_view:
            highlighted = list_view.highlighted_child

            self.push_screen(
                EditScreen(Mode.CATEGORY, highlighted.query_one(Label).renderable),
                edit_cat,
            )
        elif focused == data_table:
            row_index = data_table.cursor_row
            if row_index is None:
                return

            row = data_table.get_row_at(row_index)
            self.push_screen(EditScreen(Mode.KEYBIND, row[0], row[1]), edit_keyb)


if __name__ == "__main__":
    asyncio.run(initialize())
    app = KeybindVaultApp()
    app.run()
