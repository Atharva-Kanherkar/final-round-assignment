'use client'

import { useState } from 'react'
import { useRouter } from 'next/navigation'
import { api } from '@/lib/api'
import { FileText, Briefcase, ArrowRight, Loader2 } from 'lucide-react'

export default function Home() {
  const router = useRouter()
  const [resume, setResume] = useState('')
  const [jobDescription, setJobDescription] = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')

  const handleStartInterview = async (e: React.FormEvent) => {
    e.preventDefault()
    setError('')
    setLoading(true)

    try {
      const session = await api.createSession({
        resume_text: resume,
        job_description_text: jobDescription,
      })

      // Navigate to interview page
      router.push(`/interview/${session.session_id}`)
    } catch (err: any) {
      setError(err.message || 'Failed to start interview')
      setLoading(false)
    }
  }

  const loadSampleData = () => {
    setResume(`John Doe
Senior Software Engineer
5 years experience

Skills: Python, JavaScript, React, Node.js, AWS, Docker, Kubernetes, PostgreSQL, MongoDB, Redis

Experience:
- TechCorp (2020-2023): Led backend development for microservices architecture serving 1M+ users. Designed and implemented RESTful APIs using Python/Django. Migrated monolithic application to containerized microservices using Docker and Kubernetes.

- StartupXYZ (2018-2020): Full-stack development using React and Node.js. Built authentication system and real-time features using WebSockets.

Education: BS Computer Science, State University (2014-2018)`)

    setJobDescription(`Senior Backend Engineer
Company: TechCo

Requirements:
- 5+ years Python experience
- Strong system design skills
- Experience with distributed systems
- AWS/Cloud experience required
- Experience with microservices architecture
- Proficiency in SQL and NoSQL databases

Responsibilities:
- Design scalable backend services handling millions of requests
- Lead technical initiatives and architecture decisions
- Mentor junior engineers and conduct code reviews`)
  }

  return (
    <main className="min-h-screen bg-gradient-to-br from-blue-50 via-white to-purple-50 dark:from-gray-900 dark:via-gray-800 dark:to-gray-900">
      <div className="container mx-auto px-4 py-12 max-w-6xl">
        {/* Header */}
        <div className="text-center mb-12">
          <h1 className="text-5xl font-bold text-gray-900 dark:text-white mb-4">
            AI Mock Interview System
          </h1>
          <p className="text-xl text-gray-600 dark:text-gray-300">
            Practice technical interviews with AI-powered feedback and evaluation
          </p>
        </div>

        {/* Main Form */}
        <form onSubmit={handleStartInterview} className="space-y-8">
          {/* Resume Input */}
          <div className="bg-white dark:bg-gray-800 rounded-lg shadow-lg p-6">
            <div className="flex items-center gap-3 mb-4">
              <FileText className="w-6 h-6 text-blue-600" />
              <h2 className="text-2xl font-semibold text-gray-900 dark:text-white">
                Your Resume
              </h2>
            </div>
            <textarea
              value={resume}
              onChange={(e) => setResume(e.target.value)}
              placeholder="Paste your resume here... (minimum 50 characters)"
              className="w-full h-64 px-4 py-3 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent dark:bg-gray-700 dark:text-white resize-none"
              required
              minLength={50}
            />
            <p className="mt-2 text-sm text-gray-500 dark:text-gray-400">
              {resume.length} characters
            </p>
          </div>

          {/* Job Description Input */}
          <div className="bg-white dark:bg-gray-800 rounded-lg shadow-lg p-6">
            <div className="flex items-center gap-3 mb-4">
              <Briefcase className="w-6 h-6 text-purple-600" />
              <h2 className="text-2xl font-semibold text-gray-900 dark:text-white">
                Target Job Description
              </h2>
            </div>
            <textarea
              value={jobDescription}
              onChange={(e) => setJobDescription(e.target.value)}
              placeholder="Paste the job description here... (minimum 50 characters)"
              className="w-full h-64 px-4 py-3 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent dark:bg-gray-700 dark:text-white resize-none"
              required
              minLength={50}
            />
            <p className="mt-2 text-sm text-gray-500 dark:text-gray-400">
              {jobDescription.length} characters
            </p>
          </div>

          {/* Error Message */}
          {error && (
            <div className="bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg p-4">
              <p className="text-red-800 dark:text-red-200">{error}</p>
            </div>
          )}

          {/* Actions */}
          <div className="flex gap-4 justify-center">
            <button
              type="button"
              onClick={loadSampleData}
              className="px-6 py-3 border border-gray-300 dark:border-gray-600 rounded-lg text-gray-700 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors"
            >
              Load Sample Data
            </button>

            <button
              type="submit"
              disabled={loading || !resume.trim() || !jobDescription.trim()}
              className="px-8 py-3 bg-gradient-to-r from-blue-600 to-purple-600 text-white rounded-lg font-semibold hover:from-blue-700 hover:to-purple-700 disabled:opacity-50 disabled:cursor-not-allowed transition-all flex items-center gap-2"
            >
              {loading ? (
                <>
                  <Loader2 className="w-5 h-5 animate-spin" />
                  Starting Interview...
                </>
              ) : (
                <>
                  Start Interview
                  <ArrowRight className="w-5 h-5" />
                </>
              )}
            </button>
          </div>
        </form>

        {/* Features */}
        <div className="mt-16 grid md:grid-cols-3 gap-8">
          <div className="text-center">
            <div className="w-12 h-12 bg-blue-100 dark:bg-blue-900/30 rounded-lg flex items-center justify-center mx-auto mb-4">
              <span className="text-2xl">🤖</span>
            </div>
            <h3 className="font-semibold text-gray-900 dark:text-white mb-2">
              AI-Powered Questions
            </h3>
            <p className="text-gray-600 dark:text-gray-400 text-sm">
              Dynamic questions tailored to your background and the target role
            </p>
          </div>

          <div className="text-center">
            <div className="w-12 h-12 bg-purple-100 dark:bg-purple-900/30 rounded-lg flex items-center justify-center mx-auto mb-4">
              <span className="text-2xl">📊</span>
            </div>
            <h3 className="font-semibold text-gray-900 dark:text-white mb-2">
              Real-time Feedback
            </h3>
            <p className="text-gray-600 dark:text-gray-400 text-sm">
              Instant evaluation with detailed scoring and improvement suggestions
            </p>
          </div>

          <div className="text-center">
            <div className="w-12 h-12 bg-green-100 dark:bg-green-900/30 rounded-lg flex items-center justify-center mx-auto mb-4">
              <span className="text-2xl">📈</span>
            </div>
            <h3 className="font-semibold text-gray-900 dark:text-white mb-2">
              Comprehensive Report
            </h3>
            <p className="text-gray-600 dark:text-gray-400 text-sm">
              Complete evaluation with strengths, weaknesses, and recommendations
            </p>
          </div>
        </div>
      </div>
    </main>
  )
}
