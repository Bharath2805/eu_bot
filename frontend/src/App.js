import React, { useState, useRef, useEffect } from 'react';

import { Send, Upload, Trash2, Loader2, X, FileText } from 'lucide-react';
import './App.css';

function App() {
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const [conversationId] = useState(() => `conv_${Date.now()}`);
  const [uploadedFiles, setUploadedFiles] = useState([]);
  const messagesEndRef = useRef(null);
  const fileInputRef = useRef(null);

  const API_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

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
        return {
          name: file.name,
          file_id: data.file_id
        };
      });

      const uploadedData = await Promise.all(uploadPromises);
      
      setUploadedFiles(prev => [...prev, ...uploadedData]);
      
      const fileNames = uploadedData.map(f => f.name).join(', ');
      setMessages(prev => [...prev, {
        role: 'system',
        content: `📄 Document uploaded: ${fileNames}`,
        timestamp: new Date().toISOString()
      }]);
    } catch (error) {
      console.error('Upload error:', error);
      alert('Failed to upload one or more files');
    } finally {
      setLoading(false);
      if (fileInputRef.current) {
        fileInputRef.current.value = '';
      }
    }
  };

  const removeFile = (index) => {
    setUploadedFiles(prev => prev.filter((_, i) => i !== index));
  };

  const sendMessage = async () => {
    if (!input.trim()) return;

    const userMessage = {
      role: 'user',
      content: input,
      timestamp: new Date().toISOString()
    };

    setMessages(prev => [...prev, userMessage]);
    const currentInput = input;
    const currentFileIds = uploadedFiles.map(f => f.file_id);
    
    setInput('');
    setLoading(true);

    try {
      const response = await fetch(`${API_URL}/api/chat`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          conversation_id: conversationId,
          message: currentInput,
          uploaded_file_ids: currentFileIds.length > 0 ? currentFileIds : null
        }),
      });

      if (!response.ok) throw new Error('Failed to send message');

      const data = await response.json();
      
      const assistantMessage = {
        role: 'assistant',
        content: data.message,
        timestamp: data.timestamp,
        sources: data.sources,
        used_vector_store: data.used_vector_store,
        used_uploaded_files: data.used_uploaded_files,
        used_web_search: data.used_web_search,
        web_search_results: data.web_search_results
      };

      setMessages(prev => [...prev, assistantMessage]);
      
      // Clear uploaded files after first use
      if (uploadedFiles.length > 0) {
        setUploadedFiles([]);
      }
    } catch (error) {
      console.error('Chat error:', error);
      setMessages(prev => [...prev, {
        role: 'error',
        content: 'Failed to get response. Please try again.',
        timestamp: new Date().toISOString()
      }]);
    } finally {
      setLoading(false);
    }
  };

  const clearChat = async () => {
    try {
      await fetch(`${API_URL}/api/conversation/${conversationId}`, {
        method: 'DELETE',
      });
      setMessages([]);
      setUploadedFiles([]);
      if (fileInputRef.current) {
        fileInputRef.current.value = '';
      }
    } catch (error) {
      console.error('Clear chat error:', error);
    }
  };

  const handleKeyPress = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  };

  const formatMessage = (text) => {
    if (!text) return '';
    
    // Split into lines for better processing
    const lines = text.split('\n');
    let result = [];
    let inList = false;
    let currentParagraph = [];
    
    for (let i = 0; i < lines.length; i++) {
      const line = lines[i].trim();
      
      // Headers
      if (line.match(/^### /)) {
        if (inList) {
          result.push('</ul>');
          inList = false;
        }
        if (currentParagraph.length > 0) {
          result.push('<p>' + currentParagraph.join(' ') + '</p>');
          currentParagraph = [];
        }
        result.push('<h3>' + line.replace(/^### /, '') + '</h3>');
        continue;
      }
      if (line.match(/^## /)) {
        if (inList) {
          result.push('</ul>');
          inList = false;
        }
        if (currentParagraph.length > 0) {
          result.push('<p>' + currentParagraph.join(' ') + '</p>');
          currentParagraph = [];
        }
        result.push('<h2>' + line.replace(/^## /, '') + '</h2>');
        continue;
      }
      if (line.match(/^# /)) {
        if (inList) {
          result.push('</ul>');
          inList = false;
        }
        if (currentParagraph.length > 0) {
          result.push('<p>' + currentParagraph.join(' ') + '</p>');
          currentParagraph = [];
        }
        result.push('<h1>' + line.replace(/^# /, '') + '</h1>');
        continue;
      }
      
      // Lists
      const listMatch = line.match(/^(\d+\.|[-*])\s+(.+)$/);
      if (listMatch) {
        if (currentParagraph.length > 0) {
          result.push('<p>' + currentParagraph.join(' ') + '</p>');
          currentParagraph = [];
        }
        if (!inList) {
          result.push('<ul>');
          inList = true;
        }
        let listContent = listMatch[2];
        // Process bold in list items
        listContent = listContent.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');
        result.push('<li>' + listContent + '</li>');
        continue;
      }
      
      // Empty line
      if (line === '') {
        if (inList) {
          result.push('</ul>');
          inList = false;
        }
        if (currentParagraph.length > 0) {
          result.push('<p>' + currentParagraph.join(' ') + '</p>');
          currentParagraph = [];
        }
        continue;
      }
      
      // Regular text - process bold
      let processedLine = line.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');
      currentParagraph.push(processedLine);
    }
    
    // Close any open structures
    if (inList) {
      result.push('</ul>');
    }
    if (currentParagraph.length > 0) {
      result.push('<p>' + currentParagraph.join(' ') + '</p>');
    }
    
    return result.join('\n');
  };

  return (
    <div className="app-container">
      <div className="header">
        <div className="header-content">
          <div>
            <h1 className="title">EU AI Act Compliance Assistant</h1>
            <p className="subtitle">Your intelligent compliance expert</p>
          </div>
          <button onClick={clearChat} className="clear-button">
            <Trash2 className="icon" />
            Clear Chat
          </button>
        </div>
      </div>

      <div className="messages-container">
        <div className="messages-content">
          
          {messages.map((msg, idx) => (
            <div
              key={idx}
              className={`message-wrapper ${msg.role === 'user' ? 'user' : 'assistant'}`}
            >
              <div className={`message ${msg.role}`}>
                <div className="message-text" dangerouslySetInnerHTML={{__html: formatMessage(msg.content)}}></div>
                <div className="message-footer">
                  <p className="timestamp">
                    {new Date(msg.timestamp).toLocaleTimeString()}
                  </p>
                  {msg.role === 'assistant' && (msg.used_vector_store || msg.used_uploaded_files || msg.used_web_search) && (
                    <div className="source-info">
                      {msg.used_vector_store && (
                        <span className="source-badge vector-store">
                          📚 Vector Store
                        </span>
                      )}
                      {msg.used_uploaded_files && (
                        <span className="source-badge uploaded-files">
                          📎 Uploaded Files
                        </span>
                      )}
                      {msg.used_web_search && (
                        <span className="source-badge web-search">
                          🌐 Web Search
                        </span>
                      )}
                      {(msg.sources && msg.sources.length > 0) || (msg.web_search_results && msg.web_search_results.length > 0) && (
                        <span className="source-count">
                          ({((msg.sources?.length || 0) + (msg.web_search_results?.length || 0))} source{((msg.sources?.length || 0) + (msg.web_search_results?.length || 0)) > 1 ? 's' : ''})
                        </span>
                      )}
                    </div>
                  )}
                  {msg.role === 'assistant' && msg.web_search_results && msg.web_search_results.length > 0 && (
                    <div className="web-search-results">
                      <p className="web-results-title">Web Sources:</p>
                      {msg.web_search_results.map((result, idx) => (
                        <a
                          key={idx}
                          href={result.url}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="web-result-link"
                        >
                          {result.title || result.url}
                        </a>
                      ))}
                    </div>
                  )}
                </div>
              </div>
            </div>
          ))}
          
          {loading && (
            <div className="message-wrapper assistant">
              <div className="message assistant">
                <Loader2 className="loading-icon" />
                <span className="loading-text">Analyzing your query and searching knowledge base...</span>
              </div>
            </div>
          )}
          
          <div ref={messagesEndRef} />
        </div>
      </div>

      <div className="input-container">
        <div className="input-content">
          {uploadedFiles.length > 0 && (
            <div className="files-container">
              <div className="files-header">
                <span className="files-count">
                  📎 {uploadedFiles.length} file(s) attached
                </span>
                <button
                  onClick={() => setUploadedFiles([])}
                  className="clear-all-files"
                >
                  Clear all
                </button>
              </div>
              <div className="files-list">
                {uploadedFiles.map((file, index) => (
                  <div key={index} className="file-badge">
                    <FileText className="icon-small" />
                    <span>{file.name}</span>
                    <button
                      onClick={() => removeFile(index)}
                      className="remove-file"
                    >
                      <X className="icon-small" />
                    </button>
                  </div>
                ))}
              </div>
            </div>
          )}
          
          <div className="input-row">
            <input
              type="file"
              ref={fileInputRef}
              onChange={handleFileUpload}
              accept=".pdf,.txt,.doc,.docx"
              multiple
              className="file-input"
            />
            
            <button
              onClick={() => fileInputRef.current?.click()}
              disabled={loading}
              className="upload-button"
              title="Upload files to search"
            >
              <Upload className="icon" />
            </button>
            
            <input
              type="text"
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyPress={handleKeyPress}
              placeholder="Ask anything... files will be searched automatically"
              disabled={loading}
              className="text-input"
            />
            
            <button
              onClick={sendMessage}
              disabled={loading || !input.trim()}
              className="send-button"
            >
              <Send className="icon" />
              Send
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}

export default App;
