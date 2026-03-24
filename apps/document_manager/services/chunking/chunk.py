from dataclasses import dataclass


@dataclass
class Chunk:

    chunk_id: int
    document_id: int
    text: str
    start_index: int
    end_index: int
    analysis_text: str | None = None