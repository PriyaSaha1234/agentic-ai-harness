import os


MEMORY_FILE = "memory.md"


def load_memory():
    if not os.path.exists(MEMORY_FILE):
        return ""

    with open(MEMORY_FILE, "r", encoding="utf-8") as file:
        return file.read()


def save_memory(memory):
    with open(MEMORY_FILE, "w", encoding="utf-8") as file:
        file.write(memory)