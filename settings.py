from pathlib import Path

REPO_DIR = Path(__file__).parent
CDM_DATASET_DIR = REPO_DIR / "cdm-dataset"
LOGS_DIR = REPO_DIR / "logs"
LOGS_SOTA_DIR = LOGS_DIR / "SOTA"

MODELS = [
    "TheBloke_Llama-2-70B-Chat-GPTQ",
    # "ollama-gemma2:27b-instruct-q4_0",
    # "ollama-llama2:70b-chat-q4_0",
    # "ollama-llama3:70b-chat-q4_0",
    # "ollama-llama3.1:70b-instruct-q4_0",
]

PATHOLOGIES = [
    "appendicitis",
    "cholecystitis",
    "diverticulitis",
    "pancreatitis",
]

FIELDS = [
    "Diagnosis",
    "Gracious Diagnosis",
    # "Physical Examination",
    # "Late Physical Examination",
    # "Action Parsing",
    # "Treatment Parsing",
    # "Diagnosis Parsing",
    # "Rounds",
    # "Invalid Tools",
    # "Unnecessary Laboratory Tests",
    # "Unnecessary Imaging",
]
