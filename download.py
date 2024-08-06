import os
from datetime import datetime
import shutil

from settings import LOGS_DIR, LOGS_SOTA_DIR, MODELS, PATHOLOGIES


def download_most_recent(
    base_folder,
    pathology,
    agent,
    model,
    addendum,
    destination_folder,
    folder_position=0,
):
    listdir = os.listdir
    copy = shutil.copy

    all_folder_files = listdir(base_folder)

    base_folder = base_folder.rstrip("/")

    folder_date_mapping = {}
    if not addendum:
        addendum = tuple(str(i) for i in range(10))
    for item in all_folder_files:
        if item.startswith(f"{pathology}_{agent}_{model}_") and item.endswith(addendum):
            print(item)
            n_underscore = addendum.count("_")
            if n_underscore == 0:
                date_time_str = "_".join(item.split("_")[-2:])
            else:
                date_time_str = "_".join(item.split("_")[-(2 + n_underscore) : -n_underscore])
            date_time_obj = datetime.strptime(date_time_str, "%d-%m-%Y_%H:%M:%S")
            folder_date_mapping[item] = date_time_obj

    latest_folder = sorted(folder_date_mapping, key=folder_date_mapping.get, reverse=True)[folder_position]

    files = listdir(os.path.join(base_folder, latest_folder))
    for file in files:
        if "_results" in file:
            remote_file_path = os.path.join(base_folder, latest_folder, file)
            local_file_path = os.path.join(destination_folder, file)
            copy(remote_file_path, local_file_path)
            print(local_file_path)


def download_most_recent_FI(
    base_folder,
    pathology,
    model,
    addendum,
    destination_folder,
    folder_position=0,
):
    listdir = os.listdir
    copy = shutil.copy

    base_folder = base_folder.rstrip("/")

    all_folder_files = listdir(base_folder)
    folder_date_mapping = {}
    for item in all_folder_files:
        if item.startswith(f"{pathology}_{model}_") and item.endswith(f"_FULL_INFO{addendum}"):
            n_underscore = addendum.count("_")
            date_time_str = "_".join(item.split("_")[-(4 + n_underscore) : -(2 + n_underscore)])
            date_time_obj = datetime.strptime(date_time_str, "%d-%m-%Y_%H:%M:%S")
            folder_date_mapping[item] = date_time_obj

    latest_folder = sorted(folder_date_mapping, key=folder_date_mapping.get, reverse=True)[folder_position]

    files = listdir(os.path.join(base_folder, latest_folder))
    for file in files:
        if "_results" in file or ".log" in file:
            remote_file_path = os.path.join(base_folder, latest_folder, file)
            local_file_path = os.path.join(destination_folder, file)
            copy(remote_file_path, local_file_path)
            print(local_file_path)


full_info = True  # Change between True and False depending on if you are download CDM-FI or normal CDM runs
base_folder = str(LOGS_DIR)  # Base folder of where the runs are saved
destination_folder = str(
    LOGS_SOTA_DIR / ("FI_PLI" if full_info else "CDM_VANILLA")
)  # Base folder where you want to download the runs

agent = "ZeroShot"

folder_position = 0  # This specifies only the most recent run should be downloaded

addendum = "_PLI_N" if full_info else ""

for model in MODELS:
    for pathology in PATHOLOGIES:
        if full_info:
            download_most_recent_FI(
                base_folder,
                pathology,
                model,
                addendum,
                destination_folder,
                folder_position,
            )
        else:
            download_most_recent(
                base_folder,
                pathology,
                agent,
                model,
                addendum,
                destination_folder,
                folder_position,
            )
