"""
User Models - Data models for user-related operations
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Optional


@dataclass
class User:
    """User data model"""
    id: int
    email: str
    full_name: str
    status: str
    email_verified: bool = False
    created_at: Optional[datetime] = None
    last_login_at: Optional[datetime] = None

    @classmethod
    def from_dict(cls, data: dict) -> "User":
        """Create User from database dict"""
        return cls(
            id=data["id"],
            email=data["email"],
            full_name=data["full_name"],
            status=data["status"],
            email_verified=data.get("email_verified", False),
            created_at=data.get("created_at"),
            last_login_at=data.get("last_login_at"),
        )

    def to_dict(self) -> dict:
        """Convert User to dict"""
        return {
            "id": self.id,
            "email": self.email,
            "full_name": self.full_name,
            "status": self.status,
            "email_verified": self.email_verified,
            "created_at": self.created_at,
            "last_login_at": self.last_login_at,
        }


@dataclass
class Subscription:
    """Subscription data model"""
    id: Optional[int] = None
    user_id: int = 0
    tier: str = "free"
    status: str = "active"
    started_at: Optional[datetime] = None
    expires_at: Optional[datetime] = None
    payment_method: Optional[str] = None
    amount: Optional[float] = None
    currency: str = "VND"

    @classmethod
    def from_dict(cls, data: dict) -> "Subscription":
        """Create Subscription from database dict"""
        return cls(
            id=data.get("id"),
            user_id=data.get("user_id", 0),
            tier=data.get("tier", "free"),
            status=data.get("status", "active"),
            started_at=data.get("started_at"),
            expires_at=data.get("expires_at"),
            payment_method=data.get("payment_method"),
            amount=float(data["amount"]) if data.get("amount") is not None else None,
            currency=data.get("currency", "VND"),
        )

    def to_dict(self) -> dict:
        """Convert Subscription to dict"""
        return {
            "id": self.id,
            "user_id": self.user_id,
            "tier": self.tier,
            "status": self.status,
            "started_at": self.started_at,
            "expires_at": self.expires_at,
            "payment_method": self.payment_method,
            "amount": self.amount,
            "currency": self.currency,
        }
