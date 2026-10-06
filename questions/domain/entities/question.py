from dataclasses import dataclass

@dataclass
class Question:
    question: str
    id: int | None = None
    
