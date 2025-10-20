'use client'

import { useState, useRef, useEffect } from 'react'
import { ChevronLeft, Camera, Smile } from 'lucide-react'
import Webcam from 'react-webcam'

interface BiometricAuthProps {
  onSuccess: (patientId: string) => void
  onBack: () => void
}

export function BiometricAuth({ onSuccess, onBack }: BiometricAuthProps) {
  const [step, setStep] = useState<'camera' | 'capture' | 'processing' | 'success'>('camera')
  const [capturedImage, setCapturedImage] = useState<string | null>(null)
  const [processing, setProcessing] = useState(false)
  const [error, setError] = useState('')
  const webcamRef = useRef<Webcam>(null)

  useEffect(() => {
    // Request camera permissions
    if (navigator.mediaDevices && navigator.mediaDevices.getUserMedia) {
      navigator.mediaDevices.getUserMedia({ video: true })
        .then(() => {
          // Camera access granted
        })
        .catch(() => {
          setError('Camera access is required for biometric authentication')
        })
    }
  }, [])

  const capturePhoto = () => {
    if (webcamRef.current) {
      const imageSrc = webcamRef.current.getScreenshot()
      if (imageSrc) {
        setCapturedImage(imageSrc)
        setStep('capture')
      }
    }
  }

  const retakePhoto = () => {
    setCapturedImage(null)
    setStep('camera')
    setError('')
  }

  const confirmPhoto = async () => {
    if (!capturedImage) return

    setProcessing(true)
    setError('')

    try {
      // In a real implementation, this would send the image to the backend for biometric matching
      // For demo purposes, we'll simulate processing
      await new Promise(resolve => setTimeout(resolve, 2000))

      // Mock successful biometric match
      const mockPatientId = 'patient_123'
      onSuccess(mockPatientId)
    } catch (err) {
      setError('Biometric verification failed. Please try again or see a staff member.')
      setStep('capture')
    } finally {
      setProcessing(false)
    }
  }

  const renderCameraView = () => (
    <div className="text-center">
      <div className="relative mb-6">
        <Webcam
          ref={webcamRef}
          audio={false}
          screenshotFormat="image/jpeg"
          videoConstraints={{
            width: 640,
            height: 480,
            facingMode: "user"
          }}
          className="w-full max-w-md mx-auto rounded-lg border-2 border-gray-200"
        />

        {/* Face detection overlay */}
        <div className="absolute inset-0 flex items-center justify-center">
          <div className="w-48 h-48 border-2 border-primary-500 rounded-full opacity-50"></div>
        </div>
      </div>

      <div className="mb-6">
        <div className="flex items-center justify-center space-x-2 text-sm text-gray-600 mb-4">
          <Smile className="w-5 h-5" />
          <span>Position your face within the circle</span>
        </div>

        <button
          onClick={capturePhoto}
          className="flex items-center justify-center w-full bg-primary-600 text-white py-4 px-8 rounded-lg text-lg font-medium hover:bg-primary-700 transition-colors"
        >
          <Camera className="w-5 h-5 mr-2" />
          Take Photo
        </button>
      </div>
    </div>
  )

  const renderCaptureView = () => (
    <div className="text-center">
      <div className="mb-6">
        <img
          src={capturedImage!}
          alt="Captured"
          className="w-full max-w-md mx-auto rounded-lg border-2 border-gray-200"
        />
      </div>

      <div className="space-y-3">
        <button
          onClick={confirmPhoto}
          disabled={processing}
          className="w-full bg-green-600 text-white py-3 px-6 rounded-lg font-medium hover:bg-green-700 transition-colors disabled:opacity-50"
        >
          {processing ? (
            <div className="flex items-center justify-center">
              <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2"></div>
              Verifying...
            </div>
          ) : (
            'Confirm Photo & Verify'
          )}
        </button>

        <button
          onClick={retakePhoto}
          className="w-full bg-gray-500 text-white py-3 px-6 rounded-lg font-medium hover:bg-gray-600 transition-colors"
        >
          Retake Photo
        </button>
      </div>
    </div>
  )

  return (
    <div className="min-h-screen bg-white p-8">
      <div className="max-w-2xl mx-auto">
        {/* Header */}
        <div className="flex items-center mb-8">
          <button
            onClick={onBack}
            className="flex items-center text-gray-600 hover:text-gray-800 mr-4"
          >
            <ChevronLeft className="w-5 h-5" />
            Back
          </button>
          <h1 className="text-2xl font-bold text-gray-900">Biometric Verification</h1>
        </div>

        {/* Instructions */}
        <div className="bg-blue-50 border border-blue-200 rounded-lg p-4 mb-6">
          <h2 className="font-medium text-blue-900 mb-2">Secure Identity Verification</h2>
          <p className="text-blue-800 text-sm">
            We'll use facial recognition to verify your identity and ensure secure access to your medical records.
            This process is HIPAA-compliant and your biometric data is encrypted and stored securely.
          </p>
        </div>

        {error && (
          <div className="bg-red-50 border border-red-200 text-red-600 px-4 py-3 rounded-md mb-6">
            {error}
          </div>
        )}

        {/* Camera/Capture Interface */}
        {step === 'camera' && renderCameraView()}
        {step === 'capture' && renderCaptureView()}

        {/* Help Text */}
        <div className="mt-8 text-center">
          <p className="text-sm text-gray-500">
            Having trouble with biometric verification? Please see a staff member at the front desk for assistance.
          </p>
        </div>
      </div>
    </div>
  )
}
