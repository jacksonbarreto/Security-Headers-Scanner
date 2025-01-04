import json

from selenium import webdriver
from selenium.webdriver.chrome.options import Options

from src.config import config
from src.scanner.scan_result import ScanResult


def get_webdriver(user_agent, language):
    arguments = ["--headless", f"user-agent={user_agent}", f"accept-language={language}", f"--lang={language}",
                 "--no-sandbox", "--disable-dev-shm-usage", "--disable-blink-features=AutomationControlled",
                 "--dns-server=1.1.1.1", "--ignore-certificate-errors", "--ignore-certificate-errors-spki-list",
                 "--ignore-ssl-errors=yes"]
    options = Options()
    for arg in arguments:
        options.add_argument(arg)

    options.set_capability("goog:loggingPrefs", {"performance": "ALL"})
    driver = webdriver.Chrome(options=options)
    driver.set_page_load_timeout(config['timeout'])
    driver.execute_cdp_cmd("Network.setCacheDisabled", {"cacheDisabled": True})
    driver.execute_cdp_cmd("Network.enable", {})
    driver.execute_cdp_cmd("Network.setExtraHTTPHeaders", {
        "headers": {
            "Accept-Language": language
        }
    })
    return driver


def get_scan_result(web_driver):
    logs = web_driver.get_log("performance")
    headers = {}
    protocol = "Unknown"
    initial_status = None
    final_status = None
    redirect_count = 0

    for entry in logs:
        log = entry['message']
        message_data = json.loads(log)['message']
        if 'Network.requestWillBeSent' in message_data['method']:
            redirect_response = message_data['params'].get('redirectResponse', {})
            if redirect_response:
                redirect_status = redirect_response.get('status')
                if 300 <= redirect_status < 400:
                    redirect_count += 1
                    if initial_status is None:
                        initial_status = redirect_status
        if 'Network.responseReceived' in message_data['method']:
            response_data = message_data['params'].get('response', {})
            if response_data:
                headers = response_data.get('headers', {})
                protocol = response_data.get('protocol', "Unknown")
                final_status = response_data.get('status', None)

                if initial_status is None:
                    initial_status = final_status
    final_url = web_driver.current_url
    return ScanResult(
        initial_status=initial_status,
        final_status=final_status,
        redirect_count=redirect_count,
        headers=headers,
        protocol=protocol,
        final_url=final_url
    )
