'use client'

import { useState } from 'react'
import { useRouter } from 'next/navigation'
import { api } from '@/lib/api'
import { FileText, Briefcase, ArrowRight, Loader2, Sparkles, Target, TrendingUp } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Textarea } from '@/components/ui/textarea'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'

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
    <main className="min-h-screen bg-background">
      <div className="container mx-auto px-4 py-16 max-w-6xl">
        {/* Header */}
        <div className="text-center mb-16 space-y-4">
          <Badge variant="outline" className="mb-4">
            AI-Powered Interview Platform
          </Badge>
          <h1 className="text-5xl font-bold tracking-tight">
            AI Mock Interview System
          </h1>
          <p className="text-xl text-muted-foreground max-w-2xl mx-auto">
            Practice technical interviews with intelligent AI feedback and comprehensive evaluation
          </p>
        </div>

        {/* Main Form */}
        <form onSubmit={handleStartInterview} className="space-y-6">
          {/* Resume Input */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-3">
                <FileText className="w-5 h-5 text-primary" />
                Your Resume
              </CardTitle>
              <CardDescription>
                Paste your resume to help us understand your background and skills
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-2">
              <Textarea
                value={resume}
                onChange={(e) => setResume(e.target.value)}
                placeholder="Paste your resume here... (minimum 50 characters)"
                className="min-h-[280px] resize-none font-mono text-sm"
                required
                minLength={50}
              />
              <p className="text-xs text-muted-foreground">
                {resume.length} characters
              </p>
            </CardContent>
          </Card>

          {/* Job Description Input */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-3">
                <Briefcase className="w-5 h-5 text-primary" />
                Target Job Description
              </CardTitle>
              <CardDescription>
                Provide the job description you're preparing for
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-2">
              <Textarea
                value={jobDescription}
                onChange={(e) => setJobDescription(e.target.value)}
                placeholder="Paste the job description here... (minimum 50 characters)"
                className="min-h-[280px] resize-none font-mono text-sm"
                required
                minLength={50}
              />
              <p className="text-xs text-muted-foreground">
                {jobDescription.length} characters
              </p>
            </CardContent>
          </Card>

          {/* Error Message */}
          {error && (
            <Card className="border-destructive">
              <CardContent className="pt-6">
                <p className="text-destructive text-sm">{error}</p>
              </CardContent>
            </Card>
          )}

          {/* Actions */}
          <div className="flex gap-4 justify-center">
            <Button
              type="button"
              variant="outline"
              onClick={loadSampleData}
              size="lg"
            >
              Load Sample Data
            </Button>

            <Button
              type="submit"
              disabled={loading || !resume.trim() || !jobDescription.trim()}
              size="lg"
              className="gap-2"
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
            </Button>
          </div>
        </form>

        {/* Features */}
        <div className="mt-20 grid md:grid-cols-3 gap-6">
          <Card className="border-muted">
            <CardHeader>
              <div className="w-12 h-12 bg-primary/10 rounded-lg flex items-center justify-center mb-4">
                <Sparkles className="w-6 h-6 text-primary" />
              </div>
              <CardTitle className="text-lg">AI-Powered Questions</CardTitle>
            </CardHeader>
            <CardContent>
              <p className="text-sm text-muted-foreground">
                Dynamic questions tailored to your background and the target role
              </p>
            </CardContent>
          </Card>

          <Card className="border-muted">
            <CardHeader>
              <div className="w-12 h-12 bg-primary/10 rounded-lg flex items-center justify-center mb-4">
                <Target className="w-6 h-6 text-primary" />
              </div>
              <CardTitle className="text-lg">Real-time Feedback</CardTitle>
            </CardHeader>
            <CardContent>
              <p className="text-sm text-muted-foreground">
                Instant evaluation with detailed scoring and improvement suggestions
              </p>
            </CardContent>
          </Card>

          <Card className="border-muted">
            <CardHeader>
              <div className="w-12 h-12 bg-primary/10 rounded-lg flex items-center justify-center mb-4">
                <TrendingUp className="w-6 h-6 text-primary" />
              </div>
              <CardTitle className="text-lg">Comprehensive Report</CardTitle>
            </CardHeader>
            <CardContent>
              <p className="text-sm text-muted-foreground">
                Complete evaluation with strengths, weaknesses, and recommendations
              </p>
            </CardContent>
          </Card>
        </div>
      </div>
    </main>
  )
}
