import os
import json
import pandas as pd


"""
Reads one JSON file and returns it as pandas DataFrame.
"""

def load_json(file_path):
    with open(file_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    df = pd.json_normalize(data)
    return df

"""
Reads all JSON files in folder and merges to one DataFrame
"""
def load_all_jsons(folder_path):
    all_files = [file for file in os.listdir(folder_path) if file.endswith('.json')]
    all_dfs = []

    for file in all_files:
        file_path = os.path.join(folder_path, file)
        df = load_json(file_path)
        all_dfs.append(df)

    merged_df = pd.concat(all_dfs, ignore_index=True)
    return merged_df

if __name__ == "__main__":

    folder = '../data/raw'
    df = load_all_jsons(folder)
    print(df.head())
    print(f"Read {len(df)} road accidents")