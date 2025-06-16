# Keybind Vault

A TUI (Text-based User Interface) app built with [Textual](https://github.com/Textualize/textual) for managing your keyboard shortcuts. Organize, search, add, edit, and delete keybinds in a sleek terminal interface.

---

## Features

- **Dark Mode** toggle
- **Search** keybinds by keys, name, or description
- **Add**, **Edit**, **Delete** keybinds
- Organize keybinds into categories
- Uses a lightweight sqlite3 database for storage

---
![Demo](gif/demo.gif)
---

## Getting Started

### 1. Clone the repository

```bash
git clone https://github.com/thompsonrm/Keybind-Vault.git
cd Keybind-Vault
```

### 2. Set up a virtual environment

```bash
# With Python's built-in venv
python -m venv .venv

# Or with uv
uv venv

# Activate the environment (Windows)
.venv\Scripts\activate

# Or on Unix/macOS
source .venv/bin/activate
```

### 3. Install the package

#### Option A: Using pip (standard)

```bash
pip install .
```

#### Option B: Using uv (faster resolver)

```bash
uv pip install .
```

This installs runtime  as declared in `pyproject.toml`.dependencies

### 4. (Optional) Install development dependencies

If you want linting or other dev tools:

```bash
pip install .[dev]
# or
uv pip install .[dev]
```

This pulls in tools like `ruff` as specified under `[project.optional-dependencies]`.

### 5. Verify installation

After installation, you should have the `keybind-vault` console script available:

```bash
keybind-vault --help
```

---


## Project Structure

```text
keybind_vault/
│
├── db/                    # SQLite database logic
│   ├── __init__.py
│   └── sqlite_db.py
│
├── modals/                # Textual modal screens for Add, Edit, Delete, etc.
│   ├── styles/            # Textual CSS for the modal screens
│   ├── add_modal.py
│   ├── delete_modal.py
│   ├── edit_modal.py
│   ├── search_modal.py
│   ├── vault_types.py
│   └── __init__.py
│
├── styles/
│   └── styles.tcss        # Textual CSS for the main file
│
├── main.py                # Main Textual app logic
└── __init__.py
```

---

## Technologies Used

- Python 3.13+
- [Textual](https://textual.textualize.io/) — modern TUI framework for Python
- [Uv](https://docs.astral.sh/uv/) An extremely fast Python package and project manager, written in Rust.
- [Ruff](https://docs.astral.sh/ruff/) An extremely fast Python linter and code formatter, written in Rust.
- SQLite (via `sqlite3` module)

