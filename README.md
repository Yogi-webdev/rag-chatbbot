# 📚 File Chatbot - AI-Powered Document Q&A System

A powerful chatbot that reads and understands your uploaded documents, using semantic search and Google Gemini AI to answer questions accurately and contextually.

---

## ✨ Features

### 📄 Multi-Format Document Support

- **Text Files**: `.txt`
- **Office Documents**: `.docx`, `.xlsx`, `.pptx`
- **Data Formats**: `.csv`, `.json`
- **Web Pages**: `.html`
- **Documents**: `.pdf`
- **Images**: `.jpg`, `.png`, `.jpeg`, `.webp` (with OCR)

### 🔍 Smart Search & Understanding

- **Semantic Search**: Uses Google Gemini embeddings for intelligent document search
- **Cosine Similarity Matching**: Finds the most relevant document chunks
- **Adjustable Thresholds**: Control search sensitivity (0.0 - 1.0)
- **Top-K Results**: Returns up to 5 most relevant chunks

### 💬 Conversation-Aware Responses

- **Context Memory**: Remembers previous questions and answers
- **Smart Follow-ups**: Understands follow-up questions using conversation history
- **Relevant Context**: Only uses information from your documents
- **No Hallucinations**: Won't make up information not in documents

### 🌐 Web Interface

- **Modern React UI**: Sleek, responsive chat interface with auth and conversation history
- **Live Chat History**: See all conversations in real-time
- **Adjustable Settings**: Control similarity threshold and result count
- **Search Transparency**: View which documents were used

### 📤 File Management

- **Upload Files Directly**: Add documents via web interface
- **Automatic Processing**: Extracts text and creates embeddings
- **Persistent Storage**: Saves embeddings for fast retrieval
- **Change Detection**: Only re-processes modified files

### 💾 Export & Sharing

- **Export Conversations**: Download chat history as `.txt` or `.md`
- **Source Attribution**: See which documents answered your questions
- **Formatted Output**: Ready-to-share conversation exports

---

## 🚀 Getting Started

### Prerequisites

- Python 3.8+
- Google Gemini API Key (free tier available)
- Virtual environment

### Installation

1. **Clone/Setup the project**

```bash
cd c:\Users\Yogiy\OneDrive\Desktop\file-chatbot
```

2. **Activate virtual environment**

```bash
# Windows
.\venv\Scripts\activate

# Linux/Mac
source venv/bin/activate
```

3. **Install dependencies** (if needed)

```bash
pip install -r backend/requirements.txt
```

4. **Set up Google Gemini API**
   - Create `.env` file in `backend/` (or project root)
   - Add: `GOOGLE_API_KEY=your_api_key_here`
   - Get key from: https://ai.google.dev/

### Quick Start

#### Option 1: Web Interface (React + Backend API)

**Terminal 1 (Backend Server):**
```bash
cd backend
python react_server.py
```
> The backend serves the API and production React frontend at `http://localhost:8000`.

**Terminal 2 (Frontend Dev Mode with Hot Reload, Optional):**
```bash
cd frontend
npm run dev
```
> Opens Vite dev server with proxy to backend API at `http://localhost:5173`.

#### Option 2: Terminal Interface

```bash
cd backend
python app.py
```

Then type your questions directly in the terminal

---

## 📋 How It Works

### 1. **Document Processing**

```
Upload File → Extract Text → Split into Chunks → Create Embeddings → Store
```

### 2. **Query Processing**

```
User Question → Embed Query → Search Similar Chunks → Filter by Threshold → Build Context
```

### 3. **Answer Generation**

```
Context + History → Gemini API → Generate Answer → Display with Sources
```

---

## 🎯 Project Structure

```
file-chatbot/
├── backend/                  # Python Backend & AI Services
│   ├── app.py                # Terminal chat interface
│   ├── react_server.py       # API & static file web server
│   ├── database.py           # MySQL user & conversation persistence
│   ├── embeddings.py         # Google Gemini embeddings
│   ├── search.py             # Semantic search with cosine similarity
│   ├── context.py            # Context building & source attribution
│   ├── generator.py          # Answer generation with Gemini API
│   ├── extractors.py         # Multi-format text extraction
│   ├── chunker.py            # Text splitting into chunks
│   ├── document.py           # Data models (Document, Chunk)
│   ├── vector_store.py       # Persistent embedding storage (ChromaDB)
│   ├── requirements.txt      # Python dependencies
│   ├── uploads/              # Uploaded document files
│   └── chroma_db/            # ChromaDB vector store directory
├── frontend/                 # React SPA Frontend
│   ├── src/                  # React source code & components
│   ├── index.html            # Entry HTML
│   ├── package.json          # Node dependencies & scripts
│   ├── vite.config.js        # Vite configuration & API proxy
│   └── dist/                 # Built production assets
├── README.md                 # Project documentation
└── requirements.txt          # Root dependency entrypoint
```

---

## ⚙️ Configuration

### Similarity Threshold (Default: 0.3)

- **Lower** (0.0 - 0.5): More results, may include less relevant chunks
- **Higher** (0.5 - 1.0): Stricter matching, only highly relevant results
- **Recommended**: 0.3 - 0.5 for general use

### Max Chunks (Default: 5)

- Number of document chunks to use for context
- More chunks = more context but slower processing
- Recommended: 3-5 chunks

### Chunk Size (Default: 500 words)

- Size of text segments created from documents
- **Overlap**: 100 words between chunks
- Change in `chunker.py` if needed

---

## 💡 Usage Examples

### Example 1: Technical Documentation

```
Q: "What is Python?"
A: "Python is a programming language... [from your documents]"
```

### Example 2: Data Analysis

```
Q: "Who is Yogesh?"
A: "Yogesh is 22 years old and lives in Chennai... [from CSV/JSON]"

Follow-up: "What are his skills?"
A: "His skills include Python, React, and MySQL... [remembers context]"
```

### Example 3: Document Retrieval

```
Q: "Which files support file upload?"
A: "Based on your HTML file, the chatbot supports: PDF, DOCX, CSV..."
```

---

## 🔧 Troubleshooting

### No Results Found

- **Issue**: Queries return "No relevant chunks found"
- **Solution**: Lower the similarity threshold in settings (try 0.2)
- **Reason**: Vector embeddings sometimes need looser matching

### API Rate Limit (429 Error)

- **Issue**: "You exceeded your current quota"
- **Solution**: Wait 36+ hours for free tier reset, or upgrade to paid plan
- **Learn More**: https://ai.google.dev/gemini-api/docs/rate-limits

### File Won't Upload

- **Issue**: Unsupported file format error
- **Supported**: PDF, TXT, DOCX, CSV, XLSX, PPTX, JSON, HTML, JPG, PNG, WEBP
- **Solution**: Convert to a supported format

### Vector Store Corruption

- **Issue**: App can't load embeddings
- **Solution**: Delete `vector_store.json` and re-process files

```bash
rm vector_store.json
python app.py
```

---

## 📊 Performance

### Typical Speeds (on local machine)

- **File Upload & Processing**: 5-30 seconds per file
- **Query Search**: 1-2 seconds
- **Answer Generation**: 5-15 seconds (Gemini API)
- **Total Response Time**: 6-20 seconds per question

### File Size Limits

- **Single File**: Up to 50 MB
- **Total Storage**: Depends on disk space
- **Embeddings Database**: ~1 MB per 1000 chunks

---

## 🔐 Privacy & Security

✅ **What We Don't Share**

- Your documents never leave your computer
- Files stored locally in `uploads/` folder
- Only API calls to Google for embeddings & answers

⚠️ **API Calls Made**

- Text embedding requests to Google Gemini
- Answer generation requests to Google Gemini
- Review Google's privacy policy: https://policies.google.com/privacy

---

## 📈 Next Steps & Enhancements

### Potential Improvements

- [ ] Add authentication for multi-user access
- [ ] Implement conversation save/load
- [ ] Add PDF with sources export
- [ ] Support for batch file processing
- [ ] Real-time streaming responses
- [ ] Document tagging & categorization
- [ ] Admin dashboard for file management
- [ ] Integration with cloud storage (Google Drive, Dropbox)

### Deployment Options

- **Local**: Run on your machine (current setup)
- **Cloud**: Deploy to Google Cloud Run, AWS Lambda, Heroku
- **Docker**: Containerize for easy distribution

---

## 🤝 Contributing

Suggestions for improvements?

- Fix bugs in `generator.py` or `search.py`
- Add support for more file formats in `extractors.py`
- Improve UI in `web_app.py`
- Optimize chunking strategy in `chunker.py`

---

## 📚 Technology Stack

| Component            | Technology                                     |
| -------------------- | ---------------------------------------------- |
| **Web Framework**    | Streamlit                                      |
| **LLM & Embeddings** | Google Gemini API                              |
| **Search Algorithm** | Cosine Similarity (NumPy)                      |
| **Text Extraction**  | PyPDF, python-docx, pytesseract, BeautifulSoup |
| **Data Processing**  | Pandas, openpyxl                               |
| **Storage**          | JSON (vector_store.json)                       |
| **Language**         | Python 3.10+                                   |

---

## 📞 Support

### Common Issues & Solutions

**Q: Why is my answer generic/wrong?**

- Lower the similarity threshold to get more relevant chunks
- Make sure your documents clearly contain the information
- Rephrase your question (e.g., "What is Python?" vs "Tell me about Python")

**Q: How do I delete a file?**

- Remove from `uploads/` folder
- Delete `vector_store.json` to regenerate embeddings

**Q: Can I use a different AI model?**

- Yes! Edit `generator.py` to use a different model (Claude, GPT-4, etc.)
- Update embeddings in `embeddings.py` as well

**Q: How do I scale this to production?**

- Deploy with Docker
- Use database (PostgreSQL, Vector DB) instead of JSON
- Add authentication layer
- Implement caching for frequent queries

---

## 📄 License

Open source - feel free to modify and use!

---

## 🎉 Happy Chatting!

Your AI-powered document assistant is ready. Start by:

1. Opening `http://localhost:8501`
2. Uploading your documents
3. Asking questions!

For questions or improvements, check the code or modify as needed! 🚀
