'use client'

import { useState } from 'react'
import { useRouter } from 'next/navigation'
import { api } from '@/lib/api'
import { FileText, Briefcase, ArrowRight, Loader2, Sparkles, Target, TrendingUp, Upload } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Textarea } from '@/components/ui/textarea'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'

export default function Home() {
  const router = useRouter()
  const [resume, setResume] = useState('')
  const [resumeFile, setResumeFile] = useState<File | null>(null)
  const [jobDescription, setJobDescription] = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const [inputMode, setInputMode] = useState<'text' | 'file'>('file')

  const handleStartInterview = async (e: React.FormEvent) => {
    e.preventDefault()
    setError('')
    setLoading(true)

    try {
      let session

      if (inputMode === 'file') {
        // Validate file upload
        if (!resumeFile) {
          setError('Please upload a resume file')
          setLoading(false)
          return
        }
        if (!jobDescription.trim()) {
          setError('Please provide a job description')
          setLoading(false)
          return
        }

        // Use file upload API
        session = await api.createSessionWithFiles(resumeFile, jobDescription)
      } else {
        // Use text input API
        if (!resume.trim()) {
          setError('Please provide resume text')
          setLoading(false)
          return
        }
        if (!jobDescription.trim()) {
          setError('Please provide job description text')
          setLoading(false)
          return
        }

        session = await api.createSession({
          resume_text: resume,
          job_description_text: jobDescription,
        })
      }

      // Navigate to interview page
      router.push(`/interview/${session.session_id}`)
    } catch (err: any) {
      setError(err.message || 'Failed to start interview')
      setLoading(false)
    }
  }

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0]
    if (file) {
      const validExtensions = ['.pdf', '.docx', '.doc', '.txt']
      const fileExt = file.name.toLowerCase().slice(file.name.lastIndexOf('.'))

      if (!validExtensions.includes(fileExt)) {
        setError(`Invalid file type. Allowed: ${validExtensions.join(', ')}`)
        return
      }

      if (file.size > 5 * 1024 * 1024) {
        setError('File too large. Maximum size: 5MB')
        return
      }

      setError('')
      setResumeFile(file)
    }
  }

  const loadSampleData = () => {
    setInputMode('text')
    setResumeFile(null)
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
                Upload your resume file or paste the text directly
              </CardDescription>
            </CardHeader>
            <CardContent>
              <Tabs value={inputMode} onValueChange={(v) => setInputMode(v as 'text' | 'file')} className="w-full">
                <TabsList className="grid w-full grid-cols-2">
                  <TabsTrigger value="file">Upload File</TabsTrigger>
                  <TabsTrigger value="text">Paste Text</TabsTrigger>
                </TabsList>

                <TabsContent value="file" className="space-y-4 mt-4">
                  <div className="space-y-2">
                    <Label htmlFor="resume-file">Resume File</Label>
                    <div className="flex items-center gap-2">
                      <Input
                        id="resume-file"
                        type="file"
                        accept=".pdf,.docx,.doc,.txt"
                        onChange={handleFileChange}
                        className="cursor-pointer"
                      />
                    </div>
                    {resumeFile && (
                      <div className="flex items-center gap-2 text-sm text-muted-foreground">
                        <Upload className="w-4 h-4" />
                        <span>{resumeFile.name} ({(resumeFile.size / 1024).toFixed(2)} KB)</span>
                      </div>
                    )}
                    <p className="text-xs text-muted-foreground">
                      Supported formats: PDF, DOCX, DOC, TXT (Max 5MB)
                    </p>
                  </div>
                </TabsContent>

                <TabsContent value="text" className="space-y-4 mt-4">
                  <div className="space-y-2">
                    <Label htmlFor="resume-text">Resume Text</Label>
                    <Textarea
                      id="resume-text"
                      value={resume}
                      onChange={(e) => setResume(e.target.value)}
                      placeholder="Paste your resume here... (minimum 50 characters)"
                      className="min-h-[280px] resize-none font-mono text-sm"
                    />
                    <p className="text-xs text-muted-foreground">
                      {resume.length} characters
                    </p>
                  </div>
                </TabsContent>
              </Tabs>
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
              disabled={
                loading ||
                !jobDescription.trim() ||
                (inputMode === 'text' && !resume.trim()) ||
                (inputMode === 'file' && !resumeFile)
              }
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
