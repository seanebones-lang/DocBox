'use client'

import { useState, useEffect } from 'react'
import { CheckInFlow } from '@/components/CheckInFlow'
import { WelcomeScreen } from '@/components/WelcomeScreen'
import { AppointmentLookup } from '@/components/AppointmentLookup'
import { BiometricAuth } from '@/components/BiometricAuth'
import { CheckInConfirmation } from '@/components/CheckInConfirmation'

type KioskStep = 'welcome' | 'lookup' | 'biometric' | 'confirmation' | 'complete'

interface Appointment {
  id: string
  patient_name: string
  provider_name: string
  scheduled_time: string
  appointment_type: string
  clinic_name: string
}

export default function KioskPage() {
  const [currentStep, setCurrentStep] = useState<KioskStep>('welcome')
  const [appointment, setAppointment] = useState<Appointment | null>(null)
  const [patientId, setPatientId] = useState<string | null>(null)
  const [isOffline, setIsOffline] = useState(false)

  useEffect(() => {
    // Check for offline capability
    if ('serviceWorker' in navigator) {
      navigator.serviceWorker.ready.then(() => {
        // PWA is ready for offline use
      })
    }

    // Listen for online/offline status
    const handleOnline = () => setIsOffline(false)
    const handleOffline = () => setIsOffline(true)

    window.addEventListener('online', handleOnline)
    window.addEventListener('offline', handleOffline)

    return () => {
      window.removeEventListener('online', handleOnline)
      window.removeEventListener('offline', handleOffline)
    }
  }, [])

  const handleAppointmentFound = (appt: Appointment) => {
    setAppointment(appt)
    setCurrentStep('biometric')
  }

  const handleBiometricSuccess = (id: string) => {
    setPatientId(id)
    setCurrentStep('confirmation')
  }

  const handleCheckInComplete = () => {
    setCurrentStep('complete')
    // Reset after a delay for next patient
    setTimeout(() => {
      setCurrentStep('welcome')
      setAppointment(null)
      setPatientId(null)
    }, 3000)
  }

  const renderStep = () => {
    switch (currentStep) {
      case 'welcome':
        return <WelcomeScreen onContinue={() => setCurrentStep('lookup')} />

      case 'lookup':
        return (
          <AppointmentLookup
            onAppointmentFound={handleAppointmentFound}
            onBack={() => setCurrentStep('welcome')}
          />
        )

      case 'biometric':
        return (
          <BiometricAuth
            onSuccess={handleBiometricSuccess}
            onBack={() => setCurrentStep('lookup')}
          />
        )

      case 'confirmation':
        return (
          <CheckInConfirmation
            appointment={appointment}
            patientId={patientId}
            onConfirm={handleCheckInComplete}
            onBack={() => setCurrentStep('biometric')}
          />
        )

      case 'complete':
        return (
          <div className="flex flex-col items-center justify-center min-h-screen p-8 text-center">
            <div className="w-16 h-16 bg-green-100 rounded-full flex items-center justify-center mb-6">
              <svg className="w-8 h-8 text-green-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
              </svg>
            </div>
            <h2 className="text-2xl font-bold text-gray-900 mb-2">Check-In Complete!</h2>
            <p className="text-gray-600 mb-6">
              Thank you for checking in. Please proceed to the waiting area.
            </p>
            <p className="text-sm text-gray-500">
              Returning to welcome screen...
            </p>
          </div>
        )

      default:
        return <WelcomeScreen onContinue={() => setCurrentStep('lookup')} />
    }
  }

  return (
    <div className="relative">
      {/* Offline indicator */}
      {isOffline && (
        <div className="absolute top-0 left-0 right-0 bg-yellow-100 border-b border-yellow-200 p-2 text-center">
          <span className="text-yellow-800 text-sm">
            ⚠️ Operating in offline mode. Some features may be limited.
          </span>
        </div>
      )}

      {/* Main content */}
      <div className="kiosk-content">
        {renderStep()}
      </div>

      {/* Progress indicator */}
      <div className="fixed bottom-4 left-1/2 transform -translate-x-1/2">
        <div className="flex space-x-2">
          {['welcome', 'lookup', 'biometric', 'confirmation'].map((step, index) => (
            <div
              key={step}
              className={`w-3 h-3 rounded-full ${
                currentStep === step
                  ? 'bg-primary-600'
                  : ['welcome', 'lookup', 'biometric', 'confirmation'].indexOf(currentStep) > index
                  ? 'bg-green-500'
                  : 'bg-gray-300'
              }`}
            />
          ))}
        </div>
      </div>
    </div>
  )
}
