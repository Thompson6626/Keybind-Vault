import sqlite3
from contextlib import closing
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

APP_NAME = "keybind_vault"
CONFIG_DIR = Path.home() / ".config" / APP_NAME
CONFIG_DIR.mkdir(parents=True, exist_ok=True)
DB_PATH = CONFIG_DIR / "keybindings.db"


@dataclass
class KeyBind:
    id: int
    keys: str
    description: str
    category_id: Optional[int]


@dataclass
class Category:
    id: int
    name: str


CategoryId = int
KeybindId = int
# In-memory cache
_keybinds_cache: dict[CategoryId, dict[KeybindId, KeyBind]] = {}


def _connect():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row  # Optional, for named columns
    conn.execute("PRAGMA foreign_keys = ON;")
    return conn


async def initialize() -> None:
    with closing(_connect()) as conn:
        cursor = conn.cursor()

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS category (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT UNIQUE NOT NULL
            );
        """)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS keybinds (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                keys TEXT NOT NULL,
                description TEXT,
                category_id INTEGER,
                FOREIGN KEY (category_id) REFERENCES category (id) ON DELETE CASCADE
            );
        """)

        cursor.execute("INSERT OR IGNORE INTO category (name) VALUES (?)", ("General",))
        conn.commit()


async def get_categories() -> list[Category]:
    with closing(_connect()) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM category")
        rows = cursor.fetchall()

        return [Category(**dict(row)) for row in rows]


async def get_keybinds_by_category(category_id: int = 1) -> list[KeyBind]:
    if category_id in _keybinds_cache:
        return list(_keybinds_cache[category_id].values())

    with closing(_connect()) as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT * 
            FROM keybinds
            WHERE category_id = ?
        """,
            (category_id,),
        )
        rows = cursor.fetchall()

        results = {int(row["id"]): KeyBind(**dict(row)) for row in rows}

        _keybinds_cache[category_id] = results
        return list(results.values())


async def update_keybind(
    keybind_id: int,
    keys: Optional[str],
    description: Optional[str],
    category_id: Optional[int],
) -> Optional[KeyBind]:
    try:
        with closing(_connect()) as conn:
            cursor = conn.cursor()

            fields = []
            values = []

            if keys is not None:
                fields.append("keys = ?")
                values.append(keys)
            if description is not None:
                fields.append("description = ?")
                values.append(description)
            if category_id is not None:
                fields.append("category_id = ?")
                values.append(category_id)

            if not fields:
                # Nothing to update
                return None

            values.append(keybind_id)
            sql = f"""
                UPDATE keybinds
                SET {", ".join(fields)}
                WHERE id = ?
            """
            cursor.execute(sql, tuple(values))
            conn.commit()

            cursor.execute("SELECT * FROM keybinds WHERE id = ?", (keybind_id,))
            row = cursor.fetchone()
            if row:
                result = KeyBind(**dict(row))
                # Use original category_id if not updated
                cache_category_id = (
                    category_id if category_id is not None else result.category_id
                )
                _keybinds_cache[cache_category_id][keybind_id] = result
                return result
    except sqlite3.IntegrityError as e:
        print(f"Update error (keybind): {e}")
    return None


async def insert_keybind(
    keys: str, description: str, category_id: int
) -> Optional[KeyBind]:
    try:
        with closing(_connect()) as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT INTO keybinds (keys, description, category_id)
                VALUES (?, ?, ?)
                RETURNING id, keys, description, category_id
            """,
                (keys, description, category_id),
            )
            row = cursor.fetchone()
            conn.commit()
            if row:
                result = KeyBind(**dict(row))
                _keybinds_cache[category_id][int(row["id"])] = result
                return result
    except sqlite3.IntegrityError as e:
        print(f"Insert error (keybind): {e}")
    return None


async def delete_keybind(keybind_id: int, category_id: int) -> bool:
    try:
        with closing(_connect()) as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM keybinds WHERE id = ?", (keybind_id,))
            conn.commit()

        _keybinds_cache[category_id].pop(keybind_id, None)
        return True
    except sqlite3.IntegrityError as e:
        print(f"Delete error (keybind): {e}")
    return False


async def insert_category(name: str) -> Optional[Category]:
    try:
        with closing(_connect()) as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT INTO category (name)
                VALUES (?)
                RETURNING *
            """,
                (name,),
            )
            row = cursor.fetchone()
            conn.commit()
            if row:
                return Category(**dict(row))
    except sqlite3.IntegrityError as e:
        print(f"Insert error (category): {e}")
    return None


async def update_category(name: str, cat_id: int) -> Optional[Category]:
    try:
        with closing(_connect()) as conn:
            cursor = conn.cursor()
            cursor.execute("UPDATE category SET name = ? WHERE id = ?", (name, cat_id))
            conn.commit()

            cursor.execute("SELECT id, name FROM category WHERE id = ?", (cat_id,))
            row = cursor.fetchone()
            if row:
                return Category(**dict(row))
    except sqlite3.IntegrityError as e:
        print(f"Update error (category): {e}")
    return None


async def delete_category(category_id: int) -> bool:
    try:
        with closing(_connect()) as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM category WHERE id = ?", (category_id,))
            conn.commit()
            return True
    except sqlite3.IntegrityError as e:
        print(f"Delete error (category): {e}")
    return False
