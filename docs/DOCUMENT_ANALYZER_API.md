# DocumentAnalyzerAgent - API Documentation

## Overview

The **DocumentAnalyzerAgent** is a specialized AI agent that provides document and image analysis exclusively for the authenticated Boss user. It supports PDF summarization, Word document analysis, and AI-powered image description using vision-capable LLMs.

## Features

### 📄 Document Analysis
- **PDF Files**: Extract and summarize content from multi-page PDFs
- **Word Documents**: Analyze .doc and .docx files
- **Text Files**: Process plain text, HTML, and Markdown files
- **Smart Extraction**: Key points, action items, dates, and important entities

### 🖼️ Image Analysis
- **Visual Description**: Detailed explanation of image content
- **Text Extraction**: OCR capability to read text from images
- **Context Understanding**: Identify purpose, setting, and meaning
- **Vision AI**: Powered by Google Gemini Vision or Claude Vision

### 🔒 Security
- **Boss-Only Access**: Phone number verification
- **Intent Validation**: Orchestrator confirms analysis request
- **Unauthorized Response**: Generic message for non-Boss users

## Task Type

```python
TaskType.DOCUMENT_ANALYSIS
```

## Input Data Format

The agent expects the following fields in `Task.input_data`:

```python
{
    "file_path": str,          # Required: Absolute path to the file
    "file_type": str,          # Required: MIME type (e.g., "application/pdf", "image/jpeg")
    "analysis_type": str,      # Optional: "summary" (default), "detailed", or "explain" (for images)
    "requester_phone": str,    # Required: Phone number for authentication
    "requester_name": str      # Optional: Name of requester
}
```

## Supported File Types

### Documents
| MIME Type | Extension | Description |
|-----------|-----------|-------------|
| `application/pdf` | .pdf | Adobe PDF documents |
| `application/msword` | .doc | Microsoft Word 97-2003 |
| `application/vnd.openxmlformats-officedocument.wordprocessingml.document` | .docx | Microsoft Word 2007+ |
| `text/plain` | .txt | Plain text files |
| `text/html` | .html | HTML documents |
| `text/markdown` | .md | Markdown files |

### Images
| MIME Type | Extension | Description |
|-----------|-----------|-------------|
| `image/jpeg` | .jpg, .jpeg | JPEG images |
| `image/png` | .png | PNG images |
| `image/gif` | .gif | GIF images |
| `image/webp` | .webp | WebP images |
| `image/svg+xml` | .svg | SVG vector graphics |

## Analysis Types

### 1. Summary Analysis (`analysis_type: "summary"`)
**For Documents:**
- Brief summary (2-3 sentences)
- Key points (bullet points)
- Main topics covered
- Important dates, names, numbers

**Example Use Case**: Quick overview of a contract or report

### 2. Detailed Analysis (`analysis_type: "detailed"`)
**For Documents:**
- Executive summary
- Main themes and topics
- Key findings
- Important details (dates, numbers, entities)
- Recommendations or action items
- Overall assessment

**Example Use Case**: Comprehensive analysis of a business proposal

### 3. Explain Analysis (`analysis_type: "explain"`)
**For Images:**
- What is visible in the image
- Setting and context
- Text visible in the image (OCR)
- Notable details or important elements
- Overall purpose or meaning

**Example Use Case**: Understanding a chart, diagram, or photo

## API Workflow

### Creating a Document Analysis Task

```python
from database.models import TaskType, TaskPriority
from tasks.task_manager import TaskManager

task_manager = TaskManager()

# Create document analysis task
task = await task_manager.create_task(
    task_type=TaskType.DOCUMENT_ANALYSIS,
    chat_id="123456@c.us",
    input_data={
        "file_path": "/path/to/document.pdf",
        "file_type": "application/pdf",
        "analysis_type": "summary",
        "requester_phone": "+85212345678",
        "requester_name": "Boss"
    },
    priority=TaskPriority.HIGH.value
)

print(f"Task created: {task.id}")
```

### Checking Task Status

```python
# Get task status
task = await task_manager.get_task(task_id)

print(f"Status: {task.status.value}")
print(f"Started: {task.started_at}")
print(f"Completed: {task.completed_at}")

if task.status == TaskStatus.COMPLETED:
    result = eval(task.output_data)  # Parse output data
    print(f"Analysis: {result['response']}")
elif task.status == TaskStatus.FAILED:
    print(f"Error: {task.error_message}")
```

## Response Format

### Success Response

```python
{
    "success": True,
    "analysis_type": "summary",        # or "detailed", "explain"
    "file_type": "application/pdf",
    "response": "AI-generated analysis text...",
    "document_length": 12500,          # For documents: character count
    "extracted_text_sample": "...",    # First 500 chars of extracted text
    # OR for images:
    "image_size": 245678               # File size in bytes
}
```

### Error Response

```python
{
    "success": False,
    "error": "Error description",
    "response": "User-friendly error message"
}
```

### Unauthorized Response

```python
{
    "success": False,
    "error": "Unauthorized",
    "response": "Sorry, Mr Hung is not available at this moment..."
}
```

## Example Usage Scenarios

### Scenario 1: PDF Summary for Boss

**WhatsApp Message from Boss:**
```
Boss sends a PDF file with message: "Summarize this contract"
```

**Backend Processing:**
1. WhatsApp service downloads the PDF to `/tmp/contract_123.pdf`
2. Orchestrator detects file + analysis intent
3. Creates `DOCUMENT_ANALYSIS` task with:
   ```python
   {
       "file_path": "/tmp/contract_123.pdf",
       "file_type": "application/pdf",
       "analysis_type": "summary",
       "requester_phone": "+85212345678"
   }
   ```
4. DocumentAnalyzerAgent processes:
   - Verifies Boss phone number ✓
   - Extracts text from PDF using PyPDF2
   - Sends to LLM for summarization
   - Returns summary

**Response to Boss:**
```
📄 Contract Summary:

Brief Summary:
This is a 3-year service agreement between Company A and Company B for cloud infrastructure services, valued at $500K annually.

Key Points:
• Contract duration: Jan 1, 2025 - Dec 31, 2027
• Annual value: $500,000
• Services: Cloud hosting, backup, support
• Payment terms: Quarterly in advance
• Termination: 90-day notice required

Main Topics:
- Service Level Agreements (99.9% uptime)
- Data security and compliance
- Pricing and payment schedule
- Intellectual property rights
```

### Scenario 2: Image Explanation

**WhatsApp Message from Boss:**
```
Boss sends an image of a business chart with message: "Explain this chart"
```

**Backend Processing:**
1. WhatsApp service downloads image to `/tmp/chart_456.jpg`
2. Orchestrator detects image + analysis intent
3. Creates `DOCUMENT_ANALYSIS` task
4. DocumentAnalyzerAgent:
   - Verifies Boss ✓
   - Loads image with PIL
   - Sends to Gemini Vision with analysis prompt
   - Returns explanation

**Response to Boss:**
```
📊 Chart Analysis:

Visual Description:
This is a bar chart showing quarterly sales performance across 4 regions (North, South, East, West) for 2024.

Key Findings:
• North region leads with $2.5M in Q4
• South region shows consistent growth (15% QoQ)
• East region declined in Q3 (-8%)
• West region recovered in Q4 (+22%)

Text Content:
Title: "2024 Regional Sales Performance"
Y-axis: Revenue (Millions USD)
X-axis: Quarters (Q1-Q4)

Overall Assessment:
Total company sales grew 12% YoY. North and West regions are performing well, while East needs attention.
```

### Scenario 3: Unauthorized Access Attempt

**WhatsApp Message from Random User:**
```
Random user sends PDF: "Analyze this document"
```

**Backend Processing:**
1. Orchestrator creates task
2. DocumentAnalyzerAgent checks phone number
3. Phone ≠ Boss phone → Unauthorized

**Response:**
```
Sorry, Mr Hung is not available at this moment...
```

## Configuration

### Environment Variables

```bash
# Required for image analysis
GEMINI_API_KEY=your_gemini_api_key_here  # For vision support
# OR
ANTHROPIC_API_KEY=your_claude_api_key_here  # Alternative vision provider

# Boss authentication
BOSS_PHONE_NUMBER=+85212345678
UNAUTHORIZED_MESSAGE=Sorry, Mr Hung is not available at this moment...
```

### Dependencies

Install required Python packages:

```bash
pip install PyPDF2>=3.0.0          # PDF extraction
pip install python-docx>=1.1.0     # Word document processing
pip install pdfplumber>=0.10.3     # Alternative PDF library
pip install Pillow>=10.0.0         # Image processing
pip install google-generativeai    # Gemini Vision (if using Google)
pip install anthropic              # Claude Vision (if using Anthropic)
```

## Error Handling

### Common Errors

| Error | Cause | Solution |
|-------|-------|----------|
| `File not found` | Invalid `file_path` | Verify file was downloaded successfully |
| `Unsupported file type` | MIME type not in supported list | Check supported file types table |
| `No text content found` | Empty or image-only PDF | Use image analysis instead |
| `Vision analysis not supported` | No vision-capable LLM configured | Configure Gemini or Anthropic API key |
| `Unauthorized` | Phone number doesn't match Boss | Only Boss can use this agent |
| `LLM service not available` | LLM service initialization failed | Check API keys and service status |

### Error Recovery

```python
result = await agent.execute(task)

if not result['success']:
    error_type = result.get('error', '')

    if error_type == 'Unauthorized':
        # Send generic message
        await send_message(chat_id, settings.UNAUTHORIZED_MESSAGE)

    elif error_type == 'File not found':
        # Re-download file
        await redownload_file(file_id)

    elif 'Vision' in error_type:
        # Fall back to text extraction only
        text = extract_text_from_image_ocr(file_path)
        # Process as text document
```

## Integration with Orchestrator

The Orchestrator automatically routes document/image analysis requests to this agent:

```python
# In OrchestratorAgent
async def _classify_intent(self, message: str, has_media: bool) -> str:
    if has_media:
        # Check if requester is Boss
        if self._is_boss(phone_number):
            # Check for analysis keywords
            if any(kw in message.lower() for kw in ['summarize', 'analyze', 'explain', 'what is this']):
                return TaskType.DOCUMENT_ANALYSIS

    # ... other intent classification
```

## Performance Considerations

### Processing Times

| File Type | Size | Typical Processing Time |
|-----------|------|-------------------------|
| PDF (text) | 10 pages | 5-15 seconds |
| PDF (scanned) | 10 pages | 15-30 seconds |
| Word document | 5 pages | 3-10 seconds |
| Image (JPG) | 2MB | 3-8 seconds |
| Image (PNG) | 5MB | 5-12 seconds |

### Resource Usage

- **Memory**: ~50-200MB per document (depending on size)
- **CPU**: Text extraction is CPU-intensive for large PDFs
- **LLM Tokens**:
  - Summary: ~500-1000 tokens
  - Detailed: ~1500-2500 tokens
  - Image: ~1000-2000 tokens

### Optimization Tips

1. **Limit text sent to LLM**: Currently truncates to 8000 characters
2. **Use pdfplumber for complex PDFs**: Better extraction than PyPDF2
3. **Cache results**: Store analysis in task.output_data for repeat requests
4. **Compress images**: Resize large images before sending to vision API
5. **Batch processing**: Queue multiple analysis tasks for sequential processing

## Future Enhancements

### Planned Features

- [ ] **Multi-page image analysis**: Analyze multiple images as a set
- [ ] **Table extraction**: Extract and analyze tables from PDFs
- [ ] **Document comparison**: Compare two documents and highlight differences
- [ ] **Export to formats**: Save analysis as PDF, DOCX, or JSON
- [ ] **Template-based analysis**: Custom analysis templates for specific document types
- [ ] **Language detection**: Auto-detect document language
- [ ] **Translation**: Translate document to English before analysis
- [ ] **Incremental analysis**: Analyze large documents in chunks

### API Extensions

```python
# Future: Batch analysis
task = await task_manager.create_task(
    task_type=TaskType.DOCUMENT_BATCH_ANALYSIS,
    input_data={
        "file_paths": ["/path/to/doc1.pdf", "/path/to/doc2.pdf"],
        "analysis_type": "comparison",
        "requester_phone": "+85212345678"
    }
)

# Future: Custom templates
task = await task_manager.create_task(
    task_type=TaskType.DOCUMENT_ANALYSIS,
    input_data={
        "file_path": "/path/to/invoice.pdf",
        "analysis_type": "template",
        "template": "invoice",  # Pre-defined template
        "requester_phone": "+85212345678"
    }
)
```

## Testing

### Unit Tests

```python
import pytest
from agents.document_analyzer import DocumentAnalyzerAgent

@pytest.mark.asyncio
async def test_pdf_analysis():
    agent = DocumentAnalyzerAgent(llm_service)

    task = create_test_task(
        input_data={
            "file_path": "tests/fixtures/sample.pdf",
            "file_type": "application/pdf",
            "analysis_type": "summary",
            "requester_phone": settings.BOSS_PHONE_NUMBER
        }
    )

    result = await agent.execute(task)

    assert result['success'] == True
    assert 'response' in result
    assert len(result['response']) > 100

@pytest.mark.asyncio
async def test_unauthorized_access():
    agent = DocumentAnalyzerAgent(llm_service)

    task = create_test_task(
        input_data={
            "file_path": "tests/fixtures/sample.pdf",
            "file_type": "application/pdf",
            "requester_phone": "+85299999999"  # Not Boss
        }
    )

    result = await agent.execute(task)

    assert result['success'] == False
    assert result['error'] == 'Unauthorized'
```

### Integration Tests

```bash
# Test PDF analysis
curl -X POST http://localhost:8001/api/tasks/analyze-document \
  -H "Content-Type: application/json" \
  -d '{
    "file_path": "/tmp/test.pdf",
    "file_type": "application/pdf",
    "analysis_type": "summary",
    "requester_phone": "+85212345678"
  }'

# Test image analysis
curl -X POST http://localhost:8001/api/tasks/analyze-document \
  -H "Content-Type: application/json" \
  -d '{
    "file_path": "/tmp/chart.jpg",
    "file_type": "image/jpeg",
    "analysis_type": "explain",
    "requester_phone": "+85212345678"
  }'
```

## Support

For issues or questions:
1. Check logs: `railway logs` or local backend logs
2. Verify file permissions: Agent needs read access to files
3. Check LLM service status: Ensure Gemini/Anthropic is configured
4. Test with sample files: Use provided test fixtures
5. Review task error messages: `task.error_message` field

---

**Version**: 2.2.0
**Last Updated**: 2025-12-30
**Agent Type**: `document_analyzer`
**Status**: ✅ Production Ready
