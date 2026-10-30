"""
Category Data Model.
"""

from dataclasses import dataclass
from typing import Optional


@dataclass
class Category:
    category_id: int
    category_name: str
    category_type: str  # 'EXPENSE' or 'INCOME'
    description: Optional[str] = ""
    is_active: str = "Y"

    @classmethod
    def from_dict(cls, data: dict) -> "Category":
        return cls(
            category_id=int(data.get("CATEGORY_ID", 0)),
            category_name=str(data.get("CATEGORY_NAME", "")),
            category_type=str(data.get("CATEGORY_TYPE", "EXPENSE")),
            description=str(data.get("DESCRIPTION") or ""),
            is_active=str(data.get("IS_ACTIVE", "Y"))
        )
