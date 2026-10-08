from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from json import loads, dumps
from secrets import token_hex

from services.chat_cache.session import chat_cache
from services.chat_cache.config import settings as chat_cache_settings
from services.chat_cache.tools import validate_session_token

from services.store_db.session import get_db as get_store_db
from services.store_db.crud import create_review, search_product

from services.rag.agent import run_rag_agent
from services.rag.config import settings as rag_settings

from services.chat_db.session import get_db as get_chat_db
from services.chat_db.security import verify_password
from services.chat_db.crud import (
    create_user,
    create_chat,
    create_message,
    get_password,
    get_chats,
    get_messages,
    validate_chat_token
)


from schemas.customer import (
    LoginRequest,
    LoginResponse,
    LogoutRequest,
    RAGQueryRequest,
    RAGQueryResponse,
    ReviewCreate,
    ReviewResponse,
    ProductSearchItem,
    ProductSearchRequest,
    CreateUserRequest,
    CreateChatRequest,
    GetChatsRequest,
    GetMessagesRequest,
    UserResponse,
    ChatResponse,
    MessageResponse,
    ChatItemResponse,
    MessageItemResponse
)

router = APIRouter(prefix="/customer", tags=["Customer RAG"])


@router.post(
    "/login",
    response_model=LoginResponse
)
def login(
    payload: LoginRequest,
    db: Session = Depends(get_chat_db)
):
    try:
        true_password = get_password(
            db=db,
            email=payload.email
        )
        
        if not verify_password(
            plain_text_password=payload.password,
            true_hashed_password=true_password
        ):
            raise HTTPException(status_code=500, detail=str('Invalid credentials'))
        else:
            pass

        session_token = token_hex(16)

        chat_cache.set(session_token, payload.email, ex=chat_cache_settings.CHAT_SESSION_TIMEOUT)

        return {
            "session_token": session_token
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))



@router.post(
    "/logout"
)
def login(
    payload: LogoutRequest
):
    try:
        if chat_cache.get(payload.session_token) is not None:
            chat_cache.delete(payload.session_token)
        return

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))



@router.post(
    "/query",
    response_model=RAGQueryResponse
)
def ask_rag_system_endpoint(
    payload: RAGQueryRequest,
    db: Session = Depends(get_chat_db)
):
    try:
        email = validate_session_token(
            cache=chat_cache,
            session_token=payload.session_token
        )
    
        if email is None:
            raise HTTPException(status_code=500, detail=str('Invalid session token'))
        
        if not validate_chat_token(db=db, chat_token=payload.chat_token):
            raise HTTPException(status_code=500, detail=str('Invalid chat token'))

        cache_content = chat_cache.get(payload.chat_token)

        if cache_content is None:

            messages = get_messages(
                db=db,
                chat_token=payload.chat_token
            )

            data = [
                {
                    "message_type": msg_type, 
                    "content": content, 
                    "created_at": created_at.isoformat()
                }
                for msg_type, content, created_at in messages
            ]

            if len(data) > rag_settings.NUM_PAST_MESSAGES:
                last_messages = data[:-rag_settings.NUM_PAST_MESSAGES]
            elif len(data) == 0:
                last_messages = []
            else:
                last_messages = data
            
            chat_cache.set(payload.chat_token, dumps(last_messages), ex=chat_cache_settings.CACHE_TIMEOUT)

        else:
            last_messages = loads(cache_content)
        num_messages = len(last_messages)
        if num_messages == rag_settings.NUM_PAST_MESSAGES:
            last_messages = last_messages[:-(rag_settings.NUM_PAST_MESSAGES-2)]
        elif num_messages == rag_settings.NUM_PAST_MESSAGES - 1:
            last_messages = last_messages[:-(rag_settings.NUM_PAST_MESSAGES-2)]
        else:
            pass

        result = run_rag_agent(query=payload.query, last_messages=last_messages)
        
        create_message(
            db=db,
            chat_token=payload.chat_token,
            message_type="client",
            content=payload.query
        )
        create_message(
            db=db,
            chat_token=payload.chat_token,
            message_type="server",
            content=result["answer"]
        )
        last_messages = last_messages + [
            {
                "chat_token": payload.chat_token,
                "message_type": "client",
                "content": payload.query
            },
            {
                "chat_token": payload.chat_token,
                "message_type": "server",
                "content": result["answer"]
            }
        ]
        chat_cache.set(payload.chat_token, dumps(last_messages), ex=chat_cache_settings.CACHE_TIMEOUT)

        return RAGQueryResponse(answer=result["answer"], sources=result.get("sources", []))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post(
    "/reviews", 
    status_code=status.HTTP_201_CREATED,
    response_model=ReviewResponse
)
def create_review_endpoint(
    review_in: ReviewCreate, 
    db: Session = Depends(get_store_db)
):
    """
    Submit a review for a specific product using its SKU.
    """
    try:
        review = create_review(
            db=db,
            product_sku=review_in.product_sku,
            rating=review_in.rating,
            comment=review_in.comment,
        )
        return review
    except ValueError as val_err:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(val_err))
    except Exception as err:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(err))


@router.post(
    "/products/search",
    response_model=List[ProductSearchItem],
    status_code=status.HTTP_200_OK,
)
def search_products_endpoint(
    payload: ProductSearchRequest,
    db: Session = Depends(get_store_db),
):
    """
    Search for products matching a given name. Returns all products if product_name is empty.
    """
    try:
        products = search_product(db=db, product_name=payload.product_name)
        return products
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e),
        )

@router.post(
    "/users",
    status_code=status.HTTP_201_CREATED,
    response_model=UserResponse
)
def create_user_endpoint(
    payload: CreateUserRequest,
    db: Session = Depends(get_chat_db)
):
    """
    Register a new user and securely store their hashed password.
    """
    try:
        user = create_user(
            db=db,
            name=payload.name,
            email=payload.email,
            password=payload.password
        )
        return user
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.post(
    "/chats",
    status_code=status.HTTP_201_CREATED,
    response_model=ChatResponse
)
def create_chat_endpoint(
    payload: CreateChatRequest,
    db: Session = Depends(get_chat_db)
):
    """
    Create a new chat room associated with a user's email.
    """
    try:

        email = validate_session_token(
            cache=chat_cache,
            session_token=payload.session_token
        )

        print(email)
    
        if email is None:
            raise HTTPException(status_code=500, detail=str('Invalid session token'))
        
        chat = create_chat(
            db=db,
            name=payload.name,
            email=email
        )
        return chat
    except ValueError as val_err:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(val_err)
        )
    except RuntimeError as run_err:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(run_err)
        )


@router.post(
    "/chats/list",
    status_code=status.HTTP_200_OK,
    response_model=List[ChatItemResponse]
)
def get_chats_endpoint(
    payload: GetChatsRequest,
    db: Session = Depends(get_chat_db)
):
    """
    Retrieve all active chats for a given user email.
    """
    email = validate_session_token(
        cache=chat_cache,
        session_token=payload.session_token
    )

    if email is None:
        raise HTTPException(status_code=500, detail=str('Invalid session token'))
    
    chats = get_chats(
        db=db,
        email=email
    )

    return [
        {
            "name": name,
            "token": token,
            "created_at": created_at.isoformat()
        }
        for name, token, created_at in chats
    ]


@router.post(
    "/messages/list",
    status_code=status.HTTP_200_OK,
    response_model=List[MessageItemResponse]
)
def get_messages_endpoint(
    payload: GetMessagesRequest,
    db: Session = Depends(get_chat_db)
):
    """
    Retrieve all messages in a chat session for a verified user email and chat token.
    """

    email = validate_session_token(
        cache=chat_cache,
        session_token=payload.session_token
    )

    if email is None:
        raise HTTPException(status_code=500, detail=str('Invalid session token'))
    
    messages = get_messages(
        db=db,
        chat_token=payload.chat_token
    )

    result = [
        {
            "message_type": msg_type, 
            "content": content, 
            "created_at": created_at.isoformat()
        }
        for msg_type, content, created_at in messages
    ]

    if len(result) > rag_settings.NUM_PAST_MESSAGES:
        result = data[:-rag_settings.NUM_PAST_MESSAGES]
    elif len(result) == 0:
        data = []
    else:
        data = result
    chat_cache.set(payload.chat_token, dumps(data), ex=chat_cache_settings.CACHE_TIMEOUT)

    return data