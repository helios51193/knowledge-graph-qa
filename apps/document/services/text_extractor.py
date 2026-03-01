import os

def extract_text_from_file(path):
    extension = os.path.splitext(path)[1].lower()

    if extension == ".txt":
        with open(path, "r", encoding="utf-8") as f:
            return f.read()

    if extension == ".pdf":
        from pdfminer.high_level import extract_text
        return extract_text(path)

    return ""