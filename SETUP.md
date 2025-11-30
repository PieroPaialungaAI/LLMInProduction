# LLM Grading System - Setup Guide

## Quick Start

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Set Your OpenAI API Key

You have **three options**:

#### Option A: Environment Variable (Recommended)

**macOS/Linux:**
```bash
export OPENAI_API_KEY='sk-your-api-key-here'
```

**Windows (Command Prompt):**
```cmd
set OPENAI_API_KEY=sk-your-api-key-here
```

**Windows (PowerShell):**
```powershell
$env:OPENAI_API_KEY='sk-your-api-key-here'
```

#### Option B: .env File (Persistent)

Create a `.env` file in the project root:

```env
OPENAI_API_KEY=sk-your-api-key-here
```

The system will automatically load this file.

#### Option C: Inline (One-time)

```bash
OPENAI_API_KEY='sk-your-key' python main.py --submission data/sample_student_submission.json
```

### 3. Run the Grader

```bash
# Basic usage
python main.py --submission data/sample_student_submission.json

# With custom model and output
python main.py --submission data/sample_student_submission.json \
               --model gpt-4 \
               --output results/grades.json \
               --verbose
```

## Command-Line Arguments

| Argument | Required | Default | Description |
|----------|----------|---------|-------------|
| `--submission` | ✅ Yes | - | Path to student submission JSON file |
| `--model` | ❌ No | `gpt-4` | OpenAI model to use |
| `--temperature` | ❌ No | `0.1` | Temperature (0.0-1.0, lower = more deterministic) |
| `--output` | ❌ No | stdout | Save results to JSON file |
| `--student-id` | ❌ No | - | Student ID for rate limiting |
| `--verbose` | ❌ No | False | Show detailed logs |
| `--quiet` | ❌ No | False | Minimal output |

## Examples

### Grade with default settings
```bash
python main.py --submission data/sample_student_submission.json
```

### Use GPT-3.5 (cheaper, faster)
```bash
python main.py --submission data/sample_student_submission.json --model gpt-3.5-turbo
```

### Save results to file
```bash
python main.py --submission data/sample_student_submission.json \
               --output results/jane_doe_2024.json
```

### With student ID and verbose logging
```bash
python main.py --submission data/sample_student_submission.json \
               --student-id jane.doe@university.edu \
               --verbose
```

## Troubleshooting

### "OPENAI_API_KEY not found"

Make sure you've set your API key using one of the methods above. To verify:

```bash
# macOS/Linux
echo $OPENAI_API_KEY

# Windows CMD
echo %OPENAI_API_KEY%

# Windows PowerShell
echo $env:OPENAI_API_KEY
```

### "Rate limit exceeded"

The system includes built-in rate limiting (20 submissions per hour per student). If you hit the OpenAI API rate limit, try:
- Using a lower-tier model (gpt-3.5-turbo)
- Adding delays between submissions
- Upgrading your OpenAI plan

### "Module not found"

Make sure all dependencies are installed:
```bash
pip install -r requirements.txt
```

## Cost Estimation

Approximate costs per submission (10 questions):

| Model | Cost per Submission | Speed |
|-------|---------------------|-------|
| GPT-3.5 Turbo | $0.05 - $0.10 | Fast (30s) |
| GPT-4 | $0.50 - $1.00 | Medium (60s) |
| GPT-4 Turbo | $0.30 - $0.60 | Fast (40s) |

*Costs vary based on answer length and tool usage*

## Support

For issues or questions, check:
1. Ensure `OPENAI_API_KEY` is set correctly
2. Verify your OpenAI account has credits
3. Check that all files in `data/` are present
4. Review error messages with `--verbose` flag

