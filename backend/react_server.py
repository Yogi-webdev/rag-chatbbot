"""HTTP API and production static-file server for the React File Chatbot UI."""

import json
import mimetypes
import os
from email.parser import BytesParser
from email.policy import default
from http import HTTPStatus
from http.cookies import SimpleCookie
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import unquote, urlparse

from dotenv import load_dotenv

from chunker import chunk_text
from context import build_context
from database import (
    authenticate_user,
    conversation_belongs_to_user,
    create_conversation,
    create_login_session,
    delete_conversation,
    delete_login_session,
    initialize_database,
    list_conversations,
    load_messages,
    register_user,
    save_message,
    user_from_login_session,
)
from document import Chunk, Document
from embeddings import get_embedding
from extractors import extract_text
from generator import generate_answer
from search import search_chunks
from vector_store import delete_file_from_store, load_store, save_chunks


ROOT = Path(__file__).resolve().parent
PROJECT_ROOT = ROOT.parent if (ROOT.parent / "frontend").exists() else ROOT

CLIENT_DIST = PROJECT_ROOT / "frontend" / "dist"
if not CLIENT_DIST.exists() and (ROOT / "dist").exists():
    CLIENT_DIST = ROOT / "dist"

UPLOADS = ROOT / "uploads"
UPLOADS.mkdir(parents=True, exist_ok=True)
ALLOWED_EXTENSIONS = {".pdf", ".txt", ".docx", ".csv", ".xlsx", ".pptx", ".json", ".html", ".jpg", ".jpeg", ".png", ".webp"}

load_dotenv(ROOT / ".env")
load_dotenv(PROJECT_ROOT / ".env")


def greeting(text):
    responses = {
        "hi": "Hi there! How can I help you with your documents?",
        "hello": "Hello! What would you like to ask?",
        "hey": "Hey! Ready to help you find information.",
        "thanks": "You're welcome! Anything else you'd like to know?",
        "thank you": "You're welcome! Anything else you'd like to know?",
        "help": "Upload a document, then ask me a question about it.",
    }
    return responses.get(text.lower().strip())


class ApiHandler(SimpleHTTPRequestHandler):
    """Serves the React build and the /api endpoints from one origin."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(CLIENT_DIST), **kwargs)

    def log_message(self, format, *args):
        print("[web] " + format % args)

    def _json_body(self):
        length = int(self.headers.get("Content-Length", "0"))
        raw = self.rfile.read(length)
        return json.loads(raw or b"{}")

    def _send_json(self, payload, status=HTTPStatus.OK, cookie=None):
        body = json.dumps(payload, default=str).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        if cookie:
            self.send_header("Set-Cookie", cookie)
        self.end_headers()
        self.wfile.write(body)

    def _token(self):
        cookies = SimpleCookie(self.headers.get("Cookie"))
        return cookies.get("file_chatbot_session").value if cookies.get("file_chatbot_session") else None

    def _user(self):
        token = self._token()
        if not token:
            return None
        try:
            return user_from_login_session(token)
        except Exception:
            return None

    def _require_user(self):
        user = self._user()
        if not user:
            self._send_json({"error": "Please sign in first."}, HTTPStatus.UNAUTHORIZED)
            return None
        return user

    def do_GET(self):
        path = urlparse(self.path).path
        if path == "/api/session":
            self._send_json({"user": self._user()})
            return
        if path == "/api/conversations":
            user = self._user()
            convs = []
            if user:
                try:
                    convs = list_conversations(user["id"])
                except Exception:
                    convs = []
            self._send_json({"conversations": convs})
            return
        if path.startswith("/api/conversations/") and path.endswith("/messages"):
            user = self._user()
            if not user:
                self._send_json({"messages": []})
                return
            try:
                conversation_id = int(path.split("/")[3])
                if not conversation_belongs_to_user(conversation_id, user["id"]):
                    self._send_json({"error": "Conversation not found."}, HTTPStatus.NOT_FOUND)
                    return
                self._send_json({"messages": load_messages(conversation_id)})
            except Exception:
                self._send_json({"messages": []})
            return
        if path == "/api/files":
            UPLOADS.mkdir(exist_ok=True)
            self._send_json({"files": sorted(item.name for item in UPLOADS.iterdir() if item.is_file())})
            return
        if path.startswith("/api/"):
            self._send_json({"error": "Not found."}, HTTPStatus.NOT_FOUND)
            return
        if not CLIENT_DIST.exists():
            self._send_json({"error": "React is not built. Run npm install then npm run build in react_client."}, HTTPStatus.SERVICE_UNAVAILABLE)
            return
        # React router fallback.
        if path != "/" and not (CLIENT_DIST / path.lstrip("/")).exists():
            self.path = "/index.html"
        return super().do_GET()

    def do_POST(self):
        path = urlparse(self.path).path
        try:
            if path == "/api/auth/register":
                body = self._json_body()
                user_id, error = register_user(body.get("email", ""), body.get("password", ""), body.get("name", ""))
                status = HTTPStatus.CREATED if user_id else HTTPStatus.BAD_REQUEST
                self._send_json({"user_id": user_id, "error": error}, status)
                return
            if path == "/api/auth/login":
                body = self._json_body()
                user, error = authenticate_user(body.get("email", ""), body.get("password", ""))
                if not user:
                    self._send_json({"error": error}, HTTPStatus.UNAUTHORIZED)
                    return
                token = create_login_session(user["id"])
                cookie = f"file_chatbot_session={token}; Path=/; Max-Age=2592000; HttpOnly; SameSite=Lax"
                self._send_json({"user": user}, cookie=cookie)
                return
            if path == "/api/auth/logout":
                token = self._token()
                if token:
                    try:
                        delete_login_session(token)
                    except Exception:
                        pass
                self._send_json({"ok": True}, cookie="file_chatbot_session=; Path=/; Max-Age=0; HttpOnly; SameSite=Lax")
                return
            if path == "/api/conversations":
                user = self._user()
                conv_id = None
                if user:
                    try:
                        conv_id = create_conversation(user["id"])
                    except Exception:
                        conv_id = 1
                else:
                    conv_id = 1
                self._send_json({"conversation_id": conv_id}, HTTPStatus.CREATED)
                return
            if path == "/api/chat":
                self._chat()
                return
            if path == "/api/upload":
                self._upload()
                return
            self._send_json({"error": "Not found."}, HTTPStatus.NOT_FOUND)
        except (ValueError, json.JSONDecodeError) as error:
            self._send_json({"error": str(error) or "Invalid request."}, HTTPStatus.BAD_REQUEST)
        except Exception as error:
            print(f"API error: {error}")
            self._send_json({"error": "The request could not be completed."}, HTTPStatus.INTERNAL_SERVER_ERROR)

    def do_DELETE(self):
        path = urlparse(self.path).path
        if path.startswith("/api/conversations/"):
            user = self._user()
            if not user:
                self._send_json({"error": "Please sign in first."}, HTTPStatus.UNAUTHORIZED)
                return
            try:
                conv_id = int(path.split("/")[3])
                delete_conversation(conv_id, user["id"])
                self._send_json({"ok": True})
            except Exception as error:
                self._send_json({"error": str(error)}, HTTPStatus.BAD_REQUEST)
            return
        if path.startswith("/api/files/"):
            filename = unquote(path.split("/api/files/")[1])
            try:
                delete_file_from_store(filename, UPLOADS)
                self._send_json({"ok": True, "deleted": filename})
            except Exception as error:
                self._send_json({"error": str(error)}, HTTPStatus.BAD_REQUEST)
            return
        self._send_json({"error": "Not found."}, HTTPStatus.NOT_FOUND)

    def _chat(self):
        user = self._user()
        body = self._json_body()
        question = body.get("question", "").strip()
        conversation_id = body.get("conversation_id")
        selected_files = body.get("selected_files")  # list of filenames or None
        if not question:
            raise ValueError("Enter a message.")

        history = []
        if user and conversation_id:
            try:
                conv_id_int = int(conversation_id)
                previous_messages = load_messages(conv_id_int)
                history = [
                    {"question": previous_messages[index]["content"], "answer": previous_messages[index + 1]["content"]}
                    for index in range(0, len(previous_messages) - 1, 2)
                    if previous_messages[index]["role"] == "user" and previous_messages[index + 1]["role"] == "assistant"
                ]
            except Exception:
                history = []

        answer = greeting(question)
        if not answer:
            # Enforce: If user has not checked any file in Uploads, do NOT answer document questions
            if not selected_files or len(selected_files) == 0:
                answer = "Please select at least one uploaded file from the sidebar checkboxes to ask questions about it."
            else:
                store = load_store(UPLOADS)
                all_chunks = store[2] if store else []

                # Filter chunks strictly to selected files
                selected_set = set(selected_files)
                chunks = [c for c in all_chunks if c.filename in selected_set]
                if not chunks:
                    answer = f"I couldn't find indexed data for {', '.join(selected_files)}. Please check your uploaded files."
                else:
                    search_query = question
                    if history:
                        recent = history[-2:]
                        search_query = "\n".join(f"Q: {item['question']}\nA: {item['answer']}" for item in recent) + f"\nQ: {question}"

                    MIN_SCORE = 0.3  # Minimum cosine similarity to consider a chunk relevant

                    if len(selected_set) > 1:
                        # Multi-file selection: get top 3 chunks from EACH selected file so all files are referenced
                        combined_results = []
                        for fname in selected_set:
                            file_chunks = [c for c in chunks if c.filename == fname]
                            if file_chunks:
                                f_results = search_chunks(file_chunks, search_query)
                                combined_results.extend(r for r in f_results[:3] if r[1] >= MIN_SCORE)
                        combined_results.sort(key=lambda item: item[1], reverse=True)
                        results = combined_results[:8]
                    else:
                        # Single-file selection: get top 5 chunks strictly for that 1 file
                        all_results = search_chunks(chunks, search_query)
                        results = [r for r in all_results[:5] if r[1] >= MIN_SCORE]

                    if not results:
                        answer = "I couldn't find relevant information about that in the selected file(s). Try rephrasing your question or make sure the document contains that information."
                    else:
                        context = build_context(results)
                        answer = generate_answer(question, context, history)

        if user:
            try:
                conv_id_int = int(conversation_id) if conversation_id else None
                if not conv_id_int or not conversation_belongs_to_user(conv_id_int, user["id"]):
                    conv_id_int = create_conversation(user["id"])
                    conversation_id = conv_id_int
                save_message(conv_id_int, "user", question)
                save_message(conv_id_int, "assistant", answer)
            except Exception as e:
                print(f"Database message save warning: {e}")

        self._send_json({"answer": answer, "conversation_id": conversation_id})

    def _upload(self):
        content_type = self.headers.get("Content-Type", "")
        if "multipart/form-data" not in content_type:
            raise ValueError("Upload must be multipart form data.")
        
        length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(length)
        msg_bytes = b"Content-Type: " + content_type.encode("utf-8") + b"\r\n\r\n" + body
        msg = BytesParser(policy=default).parsebytes(msg_bytes)
        
        UPLOADS.mkdir(exist_ok=True)
        chunks = []
        uploaded_names = []

        for part in msg.walk():
            filename = part.get_filename()
            if not filename:
                continue
            filename = Path(filename).name
            if not filename or Path(filename).suffix.lower() not in ALLOWED_EXTENSIONS:
                continue
            content = part.get_payload(decode=True)
            if not content:
                continue
            destination = UPLOADS / filename
            destination.write_bytes(content)
            text = extract_text(destination)
            document = Document(filename=filename, file_type=destination.suffix.lower(), text=text)
            for index, section in enumerate(chunk_text(document.text), start=1):
                embedding = get_embedding(section)
                if embedding:
                    chunks.append(Chunk(filename=filename, chunk_id=index, text=section, embedding=embedding))
            uploaded_names.append(filename)

        if chunks:
            save_chunks(chunks, UPLOADS)
        self._send_json({"files": uploaded_names, "chunks": len(chunks)})


if __name__ == "__main__":
    try:
        initialize_database()
        print("Database initialized successfully.")
    except Exception as error:
        print(f"Database notice: {error}. Running in resilient mode.")
    port = int(os.getenv("PORT", "8000"))
    print(f"React File Chatbot running at http://localhost:{port}")
    ThreadingHTTPServer(("0.0.0.0", port), ApiHandler).serve_forever()
