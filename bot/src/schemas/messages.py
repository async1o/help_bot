from pydantic import BaseModel


class MsgSchema(BaseModel):
    request_id: str
    message_id: int
    operator_id: str
    sender_id: str
