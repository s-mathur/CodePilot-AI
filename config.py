import os

BASE_DIR = os.getcwd()

PROJECT_DIR = os.path.join(BASE_DIR, "user_uploads")

SESSION_TTL = 60 * 30

# Gemini
GEMINI_MODEL = "gemini-2.5-flash"

# Gemini Settings
TEMPERATURE = 0.2
MAX_CONTEXT_LENGTH = 6000

# Embedding Model
EMBEDDING_MODEL = "all-MiniLM-L6-v2"

SUPPORTED_EXTENSIONS = [".py"]

IGNORE_FOLDERS = [
    "__pycache__",
    ".git",
    ".idea",
    "venv",
    "env",
    ".venv",
    "build",
    "dist",
    ".streamlit",
    "node_modules",
    ".vscode"
]

TASKS = [
    "architecture",
    "code_review",
    "debug",
    "similar_search",
    "refactor",
    "code_generate",
    "project_analysis",
    "general"
]

DEBUG_KEYWORDS = [
    "traceback",
    "error",
    "exception",
    "attributeerror",
    "typeerror",
    "valueerror",
    "keyerror",
    "indexerror",
    "modulenotfounderror",
    "importerror",
    "syntaxerror",
    "runtimeerror",
    "zerodivisionerror",
    "filenotfounderror",
    "not working",
    "fails",
    "failure"
]

ARCHITECTURE_KEYWORDS = [
    "architecture",
    "project architecture",
    "system architecture",
    "system design",
    "data flow",
    "component interaction",
    "module interaction",
    "component relationship",
    "module relationship",
    "execution flow",
    "application flow",
    "request flow",
    "workflow",
    "how modules interact",
    "how components interact",
    "how the project is structured",
    "how the system is structured",
    "explain the architecture",
    "explain project architecture"
]
PROJECT_ANALYSIS_KEYWORDS = [
    "analyze the project",
    "project analysis",
    "analyze codebase",
    "codebase analysis",
    "project overview",
    "codebase overview",
    "project summary",
    "codebase summary",
    "summarize the project",
    "summarize codebase",
    "analyze source code",
    "analyze the codebase",
    "project details",
    "codebase details",
    "what is in the project",
    "what does the project contain",
    "list project components",
    "list project files",
    "analyze project"
]
REVIEW_KEYWORDS = [
    "code review",
    "review code",
    "review this",
    "review project",
    "best practices",
    "security issues",
    "code quality",
    "quality",
    "issues in code"
]

SIMILAR_SEARCH_KEYWORDS = [
    "where",
    "find",
    "search",
    "locate",
    "show me",
    "which file",
    "which function",
    "where is"
]

REFACTOR_KEYWORDS = [
    "refactor",
    "improve",
    "optimize",
    "clean",
    "cleanup",
    "improvement",
    "suggest improvements",
    "make it better",
    "rewrite",
    "simplify"
]

GENERATE_KEYWORDS = [
    "generate",
    "write",
    "create",
    "implement",
    "add",
    "build",
    "develop"
]

keyword_rules = [
    (DEBUG_KEYWORDS, "debug", 3),
    (PROJECT_ANALYSIS_KEYWORDS, "project_analysis", 3),
    (ARCHITECTURE_KEYWORDS, "architecture", 4),
    (REVIEW_KEYWORDS, "code_review", 4),
    (SIMILAR_SEARCH_KEYWORDS, "similar_search", 2),
    (REFACTOR_KEYWORDS, "refactor", 3),
    (GENERATE_KEYWORDS, "code_generate", 2),
]