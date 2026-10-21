from enum import Enum
from typing import Any, Optional, Dict, List
from decimal import Decimal
from pydantic import BaseModel, Field

class FactSource(str, Enum):
    TRANSACTION_ATTRIBUTE = "TRANSACTION_ATTRIBUTE"
    HISTORICAL_VELOCITY = "HISTORICAL_VELOCITY"
    TEMPORAL_CONTEXT = "TEMPORAL_CONTEXT"
    DERIVED_INFERENCE = "DERIVED_INFERENCE"
    USER_INPUT = "USER_INPUT"
    DATA_QUALITY = "DATA_QUALITY"


class Fact(BaseModel):
    name: str = Field(..., description="Unique fact name/identifier")
    value: Any = Field(..., description="Fact value")
    data_type: str = Field(default="STRING", description="NUMBER, STRING, BOOLEAN, LIST, UNKNOWN")
    source: FactSource = Field(default=FactSource.TRANSACTION_ATTRIBUTE)
    confidence: float = Field(default=1.0, ge=0.0, le=1.0)
    description: str = Field(default="")
    derived_by_rule_id: Optional[str] = Field(default=None, description="Rule that derived this fact if any")

    def to_display_value(self) -> str:
        if self.value is None:
            return "UNKNOWN (Missing)"
        if isinstance(self.value, Decimal):
            return str(self.value)
        if isinstance(self.value, bool):
            return "Yes" if self.value else "No"
        return str(self.value)


class FactSet:
    """Working memory holding verified and derived facts for the inference engine."""

    def __init__(self, initial_facts: Optional[List[Fact]] = None):
        self._facts: Dict[str, Fact] = {}
        if initial_facts:
            for f in initial_facts:
                self.add_fact(f)

    def add_fact(self, fact: Fact) -> None:
        self._facts[fact.name] = fact

    def get_fact(self, name: str) -> Optional[Fact]:
        return self._facts.get(name)

    def get_value(self, name: str, default: Any = None) -> Any:
        fact = self.get_fact(name)
        return fact.value if fact is not None else default

    def has_fact(self, name: str) -> bool:
        return name in self._facts and self._facts[name].value is not None

    def all_facts(self) -> List[Fact]:
        return list(self._facts.values())

    def to_dict(self) -> Dict[str, Any]:
        return {name: f.value for name, f in self._facts.items()}

    def __contains__(self, name: str) -> bool:
        return name in self._facts

    def __len__(self) -> int:
        return len(self._facts)
