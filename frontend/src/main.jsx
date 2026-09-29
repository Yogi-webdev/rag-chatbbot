import { useEffect, useRef, useState } from 'react'
import { createRoot } from 'react-dom/client'
import './styles.css'

// ─── Login Page ───────────────────────────────────────────────────────────────
function LoginPage({ onLogin }) {
  const [mode, setMode] = useState('login') // 'login' | 'register'
  const [name, setName] = useState('')
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [confirmPassword, setConfirmPassword] = useState('')
  const [showPw, setShowPw] = useState(false)
  const [showConfirmPw, setShowConfirmPw] = useState(false)
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)

  const submit = async (e) => {
    e.preventDefault()
    setError('')

    if (mode === 'register') {
      if (!name.trim()) {
        setError('Please enter your full name.')
        return
      }
      if (!email.trim()) {
        setError('Please enter your email address.')
        return
      }
      if (password.length < 6) {
        setError('Password must be at least 6 characters long.')
        return
      }
      if (password !== confirmPassword) {
        setError('Passwords do not match. Please check and try again.')
        return
      }
    }

    setLoading(true)
    try {
      if (mode === 'register') {
        const res = await fetch('/api/auth/register', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ name: name.trim(), email: email.trim(), password }),
          credentials: 'include',
        })
        const data = await res.json()
        if (!res.ok) throw new Error(data.error || 'Registration failed.')
        
        // Auto-login immediately upon successful registration
        const loginRes = await fetch('/api/auth/login', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ email: email.trim(), password }),
          credentials: 'include',
        })
        const loginData = await loginRes.json()
        if (loginRes.ok && loginData.user) {
          onLogin(loginData.user)
          return
        }
        setMode('login')
        setError('Account created! Please sign in with your email and password.')
      } else {
        const res = await fetch('/api/auth/login', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ email: email.trim(), password }),
          credentials: 'include',
        })
        const data = await res.json()
        if (!res.ok) throw new Error(data.error || 'Login failed.')
        onLogin(data.user)
      }
    } catch (err) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="login-screen">
      {/* Top Left Brand */}
      <div className="login-top-brand">
        <div className="login-brand-logo">
          <svg viewBox="0 0 24 24" width="22" height="22" fill="currentColor">
            <path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm-1 14.5v-9l6 4.5-6 4.5z" />
          </svg>
        </div>
        <span className="login-brand-text">File Chatbot</span>
      </div>

      {/* Background Arc Rings */}
      <div className="login-arc-bg">
        <div className="arc-circle arc-1"></div>
        <div className="arc-circle arc-2"></div>
        <div className="arc-circle arc-3"></div>
      </div>

      {/* Centered Glassmorphism Card */}
      <div className="login-card-container">
        <div className="login-glass-card">
          {/* Brand Logo */}
          <div className="login-card-logo">
            <svg viewBox="0 0 24 24" width="24" height="24" fill="currentColor">
              <path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm-1 14.5v-9l6 4.5-6 4.5z" />
            </svg>
          </div>

          <h1 className="login-headline">
            {mode === 'login' ? 'Sign in with email' : 'Create an account'}
          </h1>
          
          <p className="login-subtext">
            {mode === 'login'
              ? 'Upload documents, ask questions, and chat with your files in real time. For free'
              : 'Sign up to analyze your PDFs, Word documents, Excel sheets, and images with AI.'}
          </p>

          <form onSubmit={submit} className="login-form-box">
            {/* Name Field - Register Mode Only */}
            {mode === 'register' && (
              <div className="login-input-row">
                <span className="login-input-icon">
                  <svg viewBox="0 0 24 24" width="17" height="17" fill="none" stroke="#8c93a0" strokeWidth="2">
                    <path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2" />
                    <circle cx="12" cy="7" r="4" />
                  </svg>
                </span>
                <input
                  id="login-name-input"
                  type="text"
                  placeholder="Full Name"
                  value={name}
                  onChange={(e) => setName(e.target.value)}
                  required
                  autoComplete="name"
                />
              </div>
            )}

            {/* Email Field */}
            <div className="login-input-row">
              <span className="login-input-icon">
                <svg viewBox="0 0 24 24" width="17" height="17" fill="none" stroke="#8c93a0" strokeWidth="2">
                  <path d="M4 4h16c1.1 0 2 .9 2 2v12c0 1.1-.9 2-2 2H4c-1.1 0-2-.9-2-2V6c0-1.1.9-2 2-2z" />
                  <polyline points="22,6 12,13 2,6" />
                </svg>
              </span>
              <input
                id="login-email-input"
                type="email"
                placeholder="Email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                required
                autoComplete="email"
              />
            </div>

            {/* Password Field */}
            <div className="login-input-row">
              <span className="login-input-icon">
                <svg viewBox="0 0 24 24" width="17" height="17" fill="none" stroke="#8c93a0" strokeWidth="2">
                  <rect x="3" y="11" width="18" height="11" rx="2" ry="2" />
                  <path d="M7 11V7a5 5 0 0 1 10 0v4" />
                </svg>
              </span>
              <input
                id="login-password-input"
                type={showPw ? 'text' : 'password'}
                placeholder={mode === 'register' ? 'Password (min 6 chars)' : 'Password'}
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                required
                autoComplete={mode === 'login' ? 'current-password' : 'new-password'}
              />
              <button
                type="button"
                className="login-pw-toggle-btn"
                onClick={() => setShowPw(!showPw)}
                tabIndex={-1}
                title={showPw ? 'Hide password' : 'Show password'}
              >
                {showPw ? (
                  <svg viewBox="0 0 24 24" width="17" height="17" fill="none" stroke="#8c93a0" strokeWidth="2">
                    <path d="M17.94 17.94A10.07 10.07 0 0 1 12 20c-7 0-11-8-11-8a18.45 18.45 0 0 1 5.06-5.94" />
                    <path d="M9.9 4.24A9.12 9.12 0 0 1 12 4c7 0 11 8 11 8a18.5 18.5 0 0 1-2.16 3.19" />
                    <line x1="1" y1="1" x2="23" y2="23" />
                  </svg>
                ) : (
                  <svg viewBox="0 0 24 24" width="17" height="17" fill="none" stroke="#8c93a0" strokeWidth="2">
                    <path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z" />
                    <circle cx="12" cy="12" r="3" />
                  </svg>
                )}
              </button>
            </div>

            {/* Confirm Password Field - Register Mode Only */}
            {mode === 'register' && (
              <div className="login-input-row">
                <span className="login-input-icon">
                  <svg viewBox="0 0 24 24" width="17" height="17" fill="none" stroke="#8c93a0" strokeWidth="2">
                    <path d="M9 11l3 3L22 4" />
                    <path d="M21 12v7a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h11" />
                  </svg>
                </span>
                <input
                  id="login-confirm-password-input"
                  type={showConfirmPw ? 'text' : 'password'}
                  placeholder="Confirm Password"
                  value={confirmPassword}
                  onChange={(e) => setConfirmPassword(e.target.value)}
                  required
                  autoComplete="new-password"
                />
                <button
                  type="button"
                  className="login-pw-toggle-btn"
                  onClick={() => setShowConfirmPw(!showConfirmPw)}
                  tabIndex={-1}
                  title={showConfirmPw ? 'Hide confirm password' : 'Show confirm password'}
                >
                  {showConfirmPw ? (
                    <svg viewBox="0 0 24 24" width="17" height="17" fill="none" stroke="#8c93a0" strokeWidth="2">
                      <path d="M17.94 17.94A10.07 10.07 0 0 1 12 20c-7 0-11-8-11-8a18.45 18.45 0 0 1 5.06-5.94" />
                      <path d="M9.9 4.24A9.12 9.12 0 0 1 12 4c7 0 11 8 11 8a18.5 18.5 0 0 1-2.16 3.19" />
                      <line x1="1" y1="1" x2="23" y2="23" />
                    </svg>
                  ) : (
                    <svg viewBox="0 0 24 24" width="17" height="17" fill="none" stroke="#8c93a0" strokeWidth="2">
                      <path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z" />
                      <circle cx="12" cy="12" r="3" />
                    </svg>
                  )}
                </button>
              </div>
            )}

            {/* Forgot password - Login Mode Only */}
            {mode === 'login' && (
              <div className="login-forgot-row">
                <button
                  type="button"
                  className="login-forgot-link"
                  onClick={() => setError('Password reset instructions: Please contact administrator or create a new account.')}
                >
                  Forgot password?
                </button>
              </div>
            )}

            {/* Status / Error feedback */}
            {error && (
              <div className={`login-alert-msg ${error.includes('created') ? 'success' : ''}`}>
                {error}
              </div>
            )}

            {/* Submit Button */}
            <button
              id="login-submit-btn"
              type="submit"
              className="login-get-started-btn"
              disabled={loading}
            >
              {loading ? 'Please wait…' : mode === 'login' ? 'Get Started' : 'Create Account'}
            </button>
          </form>

          {/* Switch mode */}
          <div className="login-footer-switch">
            <span>
              {mode === 'login' ? "Don't have an account? " : 'Already have an account? '}
            </span>
            <button
              type="button"
              className="login-switch-btn"
              onClick={() => {
                setMode(mode === 'login' ? 'register' : 'login')
                setError('')
              }}
            >
              {mode === 'login' ? 'Sign up' : 'Sign in'}
            </button>
          </div>
        </div>
      </div>
    </div>
  )
}

const api = async (url, options = {}) => {
  try {
    const response = await fetch(url, { credentials: 'include', ...options })
    const data = await response.json()
    if (!response.ok) throw new Error(data.error || 'Something went wrong.')
    return data
  } catch (err) {
    if (err.name === 'SyntaxError') {
      throw new Error('Server response error')
    }
    throw err
  }
}

const DEFAULT_RECENTS = [
  { id: 'def-1', title: 'Fix file question responses', isDefault: true },
  { id: 'def-2', title: 'Chatbot Loading Behavior Requirements', isDefault: true },
  { id: 'def-3', title: 'Explain Streamlit document search', isDefault: true },
  { id: 'def-4', title: 'PDF & DOCX text extraction pipeline', isDefault: true },
  { id: 'def-5', title: 'CSV & Excel table search query', isDefault: true },
  { id: 'def-6', title: 'OCR Image document processing', isDefault: true },
  { id: 'def-7', title: 'Gemini Embeddings RAG store', isDefault: true },
  { id: 'def-8', title: 'ChromaDB vector store indexing', isDefault: true },
  { id: 'def-9', title: 'MySQL chat history database', isDefault: true },
  { id: 'def-10', title: 'Multi-format document extractor', isDefault: true },
  { id: 'def-11', title: 'Cosine similarity search tuning', isDefault: true },
  { id: 'def-12', title: 'Follow-up question context memory', isDefault: true },
  { id: 'def-13', title: 'API rate limit & quota handling', isDefault: true },
  { id: 'def-14', title: 'Document export to TXT and Markdown', isDefault: true },
  { id: 'def-15', title: 'Vector store change detection', isDefault: true },
]

// ─── Main App ─────────────────────────────────────────────────────────────────
function App() {
  const [user, setUser] = useState(null)
  const [sessionChecked, setSessionChecked] = useState(false)
  const [conversations, setConversations] = useState([])
  const [conversationId, setConversationId] = useState(null)
  const [activeRecentId, setActiveRecentId] = useState('def-1')
  const [messages, setMessages] = useState([])
  const [prompt, setPrompt] = useState('')
  const [isSending, setIsSending] = useState(false)

  // UI states
  const [showSearchModal, setShowSearchModal] = useState(false)
  const [searchQuery, setSearchQuery] = useState('')
  const [showPlusModal, setShowPlusModal] = useState(false)
  const [showScheduledModal, setShowScheduledModal] = useState(false)
  const [showPluginsModal, setShowPluginsModal] = useState(false)
  const [notice, setNotice] = useState('')
  const [uploadedFiles, setUploadedFiles] = useState([])
  const [selectedFiles, setSelectedFiles] = useState(new Set())
  
  const inputRef = useRef(null)
  const fileInputRef = useRef(null)

  const loadFiles = async () => {
    try {
      const data = await api('/api/files')
      if (data && data.files) {
        setUploadedFiles(data.files)
      }
    } catch {
      // ignore
    }
  }

  const deleteFile = async (filename) => {
    try {
      const data = await api(`/api/files/${encodeURIComponent(filename)}`, { method: 'DELETE' })
      setUploadedFiles((prev) => prev.filter((f) => f !== filename))
      setSelectedFiles((prev) => {
        const newSet = new Set(prev)
        newSet.delete(filename)
        return newSet
      })
    } catch (err) {
      setNotice('Failed to delete file.')
    }
  }

  const toggleFileSelection = (filename) => {
    setSelectedFiles(prev => {
      const next = new Set(prev)
      if (next.has(filename)) next.delete(filename)
      else next.add(filename)
      return next
    })
  }

  const toggleAllFiles = () => {
    if (selectedFiles.size === uploadedFiles.length) {
      setSelectedFiles(new Set())
    } else {
      setSelectedFiles(new Set(uploadedFiles))
    }
  }

  const loadHistory = async () => {
    try {
      const data = await api('/api/conversations')
      if (data && data.conversations) {
        setConversations(data.conversations)
        return data.conversations
      }
    } catch (e) {
      console.error('Error loading history:', e)
    }
    return []
  }

  const initUserSession = async (loggedInUser) => {
    setUser(loggedInUser)
    try {
      await loadHistory()
      const created = await api('/api/conversations', { method: 'POST' })
      setConversationId(created.conversation_id)
      setActiveRecentId(null)
      setMessages([])
    } catch (e) {
      console.error(e)
    }
    await loadFiles()
  }

  useEffect(() => {
    api('/api/session')
      .then(async ({ user }) => {
        if (user) {
          await initUserSession(user)
        }
      })
      .catch(() => {
        // Not logged in or offline
      })
      .finally(() => {
        setSessionChecked(true)
      })
  }, [])

  const handleLoginSuccess = async (userData) => {
    await initUserSession(userData)
  }

  const startNewChat = async () => {
    setMessages([])
    setPrompt('')
    setActiveRecentId(null)
    if (user) {
      try {
        const data = await api('/api/conversations', { method: 'POST' })
        setConversationId(data.conversation_id)
        await loadHistory()
      } catch (e) {
        console.error(e)
      }
    } else {
      setConversationId(null)
    }
    setTimeout(() => inputRef.current?.focus(), 50)
  }

  const openConversation = async (item) => {
    setActiveRecentId(item.id)
    if (item.isDefault) {
      setConversationId(null)
      setMessages([
        { role: 'user', content: `Opening sample topic: ${item.title}` },
        { role: 'assistant', content: `Here is the details regarding "${item.title}". You can ask any question or upload documents to explore this context.` }
      ])
      return
    }

    try {
      const data = await api(`/api/conversations/${item.id}/messages`)
      setConversationId(item.id)
      setMessages(data.messages || [])
    } catch (err) {
      setNotice('Could not load messages.')
    }
  }

  const signOut = async () => {
    try {
      await api('/api/auth/logout', { method: 'POST' })
    } catch (e) {}
    setUser(null)
    setConversationId(null)
    setMessages([])
    setConversations([])
    setPrompt('')
  }

  const sendMessage = async (event) => {
    event?.preventDefault()
    const question = prompt.trim()
    if (!question || isSending) return

    setPrompt('')
    setMessages((items) => [...items, { role: 'user', content: question }])
    setIsSending(true)

    try {
      let currentConvId = conversationId
      if (!currentConvId) {
        const created = await api('/api/conversations', { method: 'POST' })
        currentConvId = created.conversation_id
        setConversationId(currentConvId)
        setActiveRecentId(currentConvId)
      }
      const data = await api('/api/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          conversation_id: currentConvId,
          question,
          selected_files: selectedFiles.size > 0 ? [...selectedFiles] : null,
        }),
      })
      if (data && data.conversation_id) {
        setConversationId(data.conversation_id)
        setActiveRecentId(data.conversation_id)
      }
      setMessages((items) => [...items, { role: 'assistant', content: data.answer }])
      await loadHistory()
    } catch (error) {
      setMessages((items) => [...items, { role: 'assistant', content: error.message }])
    } finally {
      setIsSending(false)
      inputRef.current?.focus()
    }
  }

  const uploadFiles = async (event) => {
    const files = [...event.target.files]
    if (!files.length) return
    const body = new FormData()
    files.forEach((file) => body.append('files', file))
    setNotice('Processing files…')
    try {
      const data = await api('/api/upload', { method: 'POST', body })
      setNotice(`✅ ${data.files.length} file(s) uploaded & indexed successfully.`)
      await loadFiles()
    } catch (error) {
      setNotice(error.message)
    }
    event.target.value = ''
  }

  const deleteConversation = async (e, item) => {
    e.stopPropagation()
    try {
      await api(`/api/conversations/${item.id}`, { method: 'DELETE' })
      if (item.id === conversationId) {
        setMessages([])
        setConversationId(null)
      }
      await loadHistory()
    } catch (err) {
      setNotice('Could not delete conversation.')
    }
  }

  // If session is still loading
  if (!sessionChecked) {
    return (
      <div className="login-screen loading-screen">
        <div className="loading-spinner"></div>
      </div>
    )
  }

  // If user is not authenticated, show Login landing page first!
  if (!user) {
    return <LoginPage onLogin={handleLoginSuccess} />
  }

  // Real user chat history only
  const allRecents = conversations.map((c) => ({ id: c.id, title: c.title, isDefault: false }))

  const userInitials = user
    ? user.email.slice(0, 2).toUpperCase()
    : ''

  const userName = user
    ? user.email.split('@')[0]
    : ''

  return (
    <div className="app-layout">
      {/* Hidden File Input for attachment icon */}
      <input
        type="file"
        ref={fileInputRef}
        multiple
        style={{ display: 'none' }}
        onChange={uploadFiles}
      />

      {/* LEFT SIDEBAR */}
      <aside className="sidebar">
        {/* Brand / Title Header */}
        <div className="sidebar-header">
          <button className="brand-dropdown-btn">
            <span className="brand-name">File Chatbot</span>
          </button>
          <button
            className="icon-btn"
            title="New chat"
            onClick={startNewChat}
          >
            <svg viewBox="0 0 24 24" width="18" height="18" fill="none" stroke="currentColor" strokeWidth="2">
              <path d="M12 5v14M5 12h14" />
            </svg>
          </button>
        </div>

        {/* Primary Navigation */}
        <nav className="nav-group">
          <button className="nav-item" onClick={startNewChat}>
            <span className="nav-icon">
              <svg viewBox="0 0 24 24" width="18" height="18" fill="none" stroke="currentColor" strokeWidth="2">
                <path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7" />
                <path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z" />
              </svg>
            </span>
            <span className="nav-text">New chat</span>
          </button>
        </nav>


        {/* Recents Section */}
        <div className="sidebar-section recents-section">
          <div className="section-label">Recents</div>
          <div className="recents-list">
            {allRecents.length > 0 ? (
              allRecents.map((item) => {
                const isActive = item.id === activeRecentId
                return (
                  <div
                    key={item.id}
                    className={`recent-item ${isActive ? 'active' : ''}`}
                    onClick={() => openConversation(item)}
                    title={item.title}
                  >
                    <span className="recent-title">{item.title}</span>
                    <button
                      className="recent-delete-btn"
                      title="Delete conversation"
                      onClick={(e) => deleteConversation(e, item)}
                    >
                      <svg viewBox="0 0 24 24" width="13" height="13" fill="none" stroke="currentColor" strokeWidth="2.5">
                        <path d="M18 6L6 18M6 6l12 12" />
                      </svg>
                    </button>
                  </div>
                )
              })
            ) : (
              <div className="empty-recents-text">
                {user ? 'No saved chats yet.' : 'Sign in to save chat history.'}
              </div>
            )}
          </div>
        </div>

        {/* Uploads Section */}
        <div className="sidebar-section uploads-section">
          <div className="uploads-section-header">
            <div className="section-label" style={{ padding: '12px 0 6px' }}>Uploads</div>
            <div className="uploads-header-actions">
              {uploadedFiles.length > 0 && (
                <button
                  className="uploads-select-all-btn"
                  onClick={toggleAllFiles}
                  title={selectedFiles.size === uploadedFiles.length ? 'Deselect all' : 'Select all'}
                >
                  {selectedFiles.size === uploadedFiles.length ? 'None' : 'All'}
                </button>
              )}
              <button
                className="uploads-add-btn"
                title="Upload a file"
                onClick={() => {
                  if (!user) { setShowAuthModal(true); return }
                  fileInputRef.current?.click()
                }}
              >
                <svg viewBox="0 0 24 24" width="13" height="13" fill="none" stroke="currentColor" strokeWidth="2.5">
                  <path d="M12 5v14M5 12h14" />
                </svg>
              </button>
            </div>
          </div>
          {/* Uploaded Files List */}
          <div className="uploads-list">
            {uploadedFiles.length === 0 ? (
              <div className="empty-recents-text">No files uploaded yet.</div>
            ) : (
              uploadedFiles.map((filename) => {
                const isChecked = selectedFiles.has(filename);
                const ext = filename.split('.').pop().toLowerCase();
                const icon = {
                  pdf: '📄', txt: '📝', docx: '📃', doc: '📃',
                  xlsx: '📊', csv: '📊', pptx: '📊',
                  jpg: '🖼️', jpeg: '🖼️', png: '🖼️', webp: '🖼️',
                  json: '🗂️', html: '🌐',
                }[ext] || '📁';
                return (
                  <label
                    key={filename}
                    className={`upload-file-item ${isChecked ? 'checked' : ''}`}
                    title={filename}
                  >
                    <input
                      type="checkbox"
                      className="upload-checkbox"
                      checked={isChecked}
                      onChange={() => toggleFileSelection(filename)}
                    />
                    <span className="upload-file-icon">{icon}</span>
                    <span className="upload-file-name">{filename}</span>
                    {/* Delete button */}
                    <button
                      type="button"
                      className="upload-delete-btn"
                      title="Delete file"
                      onClick={(e) => {
                        e.stopPropagation();
                        deleteFile(filename);
                      }}
                    >
                      ✕
                    </button>
                  </label>
                );
              })
            )}
          </div>
          {selectedFiles.size > 0 && (
            <div className="uploads-filter-badge">
              🔍 Filtering by {selectedFiles.size} file{selectedFiles.size > 1 ? 's' : ''}
            </div>
          )}
        </div>

        {/* User Account Footer */}

        <div className="user-footer">
          <div className="user-info" onClick={() => !user && setShowAuthModal(true)}>
            <div className="user-avatar">
              {user ? (
                userInitials
              ) : (
                <svg viewBox="0 0 24 24" width="16" height="16" fill="none" stroke="currentColor" strokeWidth="2">
                  <path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2" />
                  <circle cx="12" cy="7" r="4" />
                </svg>
              )}
            </div>
            <span className="user-name">{userName}</span>
          </div>
          {user && (
            <button className="signout-btn" title="Sign out" onClick={signOut}>
              ✕
            </button>
          )}
        </div>
      </aside>

      {/* MAIN CONTENT AREA */}
      <section className="main-content">
        {/* Top Header */}
        <header className="top-bar">
          <div className="top-bar-title">File Chatbot</div>
        </header>

        {/* Center Canvas */}
        <div className="chat-canvas">
          {messages.length === 0 ? (
            <div className="empty-hero">
              <h1 className="hero-heading">Ready when you are.</h1>
            </div>
          ) : (
            <div className="messages-container">
              {messages.map((msg, index) => (
                <div key={index} className={`message-row ${msg.role}`}>
                  <div className="message-avatar">
                    {msg.role === 'user' ? userInitials : '✦'}
                  </div>
                  <div className="message-content">
                    {msg.content}
                  </div>
                </div>
              ))}
              {isSending && (
                <div className="message-row assistant">
                  <div className="message-avatar">✦</div>
                  <div className="message-content thinking-indicator">
                    Thinking<span>.</span><span>.</span><span>.</span>
                  </div>
                </div>
              )}
            </div>
          )}
        </div>

        {/* Notice toast */}
        {notice && (
          <div className="toast-notice">
            <span>{notice}</span>
            <button onClick={() => setNotice('')}>✕</button>
          </div>
        )}

        {/* Bottom Floating Composer */}
        <div className="composer-container">
          <form className="composer-pill" onSubmit={sendMessage}>
            {/* Attachment Button */}
            <button
              type="button"
              className="composer-action-btn attach-btn"
              title="Attach files"
              onClick={() => fileInputRef.current?.click()}
            >
              <svg viewBox="0 0 24 24" width="20" height="20" fill="none" stroke="currentColor" strokeWidth="2.2">
                <path d="M12 5v14M5 12h14" />
              </svg>
            </button>

            {/* Input Text Area */}
            <textarea
              ref={inputRef}
              className="composer-input"
              rows={1}
              value={prompt}
              onChange={(e) => setPrompt(e.target.value)}
              onKeyDown={(e) => {
                if (e.key === 'Enter' && !e.shiftKey) {
                  e.preventDefault()
                  sendMessage()
                }
              }}
              placeholder="Message File Chatbot"
            />

            {/* Right Tools Inside Capsule */}
            <div className="composer-tools">

              {/* Send Button */}
              <button
                type="submit"
                className={`send-btn ${prompt.trim() ? 'active' : ''}`}
                disabled={!prompt.trim() || isSending}
                title="Send message"
              >
                <svg viewBox="0 0 24 24" width="18" height="18" fill="none" stroke="currentColor" strokeWidth="2.5">
                  <path d="M12 19V5M5 12l7-7 7 7" />
                </svg>
              </button>
            </div>
          </form>
        </div>
      </section>

      {/* MODALS */}
      {/* Search Modal */}
      {showSearchModal && (
        <div className="modal-backdrop" onClick={() => setShowSearchModal(false)}>
          <div className="modal-card" onClick={(e) => e.stopPropagation()}>
            <div className="modal-header">
              <h3>Search Chats</h3>
              <button className="close-btn" onClick={() => setShowSearchModal(false)}>✕</button>
            </div>
            <input
              type="text"
              className="modal-search-input"
              placeholder="Search history..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              autoFocus
            />
            <div className="search-results-list">
              {allRecents
                .filter((r) => r.title.toLowerCase().includes(searchQuery.toLowerCase()))
                .map((item) => (
                  <button
                    key={item.id}
                    className="search-result-item"
                    onClick={() => {
                      openConversation(item)
                      setShowSearchModal(false)
                    }}
                  >
                    <span>{item.title}</span>
                  </button>
                ))}
            </div>
          </div>
        </div>
      )}

      {/* Get Plus Modal */}
      {showPlusModal && (
        <div className="modal-backdrop" onClick={() => setShowPlusModal(false)}>
          <div className="modal-card plus-modal" onClick={(e) => e.stopPropagation()}>
            <div className="modal-header">
              <h3>Upgrade your plan</h3>
              <button className="close-btn" onClick={() => setShowPlusModal(false)}>✕</button>
            </div>
            <p className="plus-desc">Get unlimited access to advanced document reasoning, faster processing, and priority support.</p>
            <div className="plan-box">
              <h4>ChatGPT Plus / Premium</h4>
              <div className="plan-price">$20 / month</div>
              <ul>
                <li>✓ Access to GPT-4o & Gemini Pro</li>
                <li>✓ Unlimited document uploads</li>
                <li>✓ Priority response times</li>
              </ul>
              <button className="upgrade-confirm-btn" onClick={() => setShowPlusModal(false)}>Upgrade now</button>
            </div>
          </div>
        </div>
      )}

      {/* Scheduled Modal */}
      {showScheduledModal && (
        <div className="modal-backdrop" onClick={() => setShowScheduledModal(false)}>
          <div className="modal-card" onClick={(e) => e.stopPropagation()}>
            <div className="modal-header">
              <h3>Scheduled Actions</h3>
              <button className="close-btn" onClick={() => setShowScheduledModal(false)}>✕</button>
            </div>
            <p>No scheduled tasks active. You can set periodic document summaries or automated prompts.</p>
          </div>
        </div>
      )}

      {/* Plugins Modal */}
      {showPluginsModal && (
        <div className="modal-backdrop" onClick={() => setShowPluginsModal(false)}>
          <div className="modal-card" onClick={(e) => e.stopPropagation()}>
            <div className="modal-header">
              <h3>Plugins & Connectors</h3>
              <button className="close-btn" onClick={() => setShowPluginsModal(false)}>✕</button>
            </div>
            <p>Document OCR, Web Search, Python Code Interpreter, and Vector Store search are active.</p>
          </div>
        </div>
      )}

    </div>
  )
}

createRoot(document.getElementById('root')).render(<App />)

