import re

import pandas as pd
import os


def extract_country_and_platform(filename):
    parts = filename.replace('.csv', '').split('_')
    if len(parts) < 2:
        raise ValueError(f"Invalid filename format: {filename}. Expected format: 'country_platform.csv'")
    return parts[0], parts[1]


def load_results(input_directory):
    files = [f for f in os.listdir(input_directory) if re.match(r'^[a-zA-Z]{2}_.*\.csv$', f)]
    print(f"Found {len(files)} result files to analyze.")

    if not files:
        print(f"No CSV files found in '{input_directory}'. Please ensure the files are in the correct directory.")
        return []

    data_frames = []
    for file in files:
        file_path = os.path.join(input_directory, file)
        try:
            country, platform = extract_country_and_platform(os.path.basename(file))
            print(f"Loading file: {file} (Country: {country}, Platform: {platform})")

            df = pd.read_csv(file_path)
            df['country'] = country
            df['platform'] = platform
            data_frames.append(df)
        except Exception as e:
            print(f"Error loading {file}: {e}")

    return pd.concat(data_frames, ignore_index=True) if data_frames else pd.DataFrame()
