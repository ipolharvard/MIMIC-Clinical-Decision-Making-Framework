# MIMIC Clinical Decision Making Framework

This repository contains the code for running the clinical decision making task using the MIMIC CDM dataset.

The code to create the dataset is found at: https://github.com/paulhager/MIMIC-Clinical-Decision-Making-Dataset

The dataset is based on the MIMIC-IV database. Access can be requested here: https://physionet.org/content/mimiciv/2.2/

A pre-processed version of the dataset is currently under review by Physionet.

## MIMIC CDM

This code simulates a realistic clinical environment where an LLM is provided with the history of present illness of a patient and then tasked to gather information to come to a final diagnosis and treatment plan.

To run the clinical decision making task, use the **run.py** file. The arguments for this file are specified through config files managed by the hydra library. The most important arguments are:
- pathology: Specify one of appendicitis, cholecystitis, diverticulitis, pancreatitis
- model: Specify which model to use. The model file also contains the different role tags
- summarize: Automatically summarize the progress if we begin to reach the token limit

These additional arguments change the way information is presented but did not help performance in my experience and so were not included in the paper:
- include_ref_range: Include the reference ranges for lab results, as provided in the MIMIC database
- bin_lab_results: Replace exact lab result values with the word "low", "normal", or "high", using the reference ranges
- provide_diagnostic_criteria: Adds an extra tool where the model can consult diagnostic criteria if desired
- diag_crit_writer_openai_api_key: OpenAI key to ask for new diagnostic criteria if they are missing from the datafile
- include_tool_use_examples: Provides examples of how to use the tools

## MIMIC CDM Full Information

For the MIMIC-CDM-Full Information task, executed through **run_full_info.py**, all relevant information required for a diagnosis is provided upfront to the model and only a diagnosis is asked for. This allows us to also control what information we provide the model and explore many aspects of model performance such as robustness. The relevant arguments for this task are those from above and additionally:
- prompt_template: Determines the system instruction or prompt used to ask for an answer. Possible values are specified in run_full_info.py
- order: The order in which information is provided
- abbreviated: Provide the original, abbreviated text
- fewshot: Provides hand-crafted fewshot cases and diagnosis examples
- save_probabilities: Saves the probabilities of the generation for downstream analysis
- only_abnormal_labs: Provide only those lab results that are abnormal.
- bin_lab_results_abnormal: If only abnormal labs are provided, also bin them

## Other

Housekeeping arguments are:
- seed: The seed used for greedy decoding
- local_logging: If logs should be saved locally
- run_descr: An extra name to give to the run
- first_patient: Start executing at a specific patient
- patient_list_path: Run on only a select group of patients (given as a list of hadm_ids)

To run the code, start with a fresh python 3.10 installation using the package manager of your choice and then run 

```
pip3 install torch torchvision torchaudio
pip install transformers spacy auto-gptq langsmith langchain[llms] optimum thefuzz scispacy loguru hydra-core --upgrade negspacy openai nltk exllamav2 tiktoken paramiko seaborn https://s3-us-west-2.amazonaws.com/ai2-s2-scispacy/releases/v0.5.1/en_core_sci_lg-0.5.1.tar.gz
```
  