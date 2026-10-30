"""
Transaction Data Model.
"""

from dataclasses import dataclass
from datetime import datetime, date
from typing import Optional, Union


@dataclass
class Transaction:
    transaction_id: Optional[int]
    user_id: int
    category_id: int
    category_name: str
    transaction_type: str  # 'INCOME' or 'EXPENSE'
    expense_type: str      # 'NEED', 'WANTS', 'SELF', 'ANONYMOUS', 'INVESTMENT', 'SAVINGS', 'OTHER'
    amount: float
    transaction_date: Union[date, datetime]
    payment_method: str    # 'UPI', 'Credit Card', 'Debit Card', 'Net Banking', 'Cash'
    description: str
    notes: Optional[str] = ""
    created_at: Optional[datetime] = None

    @classmethod
    def from_dict(cls, data: dict) -> "Transaction":
        tx_date = data.get("TRANSACTION_DATE")
        if isinstance(tx_date, str):
            try:
                tx_date = datetime.strptime(tx_date[:10], "%Y-%m-%d").date()
            except Exception:
                tx_date = date.today()

        return cls(
            transaction_id=int(data.get("TRANSACTION_ID", 0)) if data.get("TRANSACTION_ID") else None,
            user_id=int(data.get("USER_ID", 1)),
            category_id=int(data.get("CATEGORY_ID", 0)),
            category_name=str(data.get("CATEGORY_NAME", "Uncategorized")),
            transaction_type=str(data.get("TRANSACTION_TYPE", "EXPENSE")),
            expense_type=str(data.get("EXPENSE_TYPE", "NEED")),
            amount=float(data.get("AMOUNT", 0.0)),
            transaction_date=tx_date,
            payment_method=str(data.get("PAYMENT_METHOD", "UPI")),
            description=str(data.get("DESCRIPTION", "")),
            notes=str(data.get("NOTES") or ""),
            created_at=data.get("CREATED_AT")
        )
