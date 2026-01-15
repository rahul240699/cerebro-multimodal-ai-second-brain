'use client'

import { useState, useRef, useEffect } from 'react'
import { Send, Loader2 } from 'lucide-react'
import ReactMarkdown from 'react-markdown'

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

interface Message {
  role: 'user' | 'assistant'
  content: string
  chunks?: any[]
  timestamp: Date
}

export default function ChatInterface() {
  const [messages, setMessages] = useState<Message[]>([])
  const [inputValue, setInputValue] = useState('')
  const [isProcessing, setIsProcessing] = useState(false)
  const [statusMessage, setStatusMessage] = useState('')
  const messagesEndRef = useRef<HTMLDivElement>(null)

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }

  useEffect(() => {
    scrollToBottom()
  }, [messages])

  const handleSendMessage = async () => {
    if (!inputValue.trim() || isProcessing) return

    const userMessage: Message = {
      role: 'user',
      content: inputValue,
      timestamp: new Date(),
    }

    setMessages(prev => [...prev, userMessage])
    setInputValue('')
    setIsProcessing(true)
    setStatusMessage('Thinking...')

    // Create placeholder for assistant response
    const assistantMessageIndex = messages.length + 1
    const assistantMessage: Message = {
      role: 'assistant',
      content: '',
      timestamp: new Date(),
    }
    setMessages(prev => [...prev, assistantMessage])

    try {
      // Connect to SSE stream
      const response = await fetch(`${API_URL}/api/query/chat`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          query: userMessage.content,
          top_k: 20,
        }),
      })

      if (!response.ok) {
        throw new Error('Failed to query brain')
      }

      const reader = response.body?.getReader()
      const decoder = new TextDecoder()

      if (!reader) throw new Error('No response stream')

      let accumulatedContent = ''

      while (true) {
        const { done, value } = await reader.read()
        if (done) break

        const chunk = decoder.decode(value)
        const lines = chunk.split('\n')

        for (const line of lines) {
          if (line.startsWith('data: ')) {
            const data = JSON.parse(line.slice(6))

            if (data.type === 'status') {
              setStatusMessage(data.message)
            } else if (data.type === 'chunks') {
              setMessages(prev => {
                const updated = [...prev]
                updated[assistantMessageIndex] = {
                  ...updated[assistantMessageIndex],
                  chunks: data.chunks,
                }
                return updated
              })
            } else if (data.type === 'token') {
              accumulatedContent += data.content
              setMessages(prev => {
                const updated = [...prev]
                updated[assistantMessageIndex] = {
                  ...updated[assistantMessageIndex],
                  content: accumulatedContent,
                }
                return updated
              })
            } else if (data.type === 'done') {
              setStatusMessage('')
              setIsProcessing(false)
            } else if (data.type === 'error') {
              throw new Error(data.message)
            }
          }
        }
      }
    } catch (error) {
      console.error('Query failed:', error)
      setMessages(prev => {
        const updated = [...prev]
        updated[assistantMessageIndex] = {
          ...updated[assistantMessageIndex],
          content: `❌ Error: ${error instanceof Error ? error.message : 'Unknown error'}`,
        }
        return updated
      })
      setIsProcessing(false)
      setStatusMessage('')
    }
  }

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSendMessage()
    }
  }

  return (
    <div className="flex flex-col h-[calc(100vh-12rem)] bg-slate-800/50 rounded-lg border border-slate-700 shadow-xl">
      {/* Messages Area */}
      <div className="flex-1 overflow-y-auto p-6 space-y-6">
        {messages.length === 0 ? (
          <div className="text-center text-slate-400 mt-20">
            <h2 className="text-2xl font-semibold mb-2">Welcome to Cerebro</h2>
            <p>Ask me anything about your knowledge base.</p>
            <p className="text-sm mt-2">I have perfect memory and can answer questions about documents, audio, web content, and images you've uploaded.</p>
          </div>
        ) : (
          messages.map((message, index) => (
            <div
              key={index}
              className={`flex ${message.role === 'user' ? 'justify-end' : 'justify-start'}`}
            >
              <div
                className={`max-w-[80%] rounded-lg p-4 ${
                  message.role === 'user'
                    ? 'bg-cerebro-purple text-white'
                    : 'bg-slate-700 text-slate-100'
                }`}
              >
                {message.role === 'assistant' ? (
                  <div className="prose prose-invert max-w-none">
                    <ReactMarkdown>{message.content}</ReactMarkdown>
                  </div>
                ) : (
                  <p className="whitespace-pre-wrap">{message.content}</p>
                )}

                {/* Show source chunks */}
                {message.chunks && message.chunks.length > 0 && (
                  <div className="mt-3 pt-3 border-t border-slate-600 text-xs text-slate-300">
                    <p className="font-semibold mb-1">Sources:</p>
                    <div className="space-y-1">
                      {message.chunks.slice(0, 3).map((chunk: any, idx: number) => (
                        <div key={idx} className="flex items-center gap-2">
                          <span className="text-cerebro-purple">•</span>
                          <span>{chunk.document_title}</span>
                          <span className="text-slate-400">
                            ({chunk.content_type}, {new Date(chunk.created_at).toLocaleDateString()})
                          </span>
                        </div>
                      ))}
                    </div>
                  </div>
                )}

                <div className="text-xs text-slate-400 mt-2">
                  {message.timestamp.toLocaleTimeString()}
                </div>
              </div>
            </div>
          ))
        )}

        {/* Status Message */}
        {statusMessage && (
          <div className="flex items-center gap-2 text-slate-400 text-sm">
            <Loader2 className="w-4 h-4 animate-spin" />
            <span>{statusMessage}</span>
          </div>
        )}

        <div ref={messagesEndRef} />
      </div>

      {/* Input Area */}
      <div className="border-t border-slate-700 p-4">
        <div className="flex gap-3">
          <input
            type="text"
            value={inputValue}
            onChange={(e) => setInputValue(e.target.value)}
            onKeyPress={handleKeyPress}
            placeholder="Ask me anything..."
            disabled={isProcessing}
            className="flex-1 bg-slate-700 text-white rounded-lg px-4 py-3 focus:outline-none focus:ring-2 focus:ring-cerebro-purple disabled:opacity-50 disabled:cursor-not-allowed"
          />
          <button
            onClick={handleSendMessage}
            disabled={!inputValue.trim() || isProcessing}
            className="bg-cerebro-purple text-white rounded-lg px-6 py-3 font-semibold hover:bg-purple-600 disabled:opacity-50 disabled:cursor-not-allowed transition-all flex items-center gap-2"
          >
            {isProcessing ? (
              <Loader2 className="w-5 h-5 animate-spin" />
            ) : (
              <Send className="w-5 h-5" />
            )}
          </button>
        </div>
      </div>
    </div>
  )
}
