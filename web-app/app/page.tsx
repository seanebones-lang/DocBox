import Link from 'next/link'

export default function Home() {
  return (
    <main className="flex min-h-screen flex-col items-center justify-center p-24">
      <div className="z-10 max-w-5xl w-full items-center justify-between font-sans text-sm">
        <div className="text-center">
          <h1 className="text-6xl font-bold mb-4 bg-gradient-to-r from-primary-600 to-primary-400 bg-clip-text text-transparent">
            DocBox
          </h1>
          <p className="text-2xl text-secondary-600 mb-8">
            Enterprise Healthcare Management System
          </p>
          <p className="text-lg text-secondary-500 mb-12 max-w-2xl mx-auto">
            AI-powered RAG system with graph database analytics, 
            self-check-in kiosks, and comprehensive patient management 
            for multi-location healthcare providers.
          </p>
          
          <div className="flex gap-4 justify-center mb-12">
            <Link
              href="/dashboard"
              className="px-8 py-3 bg-primary-600 text-white rounded-lg hover:bg-primary-700 transition-colors font-semibold"
            >
              Go to Dashboard
            </Link>
            <Link
              href="/auth/login"
              className="px-8 py-3 border-2 border-primary-600 text-primary-600 rounded-lg hover:bg-primary-50 transition-colors font-semibold"
            >
              Sign In
            </Link>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mt-16">
            <FeatureCard
              title="AI-Powered RAG"
              description="Agentic retrieval with self-correction and hallucination prevention"
              icon="🤖"
            />
            <FeatureCard
              title="Graph Analytics"
              description="Complex relationship modeling for patient care networks"
              icon="🔗"
            />
            <FeatureCard
              title="HIPAA Compliant"
              description="Enterprise-grade security with comprehensive audit logging"
              icon="🔒"
            />
          </div>
        </div>
      </div>
    </main>
  )
}

function FeatureCard({ title, description, icon }: { 
  title: string
  description: string
  icon: string
}) {
  return (
    <div className="p-6 border border-secondary-200 rounded-lg hover:border-primary-400 transition-colors bg-white shadow-sm">
      <div className="text-4xl mb-4">{icon}</div>
      <h3 className="text-xl font-semibold mb-2 text-secondary-900">{title}</h3>
      <p className="text-secondary-600">{description}</p>
    </div>
  )
}

