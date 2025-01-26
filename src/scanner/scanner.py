import logging
import os
import signal
import sys

import pandas as pd

from src.scanner.browser import get_webdriver, get_scan_result
from src.config import config
from concurrent.futures import ThreadPoolExecutor, as_completed
import threading

from src.scanner.utils.utils import save, sanitize_url, normalize_domain

lock = threading.Lock()

results_by_platform = {list(device.keys())[0]: [] for device in config['user_agents']}
errors = []
HTTP = "http://"
HTTPS = "https://"
active_web_drivers = []


def signal_handler(sig, frame):
    global active_web_drivers
    logging.warning("\nInterruption received. Ending active WebDrivers...")
    for driver in active_web_drivers:
        try:
            driver.quit()
        except Exception as e:
            logging.error(f"Error quitting WebDriver: {e}")
    sys.exit(0)


signal.signal(signal.SIGINT, signal_handler)


def run_scan(input_file):
    global results_by_platform
    global errors
    errors = []
    results_by_platform = {list(device.keys())[0]: [] for device in config['user_agents']}

    filename = os.path.basename(input_file)
    country_code = filename[:2]
    language = next((lang[country_code] for lang in config['languages'] if country_code in lang), 'en')
    max_threads = config.get('max_threads', 5)

    df = pd.read_csv(input_file)
    if "error" in df.columns:
        df = df.drop(columns=["error"])

    url_column_name = next((col for col in df.columns if col.lower() == 'url'), None)
    if url_column_name is None:
        raise ValueError(f"No 'url' column found in CSV ({filename}).")

    with ThreadPoolExecutor(max_workers=max_threads) as executor:
        futures = [executor.submit(row_scan, row, url_column_name, language) for index, row in df.iterrows()]
        for future in as_completed(futures):
            try:
                future.result()  # Catch exceptions
            except Exception as e:
                logging.error(f"Thread error in CSV ({filename}): {e}")

    for platform, results in results_by_platform.items():
        save(results, country_code, platform)
    if errors:
        save(errors, country_code, '', error=True)


def row_scan(row, url_column_name, language):
    global active_web_drivers
    process_result_by_platform = {}
    process_error = []
    base_url = sanitize_url(row[url_column_name])
    http_url = f"{HTTP}{base_url}"
    https_url = f"{HTTPS}{base_url}"

    for device in config['user_agents']:
        platform = list(device.keys())[0]
        user_agent = list(device.values())[0]

        result = {
            "assessment_datetime": None,
            "http_status_code": None,
            "https_status_code": None,
            "redirected_to_https": False,
            "redirected_https_to_same_domain": False,
            "final_url": None,
            "idioma": language,
            "platform": platform,
            "protocol_http": None,
            "redirect_count": None,
        }

        web_driver = get_webdriver(user_agent, language)
        active_web_drivers.append(web_driver)
        try:
            logging.info(f"Scanning HTTP: {base_url} - {platform}")
            web_driver.get(http_url)
            scan_result = get_scan_result(web_driver)
            result["http_status_code"] = scan_result.initial_status
            result["redirected_to_https"] = scan_result.final_url.startswith(HTTPS)
            if result["redirected_to_https"]:
                result["https_status_code"] = scan_result.final_status
                base_domain = normalize_domain(base_url)
                final_domain = normalize_domain(scan_result.final_url)
                result["redirected_https_to_same_domain"] = base_domain == final_domain

            if not result["redirected_to_https"]:
                logging.info(f"Scanning HTTPS: {https_url}")
                web_driver.quit()
                active_web_drivers.remove(web_driver)
                web_driver = get_webdriver(user_agent, language)
                active_web_drivers.append(web_driver)
                web_driver.get(https_url)
                scan_result = get_scan_result(web_driver)
                result["https_status_code"] = scan_result.final_status

            result.update({
                "protocol_http": scan_result.protocol,
                "final_url": scan_result.final_url,
                "redirect_count": scan_result.redirect_count,
                "assessment_datetime": pd.Timestamp.now(),
                **assessing_security_headers(scan_result.headers)
            })
            process_result_by_platform[platform] = {**row.to_dict(), **result}
        except Exception as e:
            logging.error(f"Error scanning {base_url} - {platform}: {e}")
            error_result = {**row.to_dict(), "error": str(e)}
            process_error.append(error_result)
            break
        finally:
            web_driver.quit()
            active_web_drivers.remove(web_driver)

    with lock:
        for platform, result in process_result_by_platform.items():
            results_by_platform[platform].append(result)
        if process_error:
            errors.extend(process_error)


def assessing_security_headers(received_headers):
    analysis = {}
    normalized_received_headers = {k.lower(): v for k, v in received_headers.items()}
    normalized_expected_headers = {k.lower(): v for k, v in config['expected_headers'].items()}

    for expected_header, heuristic in normalized_expected_headers.items():
        received_header = normalized_received_headers.get(expected_header, "Missing")
        analysis[f"{expected_header}_presence"] = received_header != "Missing"

        if received_header != "Missing":
            analysis[f"{expected_header}_config"] = heuristic(received_header)
        else:
            analysis[f"{expected_header}_config"] = "Missing"

    analysis['raw_headers'] = str(received_headers)

    return analysis
