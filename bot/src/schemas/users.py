from typing import Optional
from datetime import datetime
from pydantic import BaseModel

class UserSchema(BaseModel):
    user_id: str
    full_name: Optional[str] = None
    is_operator: bool = False
    is_admin: bool = False
    is_paid: bool = False
    paid_at: Optional[datetime] = None
    has_paid_ever: bool = False
