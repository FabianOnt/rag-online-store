import bcrypt

def hash_password(plain_text_password: str) -> str:
    """
    Hashes a plain-text password using bcrypt.
    """
    password_bytes = plain_text_password.encode('utf-8')
    
    salt = bcrypt.gensalt()
    hashed_bytes = bcrypt.hashpw(password_bytes, salt)
    
    return hashed_bytes.decode('utf-8')


def verify_password(plain_text_password: str, true_hashed_password: str) -> bool:
    """
    Compares an input password against the hashed password stored in the database.
    """
    password_bytes = plain_text_password.encode('utf-8')
    hashed_bytes = true_hashed_password.encode('utf-8')
    
    return bcrypt.checkpw(password_bytes, hashed_bytes)