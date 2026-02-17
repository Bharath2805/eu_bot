import React, { useState, useRef, useEffect, useCallback } from 'react';
import { Send, Upload, Loader2, X, FileText, MessageSquare, Plus, Scale, Shield } from 'lucide-react';
import './App.css';

function App() {
  // Chat state
  const [chats, setChats] = useState(() => {
    const initialId = `conv_${Date.now()}`;
    return {
      [initialId]: {
        id: initialId,
        title: 'New conversation',
        messages: [],
        uploadedFiles: []
      }
    };
  });
  const [activeChat, setActiveChat] = useState(() => Object.keys(chats)[0]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);

  const messagesEndRef = useRef(null);
  const fileInputRef = useRef(null);

  const API_URL = process.env.REACT_APP_API_URL || 'http://localhost:8005';

  // Derived state
  const currentChat = chats[activeChat] || { messages: [], uploadedFiles: [], title: 'New conversation' };
  const messages = currentChat.messages;
  const uploadedFiles = currentChat.uploadedFiles;

  const scrollToBottom = useCallback(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, []);

  useEffect(() => {
    scrollToBottom();
  }, [messages, scrollToBottom]);

  // Update chat title based on first user message
  const updateChatTitle = useCallback((chatId, firstMessage) => {
    const title = firstMessage.length > 28
      ? firstMessage.substring(0, 28) + '...'
      : firstMessage;
    setChats(prev => ({
      ...prev,
      [chatId]: { ...prev[chatId], title }
    }));
  }, []);

  const setMessages = useCallback((updater) => {
    setChats(prev => {
      const current = prev[activeChat];
      const newMessages = typeof updater === 'function'
        ? updater(current.messages)
        : updater;
      return {
        ...prev,
        [activeChat]: { ...current, messages: newMessages }
      };
    });
  }, [activeChat]);

  const setUploadedFiles = useCallback((updater) => {
    setChats(prev => {
      const current = prev[activeChat];
      const newFiles = typeof updater === 'function'
        ? updater(current.uploadedFiles)
        : updater;
      return {
        ...prev,
        [activeChat]: { ...current, uploadedFiles: newFiles }
      };
    });
  }, [activeChat]);

  const handleFileUpload = async (e) => {
    const files = Array.from(e.target.files);
    if (files.length === 0) return;

    setLoading(true);
    try {
      const uploadPromises = files.map(async (file) => {
        const formData = new FormData();
        formData.append('file', file);

        const response = await fetch(`${API_URL}/api/upload`, {
          method: 'POST',
          body: formData,
        });

        if (!response.ok) throw new Error(`Failed to upload ${file.name}`);

        const data = await response.json();
        return { name: file.name, file_id: data.file_id };
      });

      const uploadedData = await Promise.all(uploadPromises);
      setUploadedFiles(prev => [...prev, ...uploadedData]);

      const fileNames = uploadedData.map(f => f.name).join(', ');
      setMessages(prev => [...prev, {
        role: 'system',
        content: `📄 Uploaded: ${fileNames}`,
        timestamp: new Date().toISOString()
      }]);
    } catch (error) {
      console.error('Upload error:', error);
    } finally {
      setLoading(false);
      if (fileInputRef.current) fileInputRef.current.value = '';
    }
  };

  const removeFile = (index) => {
    setUploadedFiles(prev => prev.filter((_, i) => i !== index));
  };

  const sendMessage = async () => {
    if (!input.trim() || loading) return;

    const userMessage = {
      role: 'user',
      content: input,
      timestamp: new Date().toISOString()
    };

    // Update title on first user message
    if (messages.filter(m => m.role === 'user').length === 0) {
      updateChatTitle(activeChat, input);
    }

    setMessages(prev => [...prev, userMessage]);

    const placeholderMessage = {
      role: 'assistant',
      content: '',
      timestamp: new Date().toISOString(),
      loading: true
    };
    setMessages(prev => [...prev, placeholderMessage]);

    const currentInput = input;
    const currentFileIds = uploadedFiles.map(f => f.file_id);

    setInput('');
    setLoading(true);

    try {
      const response = await fetch(`${API_URL}/api/chat/stream`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          conversation_id: activeChat,
          thread_id: null,
          message: currentInput,
          uploaded_file_ids: currentFileIds.length > 0 ? currentFileIds : null
        }),
      });

      if (!response.ok) throw new Error('Failed to send message');

      const reader = response.body.getReader();
      const decoder = new TextDecoder();
      let assistantContent = '';
      let streamDone = false;

      while (!streamDone) {
        const { done, value } = await reader.read();
        if (done) break;

        const chunk = decoder.decode(value, { stream: true });
        const lines = chunk.split('\n');

        for (const line of lines) {
          if (line.startsWith('data: ')) {
            const dataStr = line.slice(6);
            if (dataStr === '[DONE]') {
              streamDone = true;
              break;
            }

            try {
              const data = JSON.parse(dataStr);
              if (data.type === 'text') {
                assistantContent += data.content;
                const currentContent = assistantContent;
                setMessages(prev => {
                  const newMessages = [...prev];
                  const lastMsg = { ...newMessages[newMessages.length - 1] };
                  lastMsg.content = currentContent;
                  lastMsg.loading = false;
                  newMessages[newMessages.length - 1] = lastMsg;
                  return newMessages;
                });
              }
            } catch (e) {
              console.error('Error parsing stream', e);
            }
          }
        }
      }

      if (uploadedFiles.length > 0) {
        setUploadedFiles([]);
      }
    } catch (error) {
      console.error('Chat error:', error);
      setMessages(prev => {
        const newMessages = [...prev];
        newMessages[newMessages.length - 1] = {
          role: 'error',
          content: 'Connection failed. Please try again.',
          timestamp: new Date().toISOString()
        };
        return newMessages;
      });
    } finally {
      setLoading(false);
    }
  };

  const startNewChat = () => {
    const newId = `conv_${Date.now()}`;
    setChats(prev => ({
      ...prev,
      [newId]: {
        id: newId,
        title: 'New conversation',
        messages: [],
        uploadedFiles: []
      }
    }));
    setActiveChat(newId);
    setInput('');
  };

  const switchChat = (chatId) => {
    if (chatId !== activeChat) {
      setActiveChat(chatId);
      setInput('');
    }
  };

  const deleteChat = (chatId, e) => {
    e.stopPropagation();
    const chatIds = Object.keys(chats);

    if (chatIds.length === 1) {
      // If only one chat, just clear it
      startNewChat();
    } else {
      // Remove chat and switch to another
      const newChats = { ...chats };
      delete newChats[chatId];
      setChats(newChats);

      if (activeChat === chatId) {
        const remainingIds = Object.keys(newChats);
        setActiveChat(remainingIds[0]);
      }
    }
  };

  const clearCurrentChat = () => {
    setMessages([]);
    setUploadedFiles([]);
    setChats(prev => ({
      ...prev,
      [activeChat]: { ...prev[activeChat], title: 'New conversation' }
    }));
  };

  const handleKeyPress = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  };

  const formatMessage = (text) => {
    if (!text) return '';

    let html = text
      .replace(/^### (.+)$/gm, '<h3>$1</h3>')
      .replace(/^## (.+)$/gm, '<h2>$1</h2>')
      .replace(/^# (.+)$/gm, '<h1>$1</h1>')
      .replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>')
      .replace(/^[-*] (.+)$/gm, '<li>$1</li>')
      .replace(/^(\d+)\. (.+)$/gm, '<li>$2</li>')
      .replace(/\n\n/g, '</p><p>')
      .replace(/\n/g, '<br/>');

    html = '<p>' + html + '</p>';
    html = html.replace(/(<li>.*?<\/li>)+/gs, '<ul>$&</ul>');

    return html;
  };

  // Get sorted chat list (newest first)
  const chatList = Object.values(chats).sort((a, b) => {
    const aTime = parseInt(a.id.split('_')[1]) || 0;
    const bTime = parseInt(b.id.split('_')[1]) || 0;
    return bTime - aTime;
  });

  return (
    <div className="app">
      {/* Sidebar */}
      <aside className="sidebar">
        <div className="sidebar-header">
          <div className="logo">
            <Scale className="logo-icon" />
            <span>LawMinded</span>
          </div>
        </div>

        <button className="new-chat-btn" onClick={startNewChat}>
          <Plus size={18} />
          <span>New Chat</span>
        </button>

        <div className="chat-history">
          {chatList.map(chat => (
            <div
              key={chat.id}
              className={`chat-history-item ${chat.id === activeChat ? 'active' : ''}`}
              onClick={() => switchChat(chat.id)}
            >
              <MessageSquare size={16} />
              <span>{chat.title}</span>
              {chatList.length > 1 && (
                <button
                  className="delete-chat-btn"
                  onClick={(e) => deleteChat(chat.id, e)}
                  title="Delete chat"
                >
                  <X size={14} />
                </button>
              )}
            </div>
          ))}
        </div>

        <div className="sidebar-footer">
          <div className="compliance-badge">
            <Shield size={14} />
            <span>EU AI Act Expert</span>
          </div>
        </div>
      </aside>

      {/* Main Content */}
      <main className="main">
        {/* Header */}
        <header className="header">
          <div className="header-title">
            <h1>EU AI Act Compliance</h1>
            <p>Your intelligent compliance assistant</p>
          </div>
          <button onClick={clearCurrentChat} className="clear-btn" title="Clear chat">
            <X size={16} />
            <span>Clear</span>
          </button>
        </header>

        {/* Messages */}
        <div className="messages">
          {messages.length === 0 && (
            <div className="welcome">
              <div className="welcome-icon">
                <Scale size={48} />
              </div>
              <h2>How can I help you today?</h2>
              <p>Ask me anything about EU AI Act compliance, risk classification, or documentation requirements.</p>

              <div className="suggestions">
                <button onClick={() => setInput("What is Article 11 technical documentation?")}>
                  📋 Article 11 Requirements
                </button>
                <button onClick={() => setInput("Classify my AI system for HR recruitment")}>
                  ⚖️ Risk Classification
                </button>
                <button onClick={() => setInput("What are high-risk AI categories?")}>
                  🎯 High-Risk Categories
                </button>
              </div>
            </div>
          )}

          {messages.map((msg, idx) => (
            <div key={idx} className={`message-row ${msg.role}`}>
              <div className={`message ${msg.role}`}>
                {msg.role === 'assistant' && (
                  <div className="message-avatar">
                    <Scale size={16} />
                  </div>
                )}
                <div className="message-content">
                  {msg.loading ? (
                    <div className="typing-indicator">
                      <span></span><span></span><span></span>
                    </div>
                  ) : (
                    <div
                      className="message-text"
                      dangerouslySetInnerHTML={{ __html: formatMessage(msg.content) }}
                    />
                  )}
                  <span className="message-time">
                    {new Date(msg.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                  </span>
                </div>
              </div>
            </div>
          ))}

          <div ref={messagesEndRef} />
        </div>

        {/* Input Area */}
        <div className="input-area">
          {uploadedFiles.length > 0 && (
            <div className="attached-files">
              {uploadedFiles.map((file, index) => (
                <div key={index} className="file-chip">
                  <FileText size={14} />
                  <span>{file.name}</span>
                  <button onClick={() => removeFile(index)}>
                    <X size={12} />
                  </button>
                </div>
              ))}
            </div>
          )}

          <div className="input-wrapper">
            <input
              type="file"
              ref={fileInputRef}
              onChange={handleFileUpload}
              accept=".pdf,.txt,.doc,.docx"
              multiple
              hidden
            />

            <button
              className="upload-btn"
              onClick={() => fileInputRef.current?.click()}
              disabled={loading}
              title="Upload files"
            >
              <Upload size={18} />
            </button>

            <input
              type="text"
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyPress={handleKeyPress}
              placeholder="Ask about EU AI Act compliance..."
              disabled={loading}
              className="text-input"
            />

            <button
              className="send-btn"
              onClick={sendMessage}
              disabled={loading || !input.trim()}
              title="Send message"
            >
              {loading ? <Loader2 size={18} className="spin" /> : <Send size={18} />}
            </button>
          </div>
        </div>
      </main>
    </div>
  );
}

export default App;
