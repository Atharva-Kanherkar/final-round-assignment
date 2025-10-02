'use client'

import { useState, useEffect } from 'react'
import { useParams, useRouter } from 'next/navigation'
import { api, QuestionResponse, EvaluationResponse, FinalReportResponse } from '@/lib/api'
import { Loader2, Send, Trophy, TrendingUp, MessageSquare, Star, ArrowRight, CheckCircle2, AlertCircle } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Textarea } from '@/components/ui/textarea'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Separator } from '@/components/ui/separator'
import { Progress } from '@/components/ui/progress'

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
            className={`w-4 h-4 ${i < stars ? 'fill-yellow-500 text-yellow-500' : 'text-muted'}`}
          />
        ))}
        <span className="ml-2 font-semibold text-base">{score.toFixed(1)}/5.0</span>
      </div>
    )
  }

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-background">
        <div className="text-center space-y-4">
          <Loader2 className="w-12 h-12 animate-spin text-primary mx-auto" />
          <p className="text-muted-foreground">Loading interview session...</p>
        </div>
      </div>
    )
  }

  if (interviewComplete && finalReport) {
    return (
      <div className="min-h-screen bg-background py-12">
        <div className="container mx-auto px-4 max-w-4xl">
          <Card>
            <CardHeader className="text-center space-y-4 pb-8">
              <div className="mx-auto w-16 h-16 bg-yellow-500/10 rounded-full flex items-center justify-center">
                <Trophy className="w-8 h-8 text-yellow-500" />
              </div>
              <div>
                <CardTitle className="text-3xl mb-2">Interview Complete</CardTitle>
                <CardDescription>
                  Here's your comprehensive evaluation
                </CardDescription>
              </div>
            </CardHeader>

            <CardContent className="space-y-8">
              {/* Overall Score */}
              <Card className="border-primary/20 bg-primary/5">
                <CardContent className="pt-6">
                  <div className="text-center space-y-4">
                    <p className="text-sm text-muted-foreground">Overall Score</p>
                    <div className="flex justify-center">
                      {renderScore(finalReport.overall_score)}
                    </div>
                    <Badge variant="outline" className="text-lg px-4 py-2">
                      {finalReport.recommendation}
                    </Badge>
                  </div>
                </CardContent>
              </Card>

              {/* Topics Covered */}
              <div>
                <h3 className="text-lg font-semibold mb-4">Topics Covered</h3>
                <div className="flex flex-wrap gap-2">
                  {finalReport.topics_covered.map((topic, idx) => (
                    <Badge key={idx} variant="secondary">
                      {topic}
                    </Badge>
                  ))}
                </div>
              </div>

              <Separator />

              {/* Strengths */}
              {finalReport.overall_strengths.length > 0 && (
                <div>
                  <div className="flex items-center gap-2 mb-4">
                    <TrendingUp className="w-5 h-5 text-green-500" />
                    <h3 className="text-lg font-semibold text-green-500">Key Strengths</h3>
                  </div>
                  <ul className="space-y-3">
                    {finalReport.overall_strengths.map((strength, idx) => (
                      <li key={idx} className="flex items-start gap-3">
                        <CheckCircle2 className="w-5 h-5 text-green-500 mt-0.5 flex-shrink-0" />
                        <span className="text-sm">{strength}</span>
                      </li>
                    ))}
                  </ul>
                </div>
              )}

              {/* Areas for Improvement */}
              {finalReport.areas_for_improvement.length > 0 && (
                <div>
                  <div className="flex items-center gap-2 mb-4">
                    <MessageSquare className="w-5 h-5 text-orange-500" />
                    <h3 className="text-lg font-semibold text-orange-500">Areas for Improvement</h3>
                  </div>
                  <ul className="space-y-3">
                    {finalReport.areas_for_improvement.map((area, idx) => (
                      <li key={idx} className="flex items-start gap-3">
                        <ArrowRight className="w-5 h-5 text-orange-500 mt-0.5 flex-shrink-0" />
                        <span className="text-sm">{area}</span>
                      </li>
                    ))}
                  </ul>
                </div>
              )}

              {/* Additional Notes */}
              {finalReport.additional_notes && (
                <>
                  <Separator />
                  <div>
                    <h3 className="text-lg font-semibold mb-3">Summary</h3>
                    <p className="text-sm text-muted-foreground leading-relaxed">
                      {finalReport.additional_notes}
                    </p>
                  </div>
                </>
              )}

              {/* Actions */}
              <div className="flex justify-center pt-4">
                <Button onClick={() => router.push('/')} size="lg">
                  Start New Interview
                </Button>
              </div>
            </CardContent>
          </Card>
        </div>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-background">
      <div className="container mx-auto px-4 py-8 max-w-5xl">
        {/* Header */}
        <Card className="mb-6">
          <CardContent className="pt-6">
            <div className="flex justify-between items-start">
              <div className="space-y-1">
                <h1 className="text-2xl font-bold">
                  {sessionData?.job_title || 'Interview Session'}
                </h1>
                <p className="text-sm text-muted-foreground">
                  {sessionData?.company && `${sessionData.company} • `}
                  {sessionData?.candidate_name && `Candidate: ${sessionData.candidate_name}`}
                </p>
              </div>
              {currentQuestion && (
                <div className="text-right space-y-1">
                  <p className="text-xs text-muted-foreground">Current Topic</p>
                  <Badge variant="default" className="text-sm">
                    {currentQuestion.topic}
                  </Badge>
                  <p className="text-xs text-muted-foreground">
                    {currentQuestion.topic_progress}
                  </p>
                </div>
              )}
            </div>
          </CardContent>
        </Card>

        {/* Conversation */}
        <div className="space-y-4 mb-6">
          {messages.map((msg, idx) => (
            <div key={idx}>
              {msg.role === 'interviewer' && (
                <Card className="border-l-4 border-l-primary">
                  <CardHeader>
                    <Badge variant="outline" className="w-fit">
                      Question #{Math.floor(idx / 3) + 1}
                    </Badge>
                  </CardHeader>
                  <CardContent>
                    <p className="text-base leading-relaxed">{msg.content}</p>
                  </CardContent>
                </Card>
              )}

              {msg.role === 'candidate' && (
                <Card className="border-l-4 border-l-muted bg-muted/30">
                  <CardHeader>
                    <Badge variant="secondary" className="w-fit">
                      Your Answer
                    </Badge>
                  </CardHeader>
                  <CardContent>
                    <p className="text-sm whitespace-pre-wrap leading-relaxed">{msg.content}</p>
                  </CardContent>
                </Card>
              )}

              {msg.role === 'evaluation' && msg.evaluation && (
                <Card>
                  <CardHeader>
                    <div className="flex items-center justify-between">
                      <CardTitle className="text-lg">Evaluation</CardTitle>
                      {renderScore(msg.evaluation.overall_score)}
                    </div>
                  </CardHeader>
                  <CardContent className="space-y-6">
                    <div className="grid grid-cols-2 gap-4">
                      <div className="space-y-1">
                        <p className="text-xs text-muted-foreground">Technical Accuracy</p>
                        <div className="flex items-center gap-2">
                          <Progress value={msg.evaluation.technical_accuracy * 20} className="h-2" />
                          <span className="text-sm font-semibold min-w-[3rem]">
                            {msg.evaluation.technical_accuracy.toFixed(1)}/5
                          </span>
                        </div>
                      </div>
                      <div className="space-y-1">
                        <p className="text-xs text-muted-foreground">Depth</p>
                        <div className="flex items-center gap-2">
                          <Progress value={msg.evaluation.depth * 20} className="h-2" />
                          <span className="text-sm font-semibold min-w-[3rem]">
                            {msg.evaluation.depth.toFixed(1)}/5
                          </span>
                        </div>
                      </div>
                      <div className="space-y-1">
                        <p className="text-xs text-muted-foreground">Clarity</p>
                        <div className="flex items-center gap-2">
                          <Progress value={msg.evaluation.clarity * 20} className="h-2" />
                          <span className="text-sm font-semibold min-w-[3rem]">
                            {msg.evaluation.clarity.toFixed(1)}/5
                          </span>
                        </div>
                      </div>
                      <div className="space-y-1">
                        <p className="text-xs text-muted-foreground">Relevance</p>
                        <div className="flex items-center gap-2">
                          <Progress value={msg.evaluation.relevance * 20} className="h-2" />
                          <span className="text-sm font-semibold min-w-[3rem]">
                            {msg.evaluation.relevance.toFixed(1)}/5
                          </span>
                        </div>
                      </div>
                    </div>

                    {msg.evaluation.strengths.length > 0 && (
                      <div>
                        <p className="text-sm font-semibold text-green-500 mb-2 flex items-center gap-2">
                          <CheckCircle2 className="w-4 h-4" />
                          Strengths
                        </p>
                        <ul className="space-y-1.5">
                          {msg.evaluation.strengths.map((s, i) => (
                            <li key={i} className="text-sm text-muted-foreground pl-6">
                              • {s}
                            </li>
                          ))}
                        </ul>
                      </div>
                    )}

                    {msg.evaluation.gaps.length > 0 && (
                      <div>
                        <p className="text-sm font-semibold text-orange-500 mb-2 flex items-center gap-2">
                          <AlertCircle className="w-4 h-4" />
                          Areas to Improve
                        </p>
                        <ul className="space-y-1.5">
                          {msg.evaluation.gaps.map((g, i) => (
                            <li key={i} className="text-sm text-muted-foreground pl-6">
                              • {g}
                            </li>
                          ))}
                        </ul>
                      </div>
                    )}

                    <Separator />

                    <div className="bg-muted/30 rounded-md p-4">
                      <p className="text-sm leading-relaxed italic">
                        {msg.evaluation.feedback}
                      </p>
                    </div>
                  </CardContent>
                </Card>
              )}
            </div>
          ))}
        </div>

        {/* Input Area */}
        {!interviewComplete && currentQuestion && (
          <Card className="sticky bottom-4 shadow-lg">
            <CardContent className="pt-6 space-y-4">
              {error && (
                <Card className="border-destructive bg-destructive/10">
                  <CardContent className="pt-4">
                    <p className="text-destructive text-sm">{error}</p>
                  </CardContent>
                </Card>
              )}

              <Textarea
                value={userResponse}
                onChange={(e) => setUserResponse(e.target.value)}
                placeholder="Type your answer here... Be specific and provide examples."
                className="min-h-[160px] resize-none"
                disabled={submitting}
              />

              <div className="flex justify-between items-center">
                <p className="text-xs text-muted-foreground">
                  {userResponse.length} characters
                </p>

                <Button
                  onClick={handleSubmitResponse}
                  disabled={submitting || !userResponse.trim()}
                  size="lg"
                  className="gap-2"
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
                </Button>
              </div>
            </CardContent>
          </Card>
        )}
      </div>
    </div>
  )
}
