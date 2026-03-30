from dataclasses import dataclass, field


@dataclass
class Chunk:

    chunk_id: int
    document_id: int
    text: str
    start_index: int
    end_index: int
    analysis_text: str | None = None
    source_chunk_ids: list[int] = field(default_factory=list)