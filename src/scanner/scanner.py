import os
import pandas as pd
from src.scanner.browser import start_webdriver, get_scan_result
from src.config import config
from concurrent.futures import ThreadPoolExecutor, as_completed
import threading

from src.scanner.utils.utils import save, sanitize_url

lock = threading.Lock()
results_by_platform = {list(device.keys())[0]: [] for device in config['user_agents']}
errors = []
HTTP = "http://"
HTTPS = "https://"

def run_scan(input_file):
    global results_by_platform
    global errors
    errors = []

    filename = os.path.basename(input_file)
    country_code = filename[:2]
    language = next((lang[country_code] for lang in config['languages'] if country_code in lang), 'en')
    max_threads = config.get('max_threads', 5)

    df = pd.read_csv(input_file)

    url_column = next((col for col in df.columns if col.lower() == 'url'), None)
    if url_column is None:
        raise ValueError(f"No 'url' column found in CSV ({filename}).")

    with ThreadPoolExecutor(max_workers=max_threads) as executor:
        futures = [executor.submit(process_scan, row, url_column, language) for index, row in df.iterrows()]
        for future in as_completed(futures):
            try:
                future.result()  # Catch exceptions
            except Exception as e:
                print(f"Thread error in CSV ({filename}): {e}")

    for platform, results in results_by_platform.items():
        save(results, country_code, platform)
    if errors:
        save(errors, country_code, 'combined', error=True)

def process_scan(row, url_column, language):
    process_result_by_platform = {}
    process_error = []
    base_url = sanitize_url(row[url_column])
    http_url = f"{HTTP}{base_url}"
    https_url = f"{HTTPS}{base_url}"

    for device in config['user_agents']:
        platform = list(device.keys())[0]
        user_agent = list(device.values())[0]

        driver = start_webdriver(user_agent, language)
        result = {
            "assessment_date": None,
            "headers_analyzed": False,
            "http_status_code": None,
            "https_status_code": None,
            "redirected_to_https": None,
            "idioma": language,
            "platform": platform,
            "protocol_http": None,
            "redirect_count": None,
        }
        try:
            # test HTTP
            print(f"Scanning HTTP: {base_url} - {platform}")
            driver.get(http_url)
            scan_result = get_scan_result(driver)

            result["http_status_code"] = scan_result.initial_status
            result["redirect_count"] = scan_result.redirect_count
            result["redirected_to_https"] = scan_result.final_url.startswith(HTTPS)
            if result["redirected_to_https"]:
                result.update({
                    "headers_analyzed": True,
                    "protocol_http": scan_result.protocol,
                    "https_status_code": scan_result.final_status,
                    **assessing_security_headers(scan_result.headers)
                })

            # 2. Test HTTPS directly, if didn't have redirect
            if not result["redirected_to_https"]:
                print(f"Scanning HTTPS: {https_url}")
                driver.get(https_url)
                scan_result = get_scan_result(driver)
                result["redirect_count"] = scan_result.redirect_count
                result["https_status_code"] = scan_result.final_status
                if result["https_status_code"] == 200:
                    result.update({
                        "headers_analyzed": True,
                        "protocol_http": scan_result.protocol,
                        **assessing_security_headers(scan_result.headers)
                    })
            result["assessment_date"] = pd.Timestamp.now()
            process_result_by_platform[platform] = {**row.to_dict(), **result}
        except Exception as e:
            print(f"Error scanning {base_url} - {platform}: {e}")
            error_result = {**row.to_dict(), "platform": platform, "error": str(e)}
            process_error.append(error_result)
        finally:
            driver.quit()

    with lock:
        for platform, result in process_result_by_platform.items():
            results_by_platform[platform].append(result)
        if process_error:
            errors.extend(process_error)

def assessing_security_headers(headers):
    analysis = {}
    normalized_headers = {k.lower(): v for k, v in headers.items()}
    expected_headers = {k.lower(): v for k, v in config['expected_headers'].items()}

    for expected_header, heuristic in expected_headers.items():
        received_header = normalized_headers.get(expected_header, "Missing")
        analysis[f"{expected_header}_presence"] = received_header != "Missing"

        if received_header != "Missing":
            analysis[f"{expected_header}_config"] = heuristic(received_header)
        else:
            analysis[f"{expected_header}_config"] = "Missing"

    analysis['raw_headers'] = str(headers)

    return analysis







