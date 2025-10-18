from fastapi import FastAPI, HTTPException, Request, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
from groq import Groq
from github import Github
import os
import logging
from models.schemas import (
    RepositoryMetadata,
    ErrorResponse,
    WebhookResponse,
    AnalysisRequest,
    AnalysisResponse,
    AnalysisType
)
from utils.get_key_files import get_key_files
from utils.get_respository_structure import get_repository_structure

load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

GROQ_API_KEY = os.getenv("GROQ_API_KEY")
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")

if not GROQ_API_KEY:
    raise ValueError("GROQ_API_KEY environment variable is not set")
if not GITHUB_TOKEN:
    raise ValueError("GITHUB_TOKEN environment variable is not set")

app = FastAPI(
    title="Codebase AI Analyst",
    version="1.0.0",
    description="Advanced AI-powered codebase analysis using Groq LLMs"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"],
)

groq_client = Groq(api_key=GROQ_API_KEY)
github_client = Github(GITHUB_TOKEN)


ANALYSIS_PROMPTS = {
    AnalysisType.GENERAL: """Analyze this codebase comprehensively and structure your response with these exact sections:

    ## Architecture Overview
    Describe the overall system design, folder structure, and how components interact. Be specific about architectural patterns used.

    ## Tech Stack
    List all technologies, frameworks, libraries, and tools identified. Include versions if visible.

    ## Code Quality
    Evaluate code organization, naming conventions, documentation, error handling, and maintainability. Rate quality out of 100.

    ## Potential Improvements
    Provide 3-5 actionable, specific improvements with clear reasoning. Focus on high-impact changes.

    ## Security Considerations
    Identify security concerns in authentication, data handling, API exposure, and dependency management.

    Be detailed, specific, and evidence-based. Skip sections only if data is completely unavailable.""",

    AnalysisType.SECURITY: """Conduct an in-depth security audit. Structure your response:

    ## Critical Vulnerabilities
    List any critical security flaws (SQL injection, XSS, auth bypasses, exposed secrets).

    ## Authentication & Authorization
    Evaluate login mechanisms, session handling, token management, and access control.

    ## Data Protection
    Assess encryption, sensitive data handling, input validation, and output encoding.

    ## API Security
    Review API endpoints for proper authentication, rate limiting, input validation, and error handling.

    ## Dependencies & Configuration
    Check for outdated packages, exposed credentials, insecure defaults, and environment variable leaks.

    ## Recommendations
    Provide specific, prioritized security improvements with implementation guidance.

    Focus on actual vulnerabilities found in the code, not generic advice.""",

    AnalysisType.ARCHITECTURE: """Perform a deep architectural analysis:

    ## System Design
    Map the overall architecture: monolithic, microservices, layered, or other patterns. Describe component relationships.

    ## Design Patterns
    Identify specific design patterns used (MVC, Repository, Factory, Singleton, etc.) and evaluate their implementation.

    ## Separation of Concerns
    Assess how well responsibilities are divided across modules, classes, and functions.

    ## Scalability Analysis
    Evaluate horizontal/vertical scalability potential, bottlenecks, and database design.

    ## Maintainability
    Review code modularity, coupling, cohesion, and extensibility. Identify technical debt.

    ## Architectural Recommendations
    Suggest specific structural improvements with rationale and potential trade-offs.

    Be precise about what exists in the code, not what could theoretically be built.""",

    AnalysisType.QUALITY: """Evaluate code quality in detail:

    ## Overall Quality Score: X/100
    Provide a numeric score at the top with brief justification.

    ## Readability
    Assess naming conventions, code clarity, comment quality, and documentation.

    ## Best Practices Adherence
    Check language-specific conventions, framework patterns, and industry standards.

    ## Code Smells
    Identify specific anti-patterns, duplications, overly complex functions, and god objects.

    ## Testing
    Evaluate test coverage, test quality, and testability of the codebase.

    ## Maintainability Issues
    List technical debt, outdated patterns, and areas requiring refactoring.

    ## Actionable Improvements
    Provide 5-7 specific, prioritized refactoring tasks with expected impact.

    Base findings on actual code patterns, not assumptions.""",

    AnalysisType.PERFORMANCE: """Conduct a thorough performance analysis:

    ## Performance Bottlenecks
    Identify specific slow operations: inefficient queries, N+1 problems, excessive loops, blocking I/O.

    ## Database Performance
    Review query optimization, indexing strategy, connection pooling, and ORM usage.

    ## API Efficiency
    Evaluate request/response sizes, unnecessary data fetching, and API call patterns.

    ## Resource Utilization
    Assess memory usage, CPU-intensive operations, and resource leaks.

    ## Caching Strategy
    Review current caching (if any) and identify opportunities for caching improvements.

    ## Scalability Limits
    Identify concurrency issues, single points of failure, and horizontal scaling barriers.

    ## Optimization Recommendations
    Provide 5-7 specific, high-impact performance improvements with expected gains.

    Focus on real bottlenecks visible in the code structure."""
}


def analyze_codebase(repo_full_name: str, analysis_type: AnalysisType) -> AnalysisResponse:
    try:
        repo = github_client.get_repo(repo_full_name)
        
        metadata = RepositoryMetadata(
            full_name=repo.full_name,
            description=repo.description,
            stars=repo.stargazers_count,
            language=repo.language,
            default_branch=repo.default_branch
        )
        
        structure = get_repository_structure(repo)
        structure_text = "\n".join(structure[:100])
        
        key_files = get_key_files(repo)
        files_text = "\n\n".join([
            f"=== {f.path} ({f.size_kb:.1f}KB) ===\n{f.content}"
            for f in key_files[:15]
        ])
        
        readme_content = ""
        try:
            readme = repo.get_readme()
            readme_content = readme.decoded_content.decode('utf-8')[:2000]
        except:
            readme_content = "No README found"
        
        prompt = f"""Repository: {repo_full_name}
Language: {metadata.language or 'Multiple/Unknown'}
Stars: {metadata.stars}
Description: {metadata.description or 'No description'}

README (first 2000 chars):
{readme_content}

Repository Structure (top 100 items):
{structure_text}

Key Files Analyzed ({len(key_files)} files):
{files_text}

---

{ANALYSIS_PROMPTS[analysis_type]}

Provide a thorough, evidence-based analysis. Reference specific files and code patterns you observe."""

        models = [
            ("llama-3.3-70b-versatile", 6000),
            ("llama-3.1-70b-versatile", 6000),
            ("mixtral-8x7b-32768", 6000),
            ("llama-3.1-8b-instant", 4000)
        ]
        
        analysis = None
        last_error = None
        
        for model_name, max_tokens in models:
            try:
                chat_completion = groq_client.chat.completions.create(
                    messages=[{"role": "user", "content": prompt}],
                    model=model_name,
                    temperature=0.3,
                    max_tokens=max_tokens,
                )
                analysis = chat_completion.choices[0].message.content
                logger.info(f"Successfully used model: {model_name}")
                break
            except Exception as model_error:
                last_error = str(model_error)
                logger.warning(f"Failed with {model_name}: {last_error}")
                if "rate_limit" not in last_error.lower():
                    break
                continue
        
        if not analysis:
            raise Exception(f"All models failed. Last error: {last_error}")
        
        return AnalysisResponse(
            success=True,
            repository=repo_full_name,
            analysis_type=analysis_type,
            analysis=analysis,
            files_analyzed=len(key_files),
            stars=metadata.stars,
            language=metadata.language,
            metadata={"default_branch": metadata.default_branch}
        )
        
    except Exception as e:
        logger.error(f"Analysis error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


#index root
@app.get("/")
async def root():
    return {
        "service": "Codebase AI Analyst",
        "version": "1.0.0",
        "status": "running",
    }


# Health check endpoint
@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "service": "Codebase AI Analyst",
        "groq_connected": bool(GROQ_API_KEY),
        "github_connected": bool(GITHUB_TOKEN)
    }


# Code analysis endpoint
@app.post("/analyze", response_model=AnalysisResponse, responses={500: {"model": ErrorResponse}})
async def analyze(request: AnalysisRequest):
    try:
        result = analyze_codebase(request.repository, request.type)
        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Request error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# GitHub webhook endpoint
@app.post("/webhook", response_model=WebhookResponse)
async def github_webhook(request: Request, background_tasks: BackgroundTasks):
    try:
        event = request.headers.get('X-GitHub-Event', 'unknown')
        payload = await request.json()
        
        if event == 'push':
            repo_name = payload.get('repository', {}).get('full_name')
            ref = payload.get('ref', '')
            
            if ref in ['refs/heads/main', 'refs/heads/master'] and repo_name:
                background_tasks.add_task(analyze_codebase, repo_name, AnalysisType.GENERAL)
                logger.info(f"Triggered analysis for {repo_name}")
                return WebhookResponse(
                    message="Analysis triggered",
                    event_type=event,
                    repository=repo_name,
                    analysis_triggered=True
                )
        
        return WebhookResponse(
            message="Event received but no analysis triggered",
            event_type=event,
            analysis_triggered=False
        )
        
    except Exception as e:
        logger.error(f"Webhook error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get('PORT', 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)