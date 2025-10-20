'use client'

import { useState } from 'react'
import { ChevronLeft, CheckCircle } from 'lucide-react'

interface Appointment {
  id: string
  patient_name: string
  provider_name: string
  scheduled_time: string
  appointment_type: string
  clinic_name: string
}

interface CheckInConfirmationProps {
  appointment: Appointment | null
  patientId: string | null
  onConfirm: () => void
  onBack: () => void
}

export function CheckInConfirmation({ appointment, patientId, onConfirm, onBack }: CheckInConfirmationProps) {
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')

  const handleConfirm = async () => {
    if (!appointment || !patientId) return

    setLoading(true)
    setError('')

    try {
      // In a real implementation, this would call the check-in API
      await new Promise(resolve => setTimeout(resolve, 1500))

      // Mock successful check-in
      onConfirm()
    } catch (err) {
      setError('Check-in failed. Please try again.')
    } finally {
      setLoading(false)
    }
  }

  if (!appointment) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-center">
          <h2 className="text-xl font-medium text-gray-900 mb-2">No Appointment Selected</h2>
          <button
            onClick={onBack}
            className="text-primary-600 hover:text-primary-900"
          >
            Go back to select an appointment
          </button>
        </div>
      </div>
    )
  }

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
          <h1 className="text-2xl font-bold text-gray-900">Confirm Check-In</h1>
        </div>

        {/* Appointment Summary */}
        <div className="bg-gray-50 rounded-lg p-6 mb-6">
          <div className="flex items-start space-x-4">
            <div className="w-12 h-12 bg-green-100 rounded-full flex items-center justify-center flex-shrink-0">
              <CheckCircle className="w-6 h-6 text-green-600" />
            </div>

            <div className="flex-1">
              <h2 className="text-lg font-medium text-gray-900 mb-2">
                Identity Verified
              </h2>
              <p className="text-gray-600 text-sm mb-4">
                Patient ID: {patientId}
              </p>

              <div className="border-t border-gray-200 pt-4">
                <h3 className="font-medium text-gray-900 mb-2">Appointment Details</h3>

                <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-sm">
                  <div>
                    <span className="font-medium text-gray-700">Patient:</span>
                    <p className="text-gray-900">{appointment.patient_name}</p>
                  </div>

                  <div>
                    <span className="font-medium text-gray-700">Provider:</span>
                    <p className="text-gray-900">{appointment.provider_name}</p>
                  </div>

                  <div>
                    <span className="font-medium text-gray-700">Date & Time:</span>
                    <p className="text-gray-900">
                      {new Date(appointment.scheduled_time).toLocaleDateString()} at{' '}
                      {new Date(appointment.scheduled_time).toLocaleTimeString([], {
                        hour: '2-digit',
                        minute: '2-digit'
                      })}
                    </p>
                  </div>

                  <div>
                    <span className="font-medium text-gray-700">Type:</span>
                    <p className="text-gray-900">{appointment.appointment_type}</p>
                  </div>

                  <div className="md:col-span-2">
                    <span className="font-medium text-gray-700">Location:</span>
                    <p className="text-gray-900">{appointment.clinic_name}</p>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>

        {error && (
          <div className="bg-red-50 border border-red-200 text-red-600 px-4 py-3 rounded-md mb-6">
            {error}
          </div>
        )}

        {/* Confirmation Actions */}
        <div className="space-y-3">
          <button
            onClick={handleConfirm}
            disabled={loading}
            className="w-full bg-primary-600 text-white py-4 px-8 rounded-lg text-lg font-medium hover:bg-primary-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed focus:outline-none focus:ring-2 focus:ring-primary-500 focus:ring-offset-2"
          >
            {loading ? (
              <div className="flex items-center justify-center">
                <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-white mr-2"></div>
                Checking In...
              </div>
            ) : (
              'Confirm Check-In'
            )}
          </button>

          <button
            onClick={onBack}
            className="w-full bg-white border border-gray-300 text-gray-700 py-3 px-6 rounded-lg font-medium hover:bg-gray-50 transition-colors"
          >
            Go Back
          </button>
        </div>

        {/* Additional Information */}
        <div className="mt-8 text-center">
          <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
            <h3 className="font-medium text-blue-900 mb-2">What happens next?</h3>
            <ul className="text-blue-800 text-sm space-y-1 text-left">
              <li>• You'll receive a confirmation message on screen</li>
              <li>• Your provider will be notified of your arrival</li>
              <li>• Please proceed to the waiting area</li>
              <li>• We'll call your name when it's your turn</li>
            </ul>
          </div>
        </div>
      </div>
    </div>
  )
}
