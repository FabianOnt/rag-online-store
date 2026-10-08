import secrets
from datetime import datetime
from typing import Sequence, Tuple
from sqlalchemy import select, exists
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from services.chat_db.models import Chat, Message, MessageType, User, UserPassword
from services.chat_db.security import hash_password


def create_user(
    db: Session,
    name: str,
    email: str,
    password: str
) -> User:
    """Register a new User and store a hashed version of its password."""
    user = User(name=name, email=email)
    db.add(user)
    db.flush()  # Populates user.id for the foreign key reference

    hashed_pw = hash_password(password)
    user_password = UserPassword(user_id=user.id, password_hash=hashed_pw)
    db.add(user_password)
    
    db.commit()
    db.refresh(user)
    return user


def create_chat(
    db: Session,
    name: str,
    email: str
) -> Chat:
    """Creates a new chat associated to a user with email <email> if valid."""
    user = db.scalar(select(User).where(User.email == email))
    if not user:
        raise ValueError(f"User with email '{email}' does not exist.")

    max_retries = 3
    for _ in range(max_retries):
        try:
            token = secrets.token_hex(16)
            chat = Chat(name=name, user_id=user.id, token=token)
            db.add(chat)
            db.commit()
            db.refresh(chat)
            return chat
        except IntegrityError:
            db.rollback()
            continue

    raise RuntimeError("Failed to generate a unique token after maximum retries.")


def create_message_type(
    db: Session,
    name: str
) -> MessageType:
    """Creates a new message type."""
    message_type = MessageType(name=name)
    db.add(message_type)
    db.commit()
    db.refresh(message_type)
    return message_type


def create_message(
    db: Session,
    chat_token: str,
    message_type: str,
    content: str
) -> Message:
    """
    Creates a new message associated to an existant chat with token <token>
    and message type <message_type> associated to an existant message type
    if both valid.
    """
    chat = db.scalar(select(Chat).where(Chat.token == chat_token))
    if not chat:
        raise ValueError(f"Chat with token '{chat_token}' does not exist.")

    msg_type = db.scalar(select(MessageType).where(MessageType.name == message_type))
    if not msg_type:
        raise ValueError(f"Message type '{message_type}' does not exist.")

    message = Message(chat_id=chat.id, type_id=msg_type.id, content=content)
    db.add(message)
    db.commit()
    db.refresh(message)
    return message


def get_password(
    db: Session,
    email: str
) -> str:
    """
    Returns the hashed password associated to an existant user with email <email>
    if valid.
    """
    query = (
        select(UserPassword.password_hash)
        .join(User, User.id == UserPassword.user_id)
        .where(User.email == email)
    )
    password_hash = db.scalar(query)
    if not password_hash:
        raise ValueError(f"No password record found for user with email '{email}'.")
    return password_hash


def get_chats(
    db: Session,
    email: str
) -> Sequence[Tuple[str, str, datetime]]:
    """
    Returns all the chats associated to an existant user with email <email> if valid.
    (name, token, created_at)
    """
    query = (
        select(Chat.name, Chat.token, Chat.created_at)
        .join(User, User.id == Chat.user_id)
        .where(User.email == email)
    )
    return db.execute(query).tuples().all()


def get_messages(
    db: Session,
    chat_token: str
) -> Sequence[Tuple[str, str, datetime]]:
    """
    Returns all messages associated to an existant chat with token <chat_token> and
    user with email <email> if both valid. (message_type, content, created_at)
    """
    query = (
        select(MessageType.name, Message.content, Message.created_at)
        .join(Chat, Message.chat_id == Chat.id)
        .join(MessageType, Message.type_id == MessageType.id)
        .where(Chat.token == chat_token)
        .order_by(Message.created_at.asc())
    )
    return db.execute(query).tuples().all()


def validate_chat_token(
    db: Session,
    chat_token: str
) -> bool:
    
    query = select(exists().where(Chat.token == chat_token))

    return db.scalar(query)