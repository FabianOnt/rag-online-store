import requests

BASE_URL = "http://localhost:8000"


def new_user(name: str, email: str, password: str) -> dict:
    global BASE_URL

    return requests.post(
        f"{BASE_URL}/customer/users", 
        json = {
            "name": name,
            "email": email,
            "password": password
        }
    )


def login(email: str, password: str) -> dict:
    global BASE_URL
        
    return requests.post(
        f"{BASE_URL}/customer/login", 
        json = {
            "email": email,
            "password": password
        }
    )


def logout(session_token: str) -> dict:
    global BASE_URL
        
    return requests.post(
        f"{BASE_URL}/customer/logout", 
        json = {
            "session_token": session_token
        }
    )

def new_chat(name: str, session_token: str) -> dict:
    global BASE_URL
    
    return requests.post(
        f"{BASE_URL}/customer/chats", 
        json = {
            "name": name,
            "session_token": session_token
        }
    )


def get_chats(session_token: str) -> dict:
    global BASE_URL
    
    return requests.post(
        f"{BASE_URL}/customer/chats/list", 
        json = {
            "session_token": session_token
        }
    )


def get_messages(chat_token: str, session_token: str) -> dict:
    global BASE_URL
    
    return requests.post(
        f"{BASE_URL}/customer/messages/list",
        json = {
            "chat_token": chat_token,
            "session_token": session_token
        }
    )


def query(query: str, chat_token: str, session_token: str) -> dict:
    global BASE_URL

    return requests.post(
        f"{BASE_URL}/customer/query", 
        json = {
            "query": query,
            "chat_token": chat_token,
            "session_token": session_token
        }
    )