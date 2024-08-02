from pathlib import Path

REPO_DIR = Path(__file__).parent
CDM_DATASET_DIR = REPO_DIR / "cdm-dataset"
LOGS_DIR = REPO_DIR / "logs"
LOGS_SOTA_DIR = LOGS_DIR / "SOTA"
LOGS_SOTA_CDM_VANILLA_DIR = LOGS_DIR / "SOTA" / "CDM_VANILLA"

MODELS = [
    # "ollama-gemma2:27b-instruct-q4_0",
    "TheBloke_Llama-2-70B-Chat-GPTQ",
]

PATHOLOGIES = [
    "appendicitis",
    "cholecystitis",
    "diverticulitis",
    "pancreatitis",
]

EXPERIMENTS = [
    "CDM_VANILLA",
    # "CDM_NOSUMMARY",
]
