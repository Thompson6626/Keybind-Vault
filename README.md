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

## Installation

If you just want to install and use **Keybind Vault** from PyPI:

### 1. Install via pip

```bash
pip install keybind-vault
```

Or, using `uv`:

```bash
uv pip install keybind-vault
```

### 2. Use the CLI

```bash
keybind-vault
```

This launches the TUI.

### 3. To Uninstall

```bash
pip uninstall keybind-vault
```

---

## For Contributors / Developers

If you want to clone the repo, modify the code, and work on the project locally:

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

### 3. Install dependencies and set up in editable mode

```bash
# Sync dependencies
uv sync

# Install package in editable mode
uv pip install -e .
```

This allows you to edit the code and test changes without reinstalling.

### 4. (Optional) Install development dependencies

```bash
# With pip
pip install .[dev]

# Or with uv
uv pip install .[dev]
```

Installs tools like `ruff` for linting and formatting.

---

## Development Commands

```bash
# Format code
uv run ruff format .

# Run linter
uv run ruff check .
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
- [Uv](https://docs.astral.sh/uv/) — extremely fast Python package manager, written in Rust
- [Ruff](https://docs.astral.sh/ruff/) — extremely fast linter & formatter, written in Rust
- SQLite (via `sqlite3` module)