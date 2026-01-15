'use client'

import { useState } from 'react'
import { useDropzone } from 'react-dropzone'
import { Upload, Mic, FileText, Globe, Image, CheckCircle2, Loader2, XCircle } from 'lucide-react'
import axios from 'axios'
import AudioRecorder from './AudioRecorder'

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

interface UploadPanelProps {
  onUploadComplete?: () => void
}

type UploadType = 'audio' | 'document' | 'web' | 'image'

interface UploadStatus {
  type: UploadType
  name: string
  status: 'uploading' | 'processing' | 'completed' | 'failed'
  message?: string
  documentId?: number
}

export default function UploadPanel({ onUploadComplete }: UploadPanelProps) {
  const [activeTab, setActiveTab] = useState<UploadType>('document')
  const [webUrl, setWebUrl] = useState('')
  const [uploads, setUploads] = useState<UploadStatus[]>([])

  const handleFileUpload = async (files: File[], type: UploadType) => {
    for (const file of files) {
      const uploadStatus: UploadStatus = {
        type,
        name: file.name,
        status: 'uploading',
      }

      setUploads(prev => [...prev, uploadStatus])
      const uploadIndex = uploads.length

      try {
        const formData = new FormData()
        formData.append('file', file)
        formData.append('title', file.name)

        const endpoint = type === 'audio' ? '/api/ingest/audio' :
                        type === 'document' ? '/api/ingest/document' :
                        '/api/ingest/image'

        const response = await axios.post(`${API_URL}${endpoint}`, formData, {
          headers: {
            'Content-Type': 'multipart/form-data',
          },
        })

        const documentId = response.data.document_id

        // Update to processing
        setUploads(prev => {
          const updated = [...prev]
          updated[uploadIndex] = {
            ...updated[uploadIndex],
            status: 'processing',
            documentId,
          }
          return updated
        })

        // Poll for completion
        pollDocumentStatus(documentId, uploadIndex)

      } catch (error) {
        setUploads(prev => {
          const updated = [...prev]
          updated[uploadIndex] = {
            ...updated[uploadIndex],
            status: 'failed',
            message: error instanceof Error ? error.message : 'Upload failed',
          }
          return updated
        })
      }
    }
  }

  const handleRecordingComplete = async (audioBlob: Blob, filename: string) => {
    // Convert blob to File
    const file = new File([audioBlob], filename, { type: 'audio/webm' })
    await handleFileUpload([file], 'audio')
  }

  const pollDocumentStatus = async (documentId: number, uploadIndex: number) => {
    const maxAttempts = 60 // 5 minutes max
    let attempts = 0

    const poll = setInterval(async () => {
      attempts++

      try {
        const response = await axios.get(`${API_URL}/api/ingest/status/${documentId}`)
        const status = response.data.status

        if (status === 'completed') {
          clearInterval(poll)
          setUploads(prev => {
            const updated = [...prev]
            updated[uploadIndex] = {
              ...updated[uploadIndex],
              status: 'completed',
            }
            return updated
          })
          onUploadComplete?.()
        } else if (status === 'failed') {
          clearInterval(poll)
          setUploads(prev => {
            const updated = [...prev]
            updated[uploadIndex] = {
              ...updated[uploadIndex],
              status: 'failed',
              message: response.data.error_message || 'Processing failed',
            }
            return updated
          })
        }

        if (attempts >= maxAttempts) {
          clearInterval(poll)
        }
      } catch (error) {
        console.error('Status poll failed:', error)
      }
    }, 5000) // Poll every 5 seconds
  }

  const handleWebSubmit = async () => {
    if (!webUrl.trim()) return

    const uploadStatus: UploadStatus = {
      type: 'web',
      name: webUrl,
      status: 'uploading',
    }

    setUploads(prev => [...prev, uploadStatus])
    const uploadIndex = uploads.length

    try {
      const response = await axios.post(`${API_URL}/api/ingest/web`, {
        url: webUrl,
      })

      const documentId = response.data.document_id

      setUploads(prev => {
        const updated = [...prev]
        updated[uploadIndex] = {
          ...updated[uploadIndex],
          status: 'processing',
          documentId,
        }
        return updated
      })

      setWebUrl('')
      pollDocumentStatus(documentId, uploadIndex)

    } catch (error) {
      setUploads(prev => {
        const updated = [...prev]
        updated[uploadIndex] = {
          ...updated[uploadIndex],
          status: 'failed',
          message: error instanceof Error ? error.message : 'Failed to ingest URL',
        }
        return updated
      })
    }
  }

  const { getRootProps: getAudioProps, getInputProps: getAudioInputProps } = useDropzone({
    onDrop: (files) => handleFileUpload(files, 'audio'),
    accept: {
      'audio/*': ['.mp3', '.m4a', '.wav', '.ogg'],
    },
    multiple: true,
  })

  const { getRootProps: getDocProps, getInputProps: getDocInputProps } = useDropzone({
    onDrop: (files) => handleFileUpload(files, 'document'),
    accept: {
      'application/pdf': ['.pdf'],
      'text/markdown': ['.md', '.markdown'],
    },
    multiple: true,
  })

  const { getRootProps: getImageProps, getInputProps: getImageInputProps } = useDropzone({
    onDrop: (files) => handleFileUpload(files, 'image'),
    accept: {
      'image/*': ['.jpg', '.jpeg', '.png', '.webp'],
    },
    multiple: true,
  })

  const renderUploadArea = () => {
    switch (activeTab) {
      case 'audio':
        return (
          <div className="space-y-6">
            {/* Audio Recorder */}
            <AudioRecorder onRecordingComplete={handleRecordingComplete} />
            
            {/* Divider */}
            <div className="flex items-center gap-3">
              <div className="flex-1 h-px bg-slate-600" />
              <span className="text-sm text-slate-400">OR</span>
              <div className="flex-1 h-px bg-slate-600" />
            </div>
            
            {/* File Upload */}
            <div
              {...getAudioProps()}
              className="border-2 border-dashed border-slate-600 rounded-lg p-8 text-center cursor-pointer hover:border-cerebro-purple hover:bg-slate-700/30 transition-all"
            >
              <input {...getAudioInputProps()} />
              <Upload className="w-12 h-12 mx-auto mb-3 text-slate-400" />
              <p className="text-slate-300 mb-1">Drop audio files here or click to browse</p>
              <p className="text-sm text-slate-400">Supports: MP3, M4A, WAV, OGG, WebM</p>
            </div>
          </div>
        )

      case 'document':
        return (
          <div
            {...getDocProps()}
            className="border-2 border-dashed border-slate-600 rounded-lg p-8 text-center cursor-pointer hover:border-cerebro-purple hover:bg-slate-700/30 transition-all"
          >
            <input {...getDocInputProps()} />
            <FileText className="w-12 h-12 mx-auto mb-3 text-slate-400" />
            <p className="text-slate-300 mb-1">Drop documents here or click to browse</p>
            <p className="text-sm text-slate-400">Supports: PDF, Markdown</p>
          </div>
        )

      case 'web':
        return (
          <div className="space-y-3">
            <div className="flex items-center gap-2 text-slate-300 mb-4">
              <Globe className="w-6 h-6" />
              <span className="font-semibold">Ingest Web Content</span>
            </div>
            <input
              type="url"
              value={webUrl}
              onChange={(e) => setWebUrl(e.target.value)}
              placeholder="https://example.com/article"
              className="w-full bg-slate-700 text-white rounded-lg px-4 py-3 focus:outline-none focus:ring-2 focus:ring-cerebro-purple"
            />
            <button
              onClick={handleWebSubmit}
              disabled={!webUrl.trim()}
              className="w-full bg-cerebro-purple text-white rounded-lg px-4 py-3 font-semibold hover:bg-purple-600 disabled:opacity-50 disabled:cursor-not-allowed transition-all"
            >
              Scrape & Ingest
            </button>
          </div>
        )

      case 'image':
        return (
          <div
            {...getImageProps()}
            className="border-2 border-dashed border-slate-600 rounded-lg p-8 text-center cursor-pointer hover:border-cerebro-purple hover:bg-slate-700/30 transition-all"
          >
            <input {...getImageInputProps()} />
            <Image className="w-12 h-12 mx-auto mb-3 text-slate-400" />
            <p className="text-slate-300 mb-1">Drop images here or click to browse</p>
            <p className="text-sm text-slate-400">Supports: JPG, PNG, WebP</p>
          </div>
        )
    }
  }

  return (
    <div className="bg-slate-800/50 rounded-lg border border-slate-700 shadow-xl p-6">
      <h2 className="text-xl font-bold text-white mb-4 flex items-center gap-2">
        <Upload className="w-6 h-6 text-cerebro-purple" />
        Feed Your Brain
      </h2>

      {/* Tabs */}
      <div className="flex gap-2 mb-6 border-b border-slate-700">
        {[
          { type: 'document' as UploadType, icon: FileText, label: 'Docs' },
          { type: 'audio' as UploadType, icon: Mic, label: 'Audio' },
          { type: 'web' as UploadType, icon: Globe, label: 'Web' },
          { type: 'image' as UploadType, icon: Image, label: 'Images' },
        ].map(({ type, icon: Icon, label }) => (
          <button
            key={type}
            onClick={() => setActiveTab(type)}
            className={`flex items-center gap-2 px-4 py-2 border-b-2 transition-all ${
              activeTab === type
                ? 'border-cerebro-purple text-white'
                : 'border-transparent text-slate-400 hover:text-white'
            }`}
          >
            <Icon className="w-4 h-4" />
            <span className="text-sm font-medium">{label}</span>
          </button>
        ))}
      </div>

      {/* Upload Area */}
      <div className="mb-6">{renderUploadArea()}</div>

      {/* Upload Status */}
      {uploads.length > 0 && (
        <div className="space-y-2">
          <h3 className="text-sm font-semibold text-slate-300 mb-2">Recent Uploads</h3>
          {uploads.slice(-5).reverse().map((upload, index) => (
            <div
              key={index}
              className="flex items-center gap-3 bg-slate-700/50 rounded-lg p-3 text-sm"
            >
              {upload.status === 'uploading' && (
                <Loader2 className="w-4 h-4 text-blue-400 animate-spin flex-shrink-0" />
              )}
              {upload.status === 'processing' && (
                <Loader2 className="w-4 h-4 text-yellow-400 animate-spin flex-shrink-0" />
              )}
              {upload.status === 'completed' && (
                <CheckCircle2 className="w-4 h-4 text-green-400 flex-shrink-0" />
              )}
              {upload.status === 'failed' && (
                <XCircle className="w-4 h-4 text-red-400 flex-shrink-0" />
              )}

              <div className="flex-1 min-w-0">
                <p className="text-slate-200 truncate">{upload.name}</p>
                <p className="text-xs text-slate-400">
                  {upload.status === 'uploading' && 'Uploading...'}
                  {upload.status === 'processing' && 'Processing...'}
                  {upload.status === 'completed' && 'Ready to query'}
                  {upload.status === 'failed' && (upload.message || 'Failed')}
                </p>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
