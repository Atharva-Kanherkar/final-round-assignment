#!/bin/bash
# Test deployed API endpoints

API_URL="https://orca-app-jubw8.ondigitalocean.app"

echo "Testing AI Mock Interview API at: $API_URL"
echo "================================================"
echo ""

# Test 1: Health Check
echo "1. Testing health check..."
curl -s "$API_URL/api/ping" | python3 -m json.tool
if [ $? -eq 0 ]; then
    echo "✓ Health check passed"
else
    echo "✗ Health check failed"
    exit 1
fi
echo ""

# Test 2: Create Session
echo "2. Creating interview session..."
SESSION_RESPONSE=$(curl -s -X POST "$API_URL/api/sessions" \
  -H "Content-Type: application/json" \
  -d '{
    "resume_text": "John Doe\nSenior Software Engineer\n5 years experience\n\nSkills: Python, JavaScript, React, Node.js, AWS, Docker, Kubernetes, PostgreSQL\n\nExperience:\n- TechCorp (2020-2023): Led backend development for microservices architecture serving 1M+ users. Designed RESTful APIs using Python/Django.\n- StartupXYZ (2018-2020): Full-stack development using React and Node.js.\n\nEducation: BS Computer Science, State University (2014-2018)",
    "job_description_text": "Senior Backend Engineer\nCompany: TechCo\n\nRequirements:\n- 5+ years Python experience\n- Strong system design skills\n- Experience with distributed systems\n- AWS/Cloud experience required\n\nResponsibilities:\n- Design scalable backend services\n- Lead technical initiatives\n- Mentor junior engineers"
  }')

echo "$SESSION_RESPONSE" | python3 -m json.tool

SESSION_ID=$(echo "$SESSION_RESPONSE" | python3 -c "import sys, json; print(json.load(sys.stdin).get('session_id', ''))" 2>/dev/null)

if [ -z "$SESSION_ID" ]; then
    echo "✗ Session creation failed"
    exit 1
else
    echo "✓ Session created: $SESSION_ID"
fi
echo ""

# Test 3: Get Session
echo "3. Retrieving session..."
curl -s "$API_URL/api/sessions/$SESSION_ID" | python3 -m json.tool
if [ $? -eq 0 ]; then
    echo "✓ Session retrieval passed"
else
    echo "✗ Session retrieval failed"
fi
echo ""

# Test 4: Submit Response
echo "4. Submitting answer..."
EVAL_RESPONSE=$(curl -s -X POST "$API_URL/api/sessions/$SESSION_ID/respond" \
  -H "Content-Type: application/json" \
  -d '{"response": "Python is a high-level, interpreted programming language known for its simplicity and readability. It supports multiple programming paradigms including procedural, object-oriented, and functional programming. Python is widely used in web development, data science, machine learning, and automation due to its extensive standard library and rich ecosystem of third-party packages."}')

echo "$EVAL_RESPONSE" | python3 -m json.tool
if [ $? -eq 0 ]; then
    echo "✓ Response submission passed"
else
    echo "✗ Response submission failed"
fi
echo ""

echo "================================================"
echo "API Test Complete!"
echo ""
echo "Your API is working at: $API_URL"
echo "API Docs: $API_URL/api/docs"
