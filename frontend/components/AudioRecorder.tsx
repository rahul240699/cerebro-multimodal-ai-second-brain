'use client'

import { useState, useRef, useEffect } from 'react'
import { Mic, Square, Loader2 } from 'lucide-react'

interface AudioRecorderProps {
  onRecordingComplete: (audioBlob: Blob, filename: string) => void
}

export default function AudioRecorder({ onRecordingComplete }: AudioRecorderProps) {
  const [isRecording, setIsRecording] = useState(false)
  const [audioLevel, setAudioLevel] = useState(0)
  const [duration, setDuration] = useState(0)
  
  const mediaRecorderRef = useRef<MediaRecorder | null>(null)
  const audioChunksRef = useRef<Blob[]>([])
  const audioContextRef = useRef<AudioContext | null>(null)
  const analyserRef = useRef<AnalyserNode | null>(null)
  const animationFrameRef = useRef<number | null>(null)
  const startTimeRef = useRef<number>(0)
  const durationIntervalRef = useRef<NodeJS.Timeout | null>(null)

  useEffect(() => {
    return () => {
      // Cleanup on unmount
      if (animationFrameRef.current) {
        cancelAnimationFrame(animationFrameRef.current)
      }
      if (durationIntervalRef.current) {
        clearInterval(durationIntervalRef.current)
      }
      if (audioContextRef.current) {
        audioContextRef.current.close()
      }
    }
  }, [])

  const startRecording = async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true })
      
      // Setup MediaRecorder
      const mediaRecorder = new MediaRecorder(stream)
      mediaRecorderRef.current = mediaRecorder
      audioChunksRef.current = []

      mediaRecorder.ondataavailable = (event) => {
        if (event.data.size > 0) {
          audioChunksRef.current.push(event.data)
        }
      }

      mediaRecorder.onstop = () => {
        const audioBlob = new Blob(audioChunksRef.current, { type: 'audio/webm' })
        const timestamp = new Date().toISOString().replace(/[:.]/g, '-')
        const filename = `recording-${timestamp}.webm`
        onRecordingComplete(audioBlob, filename)
        
        // Cleanup
        stream.getTracks().forEach(track => track.stop())
      }

      // Setup audio visualization
      const audioContext = new AudioContext()
      audioContextRef.current = audioContext
      
      const analyser = audioContext.createAnalyser()
      analyserRef.current = analyser
      analyser.fftSize = 256
      
      const source = audioContext.createMediaStreamSource(stream)
      source.connect(analyser)

      // Start recording and visualization
      mediaRecorder.start()
      setIsRecording(true)
      startTimeRef.current = Date.now()
      
      // Start duration counter
      durationIntervalRef.current = setInterval(() => {
        setDuration(Math.floor((Date.now() - startTimeRef.current) / 1000))
      }, 1000)
      
      visualize()

    } catch (error) {
      console.error('Error accessing microphone:', error)
      alert('Could not access microphone. Please ensure microphone permissions are granted.')
    }
  }

  const stopRecording = () => {
    if (mediaRecorderRef.current && isRecording) {
      mediaRecorderRef.current.stop()
      setIsRecording(false)
      setAudioLevel(0)
      setDuration(0)
      
      if (animationFrameRef.current) {
        cancelAnimationFrame(animationFrameRef.current)
      }
      
      if (durationIntervalRef.current) {
        clearInterval(durationIntervalRef.current)
      }
      
      if (audioContextRef.current) {
        audioContextRef.current.close()
      }
    }
  }

  const visualize = () => {
    if (!analyserRef.current) return

    const analyser = analyserRef.current
    const dataArray = new Uint8Array(analyser.frequencyBinCount)

    const updateLevel = () => {
      analyser.getByteFrequencyData(dataArray)
      
      // Calculate average audio level
      const average = dataArray.reduce((a, b) => a + b) / dataArray.length
      const normalizedLevel = Math.min(100, (average / 255) * 100)
      
      setAudioLevel(normalizedLevel)
      animationFrameRef.current = requestAnimationFrame(updateLevel)
    }

    updateLevel()
  }

  const formatDuration = (seconds: number) => {
    const mins = Math.floor(seconds / 60)
    const secs = seconds % 60
    return `${mins}:${secs.toString().padStart(2, '0')}`
  }

  return (
    <div className="space-y-4">
      {/* Waveform Visualization */}
      {isRecording && (
        <div className="flex items-center justify-center gap-1 h-20 bg-gray-800/50 rounded-lg px-4">
          {Array.from({ length: 40 }).map((_, i) => {
            // Create wave effect based on audio level and position
            const delay = i * 0.05
            const height = Math.max(
              4,
              Math.sin((Date.now() / 200 + delay) * Math.PI) * audioLevel * 0.8 + 20
            )
            
            return (
              <div
                key={i}
                className="w-1 bg-gradient-to-t from-purple-500 to-pink-500 rounded-full transition-all duration-100"
                style={{
                  height: `${height}%`,
                  opacity: 0.7 + (audioLevel / 200)
                }}
              />
            )
          })}
        </div>
      )}

      {/* Recording Controls */}
      <div className="flex items-center justify-center gap-4">
        {!isRecording ? (
          <button
            onClick={startRecording}
            className="flex items-center gap-2 px-6 py-3 bg-red-600 hover:bg-red-700 text-white rounded-lg transition-colors"
          >
            <Mic className="w-5 h-5" />
            <span>Start Recording</span>
          </button>
        ) : (
          <div className="flex items-center gap-4">
            <div className="flex items-center gap-2 text-red-500">
              <div className="w-3 h-3 bg-red-500 rounded-full animate-pulse" />
              <span className="font-mono text-lg">{formatDuration(duration)}</span>
            </div>
            
            <button
              onClick={stopRecording}
              className="flex items-center gap-2 px-6 py-3 bg-gray-700 hover:bg-gray-600 text-white rounded-lg transition-colors"
            >
              <Square className="w-5 h-5" />
              <span>Stop Recording</span>
            </button>
          </div>
        )}
      </div>

      {/* Instructions */}
      {!isRecording && (
        <p className="text-center text-sm text-gray-400">
          Click to start recording. Your audio will be transcribed and added to your knowledge base.
        </p>
      )}
    </div>
  )
}
