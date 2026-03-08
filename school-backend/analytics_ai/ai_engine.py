import json
import boto3
from django.conf import settings
import logging

logger = logging.getLogger(__name__)

class StudentRiskAIEngine:
    """
    Wrapper for Amazon Bedrock to generate student risk predictions and recommendations.
    Uses Claude 3 Haiku for cost-effective analysis.
    """
    
    def __init__(self, region_name="us-east-1"):
        # Credentials should be provided via environment variables (AWS_ACCESS_KEY_ID, etc.)
        self.bedrock = boto3.client(
            service_name='bedrock-runtime',
            region_name=region_name
        )
        self.model_id = "anthropic.claude-3-haiku-20240307-v1:0"

    def generate_risk_assessment_prompt(self, student_data):
        """
        Constructs the prompt for Claude 3.
        """
        metrics = student_data.get('metrics', {})
        perf = metrics.get('performance', {})
        fin = metrics.get('finance', {})
        
        prompt = f"""
        Human: You are an expert educational psychologist and data analyst. 
        Analyze the following student data and provide a risk assessment.
        
        STUDENT METRICS:
        - Attendance (Last 30 days): {metrics.get('attendance_rate_30d')}%
        - Latest Exam Average: {perf.get('latest_avg')}%
        - Performance Change: {perf.get('change')}%
        - Outstanding Balance: ${fin.get('balance')}
        
        GOAL:
        1. Predict the risk level (LOW, MEDIUM, HIGH, CRITICAL).
        2. Identify key risk factors.
        3. Provide 3 actionable study recommendations.
        
        FORMAT YOUR RESPONSE AS JSON:
        {{
            "risk_score": integer (0-100),
            "risk_level": "LOW|MEDIUM|HIGH|CRITICAL",
            "primary_factors": ["factor 1", "factor 2"],
            "recommendations": "Concise text for the student and teacher."
        }}
        
        Assistant:
        """
        return prompt

    def get_prediction(self, student_data):
        """
        Invocates Bedrock and parses the response.
        """
        prompt = self.generate_risk_assessment_prompt(student_data)
        
        body = json.dumps({
            "anthropic_version": "bedrock-2023-05-31",
            "max_tokens": 1000,
            "messages": [
                {
                    "role": "user",
                    "content": [{"type": "text", "text": prompt}]
                }
            ]
        })

        try:
            response = self.bedrock.invoke_model(
                body=body,
                modelId=self.model_id
            )
            response_body = json.loads(response.get('body').read())
            content = response_body['content'][0]['text']
            
            # Extract JSON from response if LLM included conversational text
            # (Simple parsing for design demonstration)
            return json.loads(content)
            
        except Exception as e:
            logger.error(f"Bedrock invocation failed: {str(e)}")
            # Fallback to a deterministic heuristic if AI fails
            return self._heuristic_fallback(student_data)

    def _heuristic_fallback(self, student_data):
        """
        Provides a basic score if the AI service is unreachable.
        """
        metrics = student_data.get('metrics', {})
        score = 0
        if metrics.get('attendance_rate_30d', 100) < 75: score += 40
        if metrics.get('performance', {}).get('change', 0) < -10: score += 30
        
        level = "LOW"
        if score > 60: level = "HIGH"
        elif score > 30: level = "MEDIUM"
        
        return {
            "risk_score": score,
            "risk_level": level,
            "primary_factors": ["System fallback due to connectivity"],
            "recommendations": "Monitor attendance and performance closely."
        }
