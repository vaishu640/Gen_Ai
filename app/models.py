from dataclasses import dataclass

@dataclass
class Record:
    topic: str
    rule: str
    applies_to: str
    stage: str
    source_doc: str
    source_url: str