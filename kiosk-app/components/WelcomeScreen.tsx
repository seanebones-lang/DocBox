interface WelcomeScreenProps {
  onContinue: () => void
}

export function WelcomeScreen({ onContinue }: WelcomeScreenProps) {
  return (
    <div className="flex flex-col items-center justify-center min-h-screen p-8 text-center bg-gradient-to-b from-primary-50 to-white">
      <div className="max-w-md mx-auto">
        <div className="w-20 h-20 bg-primary-100 rounded-full flex items-center justify-center mb-8 mx-auto">
          <svg className="w-10 h-10 text-primary-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 21V5a2 2 0 00-2-2H7a2 2 0 00-2 2v16m14 0h2m-2 0h-5m-9 0H3m2 0h5M9 7h1m-1 4h1m4-4h1m-1 4h1m-5 10v-5a1 1 0 011-1h2a1 1 0 011 1v5m-4 0h4" />
          </svg>
        </div>

        <h1 className="text-3xl font-bold text-gray-900 mb-4">
          Welcome to DocBox
        </h1>

        <p className="text-lg text-gray-600 mb-8">
          Self-service patient check-in kiosk
        </p>

        <div className="space-y-4 mb-8">
          <div className="flex items-center justify-center space-x-3 text-sm text-gray-600">
            <svg className="w-5 h-5 text-green-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
            </svg>
            <span>Quick and easy check-in</span>
          </div>

          <div className="flex items-center justify-center space-x-3 text-sm text-gray-600">
            <svg className="w-5 h-5 text-green-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
            </svg>
            <span>Secure biometric authentication</span>
          </div>

          <div className="flex items-center justify-center space-x-3 text-sm text-gray-600">
            <svg className="w-5 h-5 text-green-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
            </svg>
            <span>Real-time appointment updates</span>
          </div>
        </div>

        <button
          onClick={onContinue}
          className="w-full bg-primary-600 text-white py-4 px-8 rounded-lg text-lg font-medium hover:bg-primary-700 transition-colors focus:outline-none focus:ring-2 focus:ring-primary-500 focus:ring-offset-2"
        >
          Start Check-In
        </button>

        <p className="mt-6 text-sm text-gray-500">
          Touch the screen to begin
        </p>
      </div>
    </div>
  )
}
