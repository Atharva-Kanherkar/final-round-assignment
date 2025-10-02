/**
 * API client for backend communication
 */

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'https://orca-app-jubw8.ondigitalocean.app';

export interface CreateSessionRequest {
  resume_text: string;
  job_description_text: string;
}

export interface SessionResponse {
  session_id: string;
  candidate_name: string;
  job_title: string;
  company: string;
  topics: any[];
  first_question: QuestionResponse;
  status: string;
}

export interface QuestionResponse {
  question: string;
  topic: string;
  question_number: number;
  topic_progress: string;
  questions_in_topic: number;
}

export interface EvaluationResponse {
  evaluation: {
    id: string;
    overall_score: number;
    technical_accuracy: number;
    depth: number;
    clarity: number;
    relevance: number;
    strengths: string[];
    gaps: string[];
    feedback: string;
  };
  next_question: QuestionResponse | null;
  transitioned: boolean;
  transition_reasoning: string | null;
  interview_complete: boolean;
}

export interface FinalReportResponse {
  overall_score: number;
  recommendation: string;
  topics_covered: string[];
  topic_summaries: any[];
  overall_strengths: string[];
  areas_for_improvement: string[];
  additional_notes: string;
}

export const api = {
  /**
   * Create new interview session with text
   */
  async createSession(data: CreateSessionRequest): Promise<SessionResponse> {
    const response = await fetch(`${API_URL}/api/sessions`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(data),
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || 'Failed to create session');
    }

    return response.json();
  },

  /**
   * Create new interview session with file upload
   */
  async createSessionWithFiles(
    resumeFile: File,
    jobDescriptionText: string
  ): Promise<SessionResponse> {
    const formData = new FormData();
    formData.append('resume_file', resumeFile);
    formData.append('job_description_text', jobDescriptionText);

    const response = await fetch(`${API_URL}/api/sessions/upload`, {
      method: 'POST',
      body: formData,
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || 'Failed to create session with files');
    }

    return response.json();
  },

  /**
   * Submit response to a question
   */
  async submitResponse(sessionId: string, response: string): Promise<EvaluationResponse> {
    const res = await fetch(`${API_URL}/api/sessions/${sessionId}/respond`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ response }),
    });

    if (!res.ok) {
      const error = await res.json();
      throw new Error(error.detail || 'Failed to submit response');
    }

    return res.json();
  },

  /**
   * Complete interview and get final report
   */
  async completeInterview(sessionId: string): Promise<FinalReportResponse> {
    const response = await fetch(`${API_URL}/api/sessions/${sessionId}/complete`, {
      method: 'POST',
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || 'Failed to complete interview');
    }

    return response.json();
  },

  /**
   * Get session details
   */
  async getSession(sessionId: string) {
    const response = await fetch(`${API_URL}/api/sessions/${sessionId}`);

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || 'Failed to get session');
    }

    return response.json();
  },

  /**
   * Health check
   */
  async healthCheck(): Promise<boolean> {
    try {
      const response = await fetch(`${API_URL}/api/ping`);
      return response.ok;
    } catch {
      return false;
    }
  },
};

export { API_URL };
