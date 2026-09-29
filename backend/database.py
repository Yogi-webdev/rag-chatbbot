"""MySQL persistence for users and chat history."""

import hashlib
import hmac
import os
import secrets
from datetime import datetime, timedelta
from pathlib import Path

from dotenv import load_dotenv

_DIR = Path(__file__).resolve().parent
load_dotenv(_DIR / ".env")
load_dotenv(_DIR.parent / ".env")

try:
    import mysql.connector
    from mysql.connector import Error
except ImportError:  # Keep the app importable until the dependency is installed.
    mysql = None
    Error = Exception


def _ensure_database():
    if "mysql" not in globals() or mysql is None:
        return
    try:
        conn = mysql.connector.connect(
            host=os.getenv("MYSQL_HOST", "localhost"),
            port=int(os.getenv("MYSQL_PORT", "3306")),
            user=os.getenv("MYSQL_USER", "root"),
            password=os.getenv("MYSQL_PASSWORD", ""),
            connection_timeout=int(os.getenv("MYSQL_CONNECT_TIMEOUT", "2")),
        )
        cursor = conn.cursor()
        db_name = os.getenv("MYSQL_DATABASE", "file_chatbot")
        cursor.execute(f"CREATE DATABASE IF NOT EXISTS `{db_name}`")
        cursor.close()
        conn.close()
    except Exception as e:
        print(f"MySQL ensure database warning: {e}")


def _connection():
    if "mysql" not in globals() or mysql is None:
        raise RuntimeError("mysql-connector-python is not installed")
    return mysql.connector.connect(
        host=os.getenv("MYSQL_HOST", "localhost"),
        port=int(os.getenv("MYSQL_PORT", "3306")),
        database=os.getenv("MYSQL_DATABASE", "file_chatbot"),
        user=os.getenv("MYSQL_USER", "root"),
        password=os.getenv("MYSQL_PASSWORD", ""),
        connection_timeout=int(os.getenv("MYSQL_CONNECT_TIMEOUT", "2")),
    )


def initialize_database():
    """Create the application tables if they do not exist."""
    _ensure_database()
    connection = _connection()
    cursor = connection.cursor()
    try:
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INT AUTO_INCREMENT PRIMARY KEY,
                email VARCHAR(255) NOT NULL UNIQUE,
                password_hash VARCHAR(255) NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS conversations (
                id BIGINT AUTO_INCREMENT PRIMARY KEY,
                user_id INT NOT NULL,
                title VARCHAR(255) NOT NULL DEFAULT 'New chat',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                CONSTRAINT fk_conversation_user FOREIGN KEY (user_id) REFERENCES users(id)
                    ON DELETE CASCADE
            )
        """)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS messages (
                id BIGINT AUTO_INCREMENT PRIMARY KEY,
                conversation_id BIGINT NOT NULL,
                role ENUM('user', 'assistant') NOT NULL,
                content LONGTEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                CONSTRAINT fk_message_conversation FOREIGN KEY (conversation_id) REFERENCES conversations(id)
                    ON DELETE CASCADE
            )
        """)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS login_sessions (
                token_hash CHAR(64) PRIMARY KEY,
                user_id INT NOT NULL,
                expires_at DATETIME NOT NULL,
                CONSTRAINT fk_session_user FOREIGN KEY (user_id) REFERENCES users(id)
                    ON DELETE CASCADE
            )
        """)
        connection.commit()
    finally:
        cursor.close()
        connection.close()


def _hash_password(password, salt=None):
    salt = salt or secrets.token_hex(16)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode(), salt.encode(), 200_000).hex()
    return f"{salt}${digest}"


def _check_password(password, stored):
    try:
        salt, expected = stored.split("$", 1)
    except ValueError:
        return False
    actual = _hash_password(password, salt).split("$", 1)[1]
    return hmac.compare_digest(actual, expected)


def register_user(email, password, name=None):
    email = email.strip().lower()
    if not email or len(password) < 6:
        return None, "Use a valid email and a password with at least 6 characters."
    connection = _connection()
    cursor = connection.cursor()
    try:
        cursor.execute(
            "INSERT INTO users (email, password_hash) VALUES (%s, %s)",
            (email, _hash_password(password)),
        )
        connection.commit()
        return cursor.lastrowid, None
    except Exception as error:
        connection.rollback()
        if "duplicate" in str(error).lower() or "unique" in str(error).lower():
            return None, "That email is already registered."
        raise
    finally:
        cursor.close()
        connection.close()


def authenticate_user(email, password):
    connection = _connection()
    cursor = connection.cursor(dictionary=True)
    try:
        cursor.execute("SELECT id, email, password_hash FROM users WHERE email = %s", (email.strip().lower(),))
        user = cursor.fetchone()
        if user and _check_password(password, user["password_hash"]):
            return {"id": user["id"], "email": user["email"]}, None
        return None, "Invalid email or password."
    finally:
        cursor.close()
        connection.close()


def create_login_session(user_id, days=30):
    token = secrets.token_urlsafe(48)
    token_hash = hashlib.sha256(token.encode()).hexdigest()
    connection = _connection()
    cursor = connection.cursor()
    try:
        cursor.execute(
            "INSERT INTO login_sessions (token_hash, user_id, expires_at) VALUES (%s, %s, %s)",
            (token_hash, user_id, datetime.utcnow() + timedelta(days=days)),
        )
        connection.commit()
        return token
    finally:
        cursor.close()
        connection.close()


def user_from_login_session(token):
    if not token:
        return None
    connection = _connection()
    cursor = connection.cursor(dictionary=True)
    try:
        token_hash = hashlib.sha256(token.encode()).hexdigest()
        cursor.execute(
            """
            SELECT u.id, u.email
            FROM login_sessions s JOIN users u ON u.id = s.user_id
            WHERE s.token_hash = %s AND s.expires_at > UTC_TIMESTAMP()
            """,
            (token_hash,),
        )
        user = cursor.fetchone()
        return {"id": user["id"], "email": user["email"]} if user else None
    finally:
        cursor.close()
        connection.close()


def delete_login_session(token):
    if not token:
        return
    connection = _connection()
    cursor = connection.cursor()
    try:
        token_hash = hashlib.sha256(token.encode()).hexdigest()
        cursor.execute("DELETE FROM login_sessions WHERE token_hash = %s", (token_hash,))
        connection.commit()
    finally:
        cursor.close()
        connection.close()


def format_title_from_text(text):
    clean = text.strip()
    if not clean:
        return "New chat"
    greetings = {"hi", "hello", "hey", "help", "thanks", "thank you", "test"}
    if clean.lower() in greetings:
        return clean.capitalize()
    words = clean.split()
    if len(words) > 6:
        title = " ".join(words[:6]) + "…"
    else:
        title = " ".join(words)
    return title[:60].capitalize()


def create_conversation(user_id, title="New chat"):
    connection = _connection()
    cursor = connection.cursor()
    try:
        cursor.execute(
            """
            SELECT c.id FROM conversations c
            LEFT JOIN messages m ON m.conversation_id = c.id
            WHERE c.user_id = %s AND m.id IS NULL
            ORDER BY c.id DESC LIMIT 1
            """,
            (user_id,)
        )
        row = cursor.fetchone()
        if row:
            return row[0]

        cursor.execute("INSERT INTO conversations (user_id, title) VALUES (%s, %s)", (user_id, title))
        connection.commit()
        return cursor.lastrowid
    finally:
        cursor.close()
        connection.close()


def latest_conversation(user_id):
    connection = _connection()
    cursor = connection.cursor()
    try:
        cursor.execute("SELECT id FROM conversations WHERE user_id = %s ORDER BY updated_at DESC LIMIT 1", (user_id,))
        row = cursor.fetchone()
        return row[0] if row else create_conversation(user_id)
    finally:
        cursor.close()
        connection.close()


def list_conversations(user_id):
    """Return conversations that contain messages, newest first."""
    connection = _connection()
    cursor = connection.cursor(dictionary=True)
    try:
        cursor.execute(
            """
            SELECT
                c.id,
                c.title,
                c.updated_at
            FROM conversations c
            WHERE c.user_id = %s
              AND EXISTS (
                  SELECT 1 FROM messages m WHERE m.conversation_id = c.id
              )
            ORDER BY c.updated_at DESC, c.id DESC
            """,
            (user_id,),
        )
        return cursor.fetchall()
    finally:
        cursor.close()
        connection.close()


def load_messages(conversation_id):
    connection = _connection()
    cursor = connection.cursor(dictionary=True)
    try:
        cursor.execute(
            "SELECT role, content FROM messages WHERE conversation_id = %s ORDER BY id",
            (conversation_id,),
        )
        return cursor.fetchall()
    finally:
        cursor.close()
        connection.close()


def conversation_belongs_to_user(conversation_id, user_id):
    connection = _connection()
    cursor = connection.cursor()
    try:
        cursor.execute(
            "SELECT 1 FROM conversations WHERE id = %s AND user_id = %s",
            (conversation_id, user_id),
        )
        return cursor.fetchone() is not None
    finally:
        cursor.close()
        connection.close()


def delete_conversation(conversation_id, user_id):
    connection = _connection()
    cursor = connection.cursor()
    try:
        cursor.execute(
            "DELETE FROM conversations WHERE id = %s AND user_id = %s",
            (conversation_id, user_id),
        )
        connection.commit()
        return cursor.rowcount > 0
    finally:
        cursor.close()
        connection.close()


def save_message(conversation_id, role, content):
    connection = _connection()
    cursor = connection.cursor()
    try:
        cursor.execute(
            "INSERT INTO messages (conversation_id, role, content) VALUES (%s, %s, %s)",
            (conversation_id, role, content),
        )
        if role == "user":
            formatted_title = format_title_from_text(content)
            cursor.execute(
                """
                UPDATE conversations
                SET title = CASE 
                    WHEN title IN ('New chat', 'Hi', 'Hello', 'Hey', 'Help', 'Thanks') THEN %s 
                    ELSE title 
                END
                WHERE id = %s
                """,
                (formatted_title, conversation_id),
            )
        cursor.execute(
            "UPDATE conversations SET updated_at = CURRENT_TIMESTAMP WHERE id = %s",
            (conversation_id,),
        )
        connection.commit()
    finally:
        cursor.close()
        connection.close()
