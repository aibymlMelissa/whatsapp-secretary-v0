# backend/agents/document_analyzer.py
"""
Document and Image Analyzer Agent

Specialized agent that analyzes documents and images for the authenticated Boss user.
Handles PDF summarization, document analysis, and image explanation.
"""

import os
import base64
from typing import Dict, Any, Optional, List
from datetime import datetime
import mimetypes

from agents.base_agent import BaseAgent
from database.models import Task, TaskType, TaskStatus
from services.llm_service import LLMService
from core.config import settings


class DocumentAnalyzerAgent(BaseAgent):
    """
    Agent specialized in analyzing documents and images

    Capabilities:
    - PDF document summarization
    - Word/text document analysis
    - Image description and explanation
    - Document content extraction
    - Multi-page document processing
    """

    def __init__(self, llm_service: Optional[LLMService] = None):
        super().__init__("DocumentAnalyzer")
        self.llm_service = llm_service

        # Supported file types
        self.supported_documents = {
            'application/pdf': 'pdf',
            'application/msword': 'doc',
            'application/vnd.openxmlformats-officedocument.wordprocessingml.document': 'docx',
            'text/plain': 'txt',
            'text/html': 'html',
            'text/markdown': 'md'
        }

        self.supported_images = {
            'image/jpeg': 'jpg',
            'image/png': 'png',
            'image/gif': 'gif',
            'image/webp': 'webp',
            'image/svg+xml': 'svg'
        }

    @property
    def agent_type(self) -> str:
        return "document_analyzer"

    async def can_handle(self, task: Task) -> bool:
        """
        Determine if this agent can handle the task

        Only handles DOCUMENT_ANALYSIS tasks
        """
        return task.task_type == TaskType.DOCUMENT_ANALYSIS

    async def process(self, task: Task) -> Dict[str, Any]:
        """
        Process document/image analysis task

        Task input_data should contain:
        - file_path: Path to the document/image file
        - file_type: MIME type of the file
        - analysis_type: 'summary', 'detailed', 'explain' (for images)
        - requester_phone: Phone number of requester (for auth check)
        - requester_name: Name of requester
        """
        try:
            # Parse input data
            input_data = self._parse_input_data(task.input_data)

            # Validate authorization
            auth_result = await self._validate_authorization(input_data)
            if not auth_result['authorized']:
                return {
                    'success': False,
                    'error': 'Unauthorized',
                    'response': auth_result['message']
                }

            # Get file info
            file_path = input_data.get('file_path')
            file_type = input_data.get('file_type')
            analysis_type = input_data.get('analysis_type', 'summary')

            if not file_path:
                return {
                    'success': False,
                    'error': 'No file provided',
                    'response': 'Please provide a document or image to analyze.'
                }

            # Verify file exists
            if not os.path.exists(file_path):
                return {
                    'success': False,
                    'error': 'File not found',
                    'response': f'The file {file_path} was not found.'
                }

            # Determine if it's a document or image
            if file_type in self.supported_documents:
                result = await self._analyze_document(file_path, file_type, analysis_type)
            elif file_type in self.supported_images:
                result = await self._analyze_image(file_path, file_type, analysis_type)
            else:
                return {
                    'success': False,
                    'error': 'Unsupported file type',
                    'response': f'Sorry, I cannot analyze {file_type} files. Supported types: PDF, DOC, DOCX, TXT, JPG, PNG, GIF, WEBP.'
                }

            return result

        except Exception as e:
            print(f"❌ Error in DocumentAnalyzerAgent: {e}")
            import traceback
            traceback.print_exc()

            return {
                'success': False,
                'error': str(e),
                'response': f'An error occurred while analyzing the file: {str(e)}'
            }

    async def _validate_authorization(self, input_data: Dict[str, Any]) -> Dict[str, bool]:
        """
        Validate that the requester is authorized (Boss)

        Returns:
            {
                'authorized': bool,
                'message': str  # Message to return if unauthorized
            }
        """
        requester_phone = input_data.get('requester_phone', '')
        boss_phone = settings.BOSS_PHONE_NUMBER

        # Normalize phone numbers (remove spaces, dashes, etc.)
        requester_normalized = ''.join(filter(str.isdigit, requester_phone))
        boss_normalized = ''.join(filter(str.isdigit, boss_phone))

        if requester_normalized != boss_normalized:
            return {
                'authorized': False,
                'message': settings.UNAUTHORIZED_MESSAGE or 'Sorry, this feature is only available to authorized users.'
            }

        return {
            'authorized': True,
            'message': 'Authorized'
        }

    async def _analyze_document(self, file_path: str, file_type: str, analysis_type: str) -> Dict[str, Any]:
        """
        Analyze a document file (PDF, DOC, TXT, etc.)

        Args:
            file_path: Path to the document
            file_type: MIME type
            analysis_type: 'summary' or 'detailed'

        Returns:
            Analysis result
        """
        try:
            # Extract text from document
            text_content = await self._extract_document_text(file_path, file_type)

            if not text_content:
                return {
                    'success': False,
                    'error': 'No text content found',
                    'response': 'The document appears to be empty or I could not extract text from it.'
                }

            # Analyze with LLM
            if analysis_type == 'summary':
                prompt = f"""You are analyzing a document for your boss. Please provide a concise summary.

Document content:
{text_content[:8000]}

Provide:
1. Brief summary (2-3 sentences)
2. Key points (bullet points)
3. Main topics covered
4. Any important dates, names, or numbers mentioned

Keep it professional and focused on what's important for decision-making."""

            else:  # detailed
                prompt = f"""You are analyzing a document for your boss. Please provide a detailed analysis.

Document content:
{text_content[:8000]}

Provide a comprehensive analysis including:
1. Executive Summary
2. Main Themes and Topics
3. Key Findings
4. Important Details (dates, numbers, entities)
5. Recommendations or Action Items (if applicable)
6. Overall Assessment

Be thorough but organized."""

            # Get LLM response
            if self.llm_service:
                llm_response = await self.llm_service.generate_response(
                    messages=[{"role": "user", "content": prompt}],
                    max_tokens=2000
                )

                response_text = llm_response.get('content', '') or llm_response.get('text', '')

                return {
                    'success': True,
                    'analysis_type': analysis_type,
                    'file_type': file_type,
                    'response': response_text,
                    'document_length': len(text_content),
                    'extracted_text_sample': text_content[:500]
                }
            else:
                return {
                    'success': False,
                    'error': 'LLM service not available',
                    'response': 'The AI analysis service is currently unavailable.'
                }

        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'response': f'Error analyzing document: {str(e)}'
            }

    async def _analyze_image(self, file_path: str, file_type: str, analysis_type: str) -> Dict[str, Any]:
        """
        Analyze an image file

        Args:
            file_path: Path to the image
            file_type: MIME type
            analysis_type: 'explain' or 'detailed'

        Returns:
            Analysis result
        """
        try:
            # Read and encode image
            with open(file_path, 'rb') as f:
                image_data = base64.b64encode(f.read()).decode('utf-8')

            # Create prompt based on analysis type
            if analysis_type == 'explain':
                prompt = """You are analyzing an image for your boss. Please provide a clear explanation.

Describe:
1. What you see in the image (main subjects, objects, people)
2. The setting or context
3. Any text visible in the image
4. Notable details or important elements
5. Overall purpose or meaning of the image

Be concise but informative."""

            else:  # detailed
                prompt = """You are analyzing an image for your boss. Please provide a detailed analysis.

Provide a comprehensive analysis:
1. Visual Description (what is shown)
2. Context and Setting
3. Text Content (if any text is visible, transcribe it)
4. Key Elements and Details
5. Composition and Quality
6. Potential Purpose or Message
7. Anything noteworthy or unusual

Be thorough and professional."""

            # Use LLM with vision capabilities (Gemini or Claude)
            if self.llm_service:
                # Check if LLM supports vision
                if hasattr(self.llm_service, 'supports_vision') and self.llm_service.supports_vision():
                    llm_response = await self.llm_service.analyze_image(
                        image_path=file_path,
                        prompt=prompt
                    )

                    response_text = llm_response.get('content', '') or llm_response.get('text', '')

                    return {
                        'success': True,
                        'analysis_type': analysis_type,
                        'file_type': file_type,
                        'response': response_text,
                        'image_size': os.path.getsize(file_path)
                    }
                else:
                    return {
                        'success': False,
                        'error': 'Vision analysis not supported',
                        'response': 'The current AI model does not support image analysis. Please configure Gemini or Claude with vision capabilities.'
                    }
            else:
                return {
                    'success': False,
                    'error': 'LLM service not available',
                    'response': 'The AI analysis service is currently unavailable.'
                }

        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'response': f'Error analyzing image: {str(e)}'
            }

    async def _extract_document_text(self, file_path: str, file_type: str) -> str:
        """
        Extract text content from various document formats

        Args:
            file_path: Path to document
            file_type: MIME type

        Returns:
            Extracted text content
        """
        try:
            # PDF extraction
            if file_type == 'application/pdf':
                try:
                    import PyPDF2
                    text = ""
                    with open(file_path, 'rb') as f:
                        pdf_reader = PyPDF2.PdfReader(f)
                        for page in pdf_reader.pages:
                            text += page.extract_text() + "\n"
                    return text
                except ImportError:
                    # Fallback: try pdfplumber
                    try:
                        import pdfplumber
                        text = ""
                        with pdfplumber.open(file_path) as pdf:
                            for page in pdf.pages:
                                text += page.extract_text() + "\n"
                        return text
                    except ImportError:
                        return f"[PDF file - requires PyPDF2 or pdfplumber library for extraction]\nFile: {os.path.basename(file_path)}"

            # Word documents
            elif file_type in ['application/msword', 'application/vnd.openxmlformats-officedocument.wordprocessingml.document']:
                try:
                    import docx
                    doc = docx.Document(file_path)
                    text = "\n".join([paragraph.text for paragraph in doc.paragraphs])
                    return text
                except ImportError:
                    return f"[Word document - requires python-docx library for extraction]\nFile: {os.path.basename(file_path)}"

            # Plain text files
            elif file_type in ['text/plain', 'text/html', 'text/markdown']:
                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    return f.read()

            else:
                return f"[Unsupported document type: {file_type}]"

        except Exception as e:
            return f"[Error extracting text: {str(e)}]"
