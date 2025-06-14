from enum import Enum


class Mode(Enum):
    CATEGORY = "category"
    KEYBIND = "keybind"


class KeybindField(Enum):
    KEYS = "keys"
    DESCRIPTION = "description"
