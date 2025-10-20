'use client'

import { useState } from 'react'
import { ChevronLeft } from 'lucide-react'

interface AppointmentLookupProps {
  onAppointmentFound: (appointment: any) => void
  onBack: () => void
}

interface Appointment {
  id: string
  patient_name: string
  provider_name: string
  scheduled_time: string
  appointment_type: string
  clinic_name: string
}

export function AppointmentLookup({ onAppointmentFound, onBack }: AppointmentLookupProps) {
  const [searchType, setSearchType] = useState<'dob' | 'phone' | 'mrn'>('dob')
  const [searchData, setSearchData] = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const [appointments, setAppointments] = useState<Appointment[]>([])

  const handleSearch = async () => {
    if (!searchData.trim()) {
      setError('Please enter search information')
      return
    }

    setLoading(true)
    setError('')

    try {
      // In a real implementation, this would call the API
      // For demo purposes, we'll simulate finding appointments
      await new Promise(resolve => setTimeout(resolve, 1000))

      // Mock data - in real app this would come from API
      const mockAppointments: Appointment[] = [
        {
          id: '1',
          patient_name: 'John Doe',
          provider_name: 'Dr. Smith',
          scheduled_time: '2025-10-20T14:00:00Z',
          appointment_type: 'Annual Physical',
          clinic_name: 'Downtown Medical Center'
        }
      ]

      setAppointments(mockAppointments)
    } catch (err) {
      setError('Failed to search appointments. Please try again.')
    } finally {
      setLoading(false)
    }
  }

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter') {
      handleSearch()
    }
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
          <h1 className="text-2xl font-bold text-gray-900">Find Your Appointment</h1>
        </div>

        {/* Search Type Selection */}
        <div className="mb-6">
          <p className="text-gray-600 mb-4">How would you like to search for your appointment?</p>

          <div className="grid grid-cols-3 gap-3">
            <button
              onClick={() => setSearchType('dob')}
              className={`p-4 rounded-lg border-2 text-center transition-colors ${
                searchType === 'dob'
                  ? 'border-primary-500 bg-primary-50 text-primary-700'
                  : 'border-gray-200 hover:border-gray-300'
              }`}
            >
              <div className="text-sm font-medium">Date of Birth</div>
              <div className="text-xs text-gray-500 mt-1">MM/DD/YYYY</div>
            </button>

            <button
              onClick={() => setSearchType('phone')}
              className={`p-4 rounded-lg border-2 text-center transition-colors ${
                searchType === 'phone'
                  ? 'border-primary-500 bg-primary-50 text-primary-700'
                  : 'border-gray-200 hover:border-gray-300'
              }`}
            >
              <div className="text-sm font-medium">Phone Number</div>
              <div className="text-xs text-gray-500 mt-1">XXX-XXX-XXXX</div>
            </button>

            <button
              onClick={() => setSearchType('mrn')}
              className={`p-4 rounded-lg border-2 text-center transition-colors ${
                searchType === 'mrn'
                  ? 'border-primary-500 bg-primary-50 text-primary-700'
                  : 'border-gray-200 hover:border-gray-300'
              }`}
            >
              <div className="text-sm font-medium">Medical Record #</div>
              <div className="text-xs text-gray-500 mt-1">MRN-XXXXXX</div>
            </button>
          </div>
        </div>

        {/* Search Input */}
        <div className="mb-6">
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Enter your {searchType === 'dob' ? 'date of birth' : searchType === 'phone' ? 'phone number' : 'medical record number'}
          </label>

          <input
            type={searchType === 'dob' ? 'date' : 'text'}
            value={searchData}
            onChange={(e) => setSearchData(e.target.value)}
            onKeyPress={handleKeyPress}
            placeholder={
              searchType === 'dob' ? 'MM/DD/YYYY' :
              searchType === 'phone' ? 'XXX-XXX-XXXX' :
              'MRN-XXXXXX'
            }
            className="w-full px-4 py-3 text-lg border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-primary-500"
          />
        </div>

        {error && (
          <div className="mb-6 bg-red-50 border border-red-200 text-red-600 px-4 py-3 rounded-md">
            {error}
          </div>
        )}

        {/* Search Button */}
        <button
          onClick={handleSearch}
          disabled={loading || !searchData.trim()}
          className="w-full bg-primary-600 text-white py-4 px-8 rounded-lg text-lg font-medium hover:bg-primary-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed focus:outline-none focus:ring-2 focus:ring-primary-500 focus:ring-offset-2"
        >
          {loading ? (
            <div className="flex items-center justify-center">
              <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-white mr-2"></div>
              Searching...
            </div>
          ) : (
            'Search Appointments'
          )}
        </button>

        {/* Search Results */}
        {appointments.length > 0 && (
          <div className="mt-8">
            <h2 className="text-lg font-medium text-gray-900 mb-4">
              Select Your Appointment
            </h2>

            <div className="space-y-3">
              {appointments.map((appointment) => (
                <button
                  key={appointment.id}
                  onClick={() => onAppointmentFound(appointment)}
                  className="w-full p-4 border border-gray-200 rounded-lg text-left hover:bg-gray-50 hover:border-gray-300 transition-colors"
                >
                  <div className="flex justify-between items-start">
                    <div>
                      <div className="font-medium text-gray-900">
                        {appointment.patient_name}
                      </div>
                      <div className="text-sm text-gray-600 mt-1">
                        with {appointment.provider_name}
                      </div>
                      <div className="text-sm text-gray-600">
                        {appointment.clinic_name}
                      </div>
                    </div>
                    <div className="text-right">
                      <div className="text-sm font-medium text-gray-900">
                        {new Date(appointment.scheduled_time).toLocaleDateString()}
                      </div>
                      <div className="text-sm text-gray-600">
                        {new Date(appointment.scheduled_time).toLocaleTimeString([], {
                          hour: '2-digit',
                          minute: '2-digit'
                        })}
                      </div>
                      <div className="text-xs text-primary-600 mt-1">
                        {appointment.appointment_type}
                      </div>
                    </div>
                  </div>
                </button>
              ))}
            </div>
          </div>
        )}

        {/* Help Text */}
        <div className="mt-8 text-center">
          <p className="text-sm text-gray-500">
            Having trouble? Please see a staff member at the front desk for assistance.
          </p>
        </div>
      </div>
    </div>
  )
}
