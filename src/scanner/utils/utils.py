import os
import pandas as pd
from urllib.parse import urlparse

def sanitize_url(url):
    return url.replace("http://", "").replace("https://", "").split("/")[0].split(':')[0]

def normalize_domain(url):
    parsed_url = urlparse(url)
    domain = parsed_url.netloc or parsed_url.path
    if domain.startswith("www."):
        domain = domain[4:]
    return domain.split(':')[0]

def save(dataframe, country_code, platform, error=False):
    folder = 'errors' if error else 'results'
    output_dir = os.path.join('.', 'src', 'data', folder)

    os.makedirs(output_dir, exist_ok=True)

    filename = f"{country_code}_{platform}{'_errors_' if error else ''}.csv"
    output_file = os.path.join(output_dir, filename)

    if isinstance(dataframe, list):
        df = pd.DataFrame(dataframe)
    else:
        df = dataframe

    if not df.empty:
        if os.path.exists(output_file):
            df.to_csv(output_file, mode='a', header=False, index=False)
        else:
            df.to_csv(output_file, index=False)
