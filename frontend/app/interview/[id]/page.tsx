'use client'

import { useState, useEffect } from 'react'
import { useParams, useRouter } from 'next/navigation'
import { api, QuestionResponse, EvaluationResponse, FinalReportResponse } from '@/lib/api'
import { Loader2, Send, Trophy, TrendingUp, MessageSquare, Star, ArrowRight } from 'lucide-react'

type Message = {
  role: 'interviewer' | 'candidate' | 'evaluation'
  content: string
  evaluation?: EvaluationResponse['evaluation']
}

export default function InterviewPage() {
  const params = useParams()
  const router = useRouter()
  const sessionId = params.id as string

  const [loading, setLoading] = useState(true)
  const [submitting, setSubmitting] = useState(false)
  const [error, setError] = useState('')

  const [sessionData, setSessionData] = useState<any>(null)
  const [currentQuestion, setCurrentQuestion] = useState<QuestionResponse | null>(null)
  const [userResponse, setUserResponse] = useState('')
  const [messages, setMessages] = useState<Message[]>([])
  const [interviewComplete, setInterviewComplete] = useState(false)
  const [finalReport, setFinalReport] = useState<FinalReportResponse | null>(null)

  // Load session data
  useEffect(() => {
    const loadSession = async () => {
      try {
        const session = await api.getSession(sessionId)
        setSessionData(session)

        // Get first question from session data
        if (session.first_question) {
          setCurrentQuestion(session.first_question)
          setMessages([{
            role: 'interviewer',
            content: session.first_question.question
          }])
        }

        setLoading(false)
      } catch (err: any) {
        setError(err.message || 'Failed to load session')
        setLoading(false)
      }
    }

    if (sessionId) {
      loadSession()
    }
  }, [sessionId])

  const handleSubmitResponse = async () => {
    if (!userResponse.trim()) return

    setSubmitting(true)
    setError('')

    try {
      // Add user message to chat
      setMessages(prev => [...prev, {
        role: 'candidate',
        content: userResponse
      }])

      // Submit to API
      const result = await api.submitResponse(sessionId, userResponse)

      // Add evaluation
      setMessages(prev => [...prev, {
        role: 'evaluation',
        content: result.evaluation.feedback,
        evaluation: result.evaluation
      }])

      // Clear input
      setUserResponse('')

      // Check if interview complete
      if (result.interview_complete) {
        setInterviewComplete(true)
        // Get final report
        const report = await api.completeInterview(sessionId)
        setFinalReport(report)
      } else if (result.next_question) {
        // Add next question
        setCurrentQuestion(result.next_question)
        setMessages(prev => [...prev, {
          role: 'interviewer',
          content: result.next_question!.question
        }])
      }

      setSubmitting(false)
    } catch (err: any) {
      setError(err.message || 'Failed to submit response')
      setSubmitting(false)
    }
  }

  const renderScore = (score: number) => {
    const stars = Math.round(score)
    return (
      <div className="flex items-center gap-1">
        {[...Array(5)].map((_, i) => (
          <Star
            key={i}
            className={`w-5 h-5 ${i < stars ? 'fill-yellow-400 text-yellow-400' : 'text-gray-300'}`}
          />
        ))}
        <span className="ml-2 font-semibold text-lg">{score.toFixed(1)}/5.0</span>
      </div>
    )
  }

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-center">
          <Loader2 className="w-12 h-12 animate-spin text-blue-600 mx-auto mb-4" />
          <p className="text-gray-600 dark:text-gray-400">Loading interview session...</p>
        </div>
      </div>
    )
  }

  if (interviewComplete && finalReport) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-blue-50 via-white to-purple-50 dark:from-gray-900 dark:via-gray-800 dark:to-gray-900 py-12">
        <div className="container mx-auto px-4 max-w-4xl">
          <div className="bg-white dark:bg-gray-800 rounded-lg shadow-2xl p-8">
            <div className="text-center mb-8">
              <Trophy className="w-16 h-16 text-yellow-500 mx-auto mb-4" />
              <h1 className="text-4xl font-bold text-gray-900 dark:text-white mb-2">
                Interview Complete!
              </h1>
              <p className="text-gray-600 dark:text-gray-400">
                Here's your comprehensive evaluation
              </p>
            </div>

            {/* Overall Score */}
            <div className="bg-gradient-to-r from-blue-50 to-purple-50 dark:from-blue-900/20 dark:to-purple-900/20 rounded-lg p-6 mb-8">
              <div className="text-center">
                <p className="text-sm text-gray-600 dark:text-gray-400 mb-2">Overall Score</p>
                <div className="flex justify-center mb-2">
                  {renderScore(finalReport.overall_score)}
                </div>
                <p className="text-2xl font-bold text-gray-900 dark:text-white">
                  {finalReport.recommendation}
                </p>
              </div>
            </div>

            {/* Topics Covered */}
            <div className="mb-8">
              <h3 className="text-xl font-semibold text-gray-900 dark:text-white mb-4">
                Topics Covered
              </h3>
              <div className="flex flex-wrap gap-2">
                {finalReport.topics_covered.map((topic, idx) => (
                  <span
                    key={idx}
                    className="px-4 py-2 bg-blue-100 dark:bg-blue-900/30 text-blue-800 dark:text-blue-300 rounded-full text-sm font-medium"
                  >
                    {topic}
                  </span>
                ))}
              </div>
            </div>

            {/* Strengths */}
            {finalReport.overall_strengths.length > 0 && (
              <div className="mb-8">
                <h3 className="text-xl font-semibold text-green-700 dark:text-green-400 mb-4 flex items-center gap-2">
                  <TrendingUp className="w-6 h-6" />
                  Key Strengths
                </h3>
                <ul className="space-y-2">
                  {finalReport.overall_strengths.map((strength, idx) => (
                    <li key={idx} className="flex items-start gap-2">
                      <span className="text-green-600 dark:text-green-400 mt-1">✓</span>
                      <span className="text-gray-700 dark:text-gray-300">{strength}</span>
                    </li>
                  ))}
                </ul>
              </div>
            )}

            {/* Areas for Improvement */}
            {finalReport.areas_for_improvement.length > 0 && (
              <div className="mb-8">
                <h3 className="text-xl font-semibold text-orange-700 dark:text-orange-400 mb-4 flex items-center gap-2">
                  <MessageSquare className="w-6 h-6" />
                  Areas for Improvement
                </h3>
                <ul className="space-y-2">
                  {finalReport.areas_for_improvement.map((area, idx) => (
                    <li key={idx} className="flex items-start gap-2">
                      <span className="text-orange-600 dark:text-orange-400 mt-1">→</span>
                      <span className="text-gray-700 dark:text-gray-300">{area}</span>
                    </li>
                  ))}
                </ul>
              </div>
            )}

            {/* Additional Notes */}
            {finalReport.additional_notes && (
              <div className="mb-8">
                <h3 className="text-xl font-semibold text-gray-900 dark:text-white mb-4">
                  Summary
                </h3>
                <p className="text-gray-700 dark:text-gray-300 leading-relaxed">
                  {finalReport.additional_notes}
                </p>
              </div>
            )}

            {/* Actions */}
            <div className="text-center">
              <button
                onClick={() => router.push('/')}
                className="px-8 py-3 bg-blue-600 text-white rounded-lg font-semibold hover:bg-blue-700 transition-colors"
              >
                Start New Interview
              </button>
            </div>
          </div>
        </div>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 via-white to-purple-50 dark:from-gray-900 dark:via-gray-800 dark:to-gray-900">
      <div className="container mx-auto px-4 py-8 max-w-5xl">
        {/* Header */}
        <div className="bg-white dark:bg-gray-800 rounded-lg shadow-lg p-6 mb-6">
          <div className="flex justify-between items-center">
            <div>
              <h1 className="text-2xl font-bold text-gray-900 dark:text-white">
                {sessionData?.job_title || 'Interview Session'}
              </h1>
              <p className="text-gray-600 dark:text-gray-400">
                {sessionData?.company || ''} • Candidate: {sessionData?.candidate_name || ''}
              </p>
            </div>
            {currentQuestion && (
              <div className="text-right">
                <p className="text-sm text-gray-500 dark:text-gray-400">Current Topic</p>
                <p className="text-lg font-semibold text-blue-600 dark:text-blue-400">
                  {currentQuestion.topic}
                </p>
                <p className="text-sm text-gray-500 dark:text-gray-400">
                  Topic {currentQuestion.topic_progress}
                </p>
              </div>
            )}
          </div>
        </div>

        {/* Conversation */}
        <div className="space-y-4 mb-6">
          {messages.map((msg, idx) => (
            <div key={idx}>
              {msg.role === 'interviewer' && (
                <div className="bg-blue-50 dark:bg-blue-900/20 rounded-lg p-6 border-l-4 border-blue-600">
                  <p className="text-sm font-semibold text-blue-600 dark:text-blue-400 mb-2">
                    Question #{Math.floor(idx / 3) + 1}
                  </p>
                  <p className="text-gray-900 dark:text-white text-lg">{msg.content}</p>
                </div>
              )}

              {msg.role === 'candidate' && (
                <div className="bg-gray-50 dark:bg-gray-700/50 rounded-lg p-6 border-l-4 border-gray-400">
                  <p className="text-sm font-semibold text-gray-600 dark:text-gray-400 mb-2">
                    Your Answer
                  </p>
                  <p className="text-gray-800 dark:text-gray-200 whitespace-pre-wrap">{msg.content}</p>
                </div>
              )}

              {msg.role === 'evaluation' && msg.evaluation && (
                <div className="bg-white dark:bg-gray-800 rounded-lg shadow-lg p-6 border border-gray-200 dark:border-gray-700">
                  <div className="flex items-center justify-between mb-4">
                    <h3 className="text-lg font-semibold text-gray-900 dark:text-white">
                      Evaluation
                    </h3>
                    {renderScore(msg.evaluation.overall_score)}
                  </div>

                  <div className="grid grid-cols-2 gap-4 mb-4">
                    <div>
                      <p className="text-sm text-gray-600 dark:text-gray-400">Technical Accuracy</p>
                      <p className="text-lg font-semibold">{msg.evaluation.technical_accuracy.toFixed(1)}/5.0</p>
                    </div>
                    <div>
                      <p className="text-sm text-gray-600 dark:text-gray-400">Depth</p>
                      <p className="text-lg font-semibold">{msg.evaluation.depth.toFixed(1)}/5.0</p>
                    </div>
                    <div>
                      <p className="text-sm text-gray-600 dark:text-gray-400">Clarity</p>
                      <p className="text-lg font-semibold">{msg.evaluation.clarity.toFixed(1)}/5.0</p>
                    </div>
                    <div>
                      <p className="text-sm text-gray-600 dark:text-gray-400">Relevance</p>
                      <p className="text-lg font-semibold">{msg.evaluation.relevance.toFixed(1)}/5.0</p>
                    </div>
                  </div>

                  {msg.evaluation.strengths.length > 0 && (
                    <div className="mb-4">
                      <p className="text-sm font-semibold text-green-700 dark:text-green-400 mb-2">
                        ✓ Strengths
                      </p>
                      <ul className="space-y-1">
                        {msg.evaluation.strengths.map((s, i) => (
                          <li key={i} className="text-sm text-gray-700 dark:text-gray-300 pl-4">
                            • {s}
                          </li>
                        ))}
                      </ul>
                    </div>
                  )}

                  {msg.evaluation.gaps.length > 0 && (
                    <div className="mb-4">
                      <p className="text-sm font-semibold text-orange-700 dark:text-orange-400 mb-2">
                        → Areas to Improve
                      </p>
                      <ul className="space-y-1">
                        {msg.evaluation.gaps.map((g, i) => (
                          <li key={i} className="text-sm text-gray-700 dark:text-gray-300 pl-4">
                            • {g}
                          </li>
                        ))}
                      </ul>
                    </div>
                  )}

                  <div className="pt-4 border-t border-gray-200 dark:border-gray-700">
                    <p className="text-sm text-gray-700 dark:text-gray-300 italic">
                      {msg.evaluation.feedback}
                    </p>
                  </div>
                </div>
              )}
            </div>
          ))}
        </div>

        {/* Input Area */}
        {!interviewComplete && currentQuestion && (
          <div className="bg-white dark:bg-gray-800 rounded-lg shadow-lg p-6 sticky bottom-4">
            {error && (
              <div className="mb-4 bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg p-3">
                <p className="text-red-800 dark:text-red-200 text-sm">{error}</p>
              </div>
            )}

            <textarea
              value={userResponse}
              onChange={(e) => setUserResponse(e.target.value)}
              placeholder="Type your answer here... Be specific and provide examples."
              className="w-full h-40 px-4 py-3 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent dark:bg-gray-700 dark:text-white resize-none mb-4"
              disabled={submitting}
            />

            <div className="flex justify-between items-center">
              <p className="text-sm text-gray-500 dark:text-gray-400">
                {userResponse.length} characters
              </p>

              <button
                onClick={handleSubmitResponse}
                disabled={submitting || !userResponse.trim()}
                className="px-6 py-3 bg-blue-600 text-white rounded-lg font-semibold hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-all flex items-center gap-2"
              >
                {submitting ? (
                  <>
                    <Loader2 className="w-5 h-5 animate-spin" />
                    Processing...
                  </>
                ) : (
                  <>
                    Submit Answer
                    <Send className="w-5 h-5" />
                  </>
                )}
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  )
}
