'use client'

import { useState } from 'react'
import ChatInterface from '@/components/ChatInterface'
import UploadPanel from '@/components/UploadPanel'
import { Brain } from 'lucide-react'

export default function Home() {
  const [refreshTrigger, setRefreshTrigger] = useState(0)

  const handleUploadComplete = () => {
    // Trigger refresh in chat interface if needed
    setRefreshTrigger(prev => prev + 1)
  }

  return (
    <main className="min-h-screen flex flex-col bg-gradient-to-br from-cerebro-darker to-cerebro-dark">
      {/* Header */}
      <header className="border-b border-slate-700 bg-slate-900/50 backdrop-blur-sm">
        <div className="container mx-auto px-4 py-4 flex items-center gap-3">
          <Brain className="w-8 h-8 text-cerebro-purple animate-pulse-slow" />
          <div>
            <h1 className="text-2xl font-bold text-white">Cerebro</h1>
            <p className="text-sm text-slate-400">Your AI Second Brain</p>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <div className="flex-1 container mx-auto px-4 py-6 grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Chat Interface - Takes more space */}
        <div className="lg:col-span-2">
          <ChatInterface key={refreshTrigger} />
        </div>

        {/* Upload Panel - Sidebar */}
        <div className="lg:col-span-1">
          <UploadPanel onUploadComplete={handleUploadComplete} />
        </div>
      </div>
    </main>
  )
}
