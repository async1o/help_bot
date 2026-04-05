from pydantic import BaseModel


class DialogSchema(BaseModel):
    operator_id: str
    sender_id: str
