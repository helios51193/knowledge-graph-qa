from pathlib import Path


def extract_text(file_path):

    ext = Path(file_path).suffix.lower()

    if ext in (".txt", ".md"):
        with open(file_path) as f:
            return f.read()

    raise Exception("Unsupported file type")