import os
import pandas as pd
from datetime import datetime


def sanitize_url(url):
    return url.replace("http://", "").replace("https://", "").strip("/")

def save(dataframe, country_code, platform, error=False):
    folder = 'errors' if error else 'results'
    output_dir = os.path.join('.', 'src', 'data', folder)

    os.makedirs(output_dir, exist_ok=True)

    now = datetime.now().strftime("%Y-%m-%d")
    filename = f"{country_code}_{platform}_{'errors_' if error else ''}{now}.csv"
    output_file = os.path.join(output_dir, filename)

    if isinstance(dataframe, list):
        df = pd.DataFrame(dataframe)
    else:
        df = dataframe

    if not df.empty:
        df.to_csv(output_file, index=False)