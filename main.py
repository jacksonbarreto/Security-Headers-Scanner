import logging
import os

from src.config import config
from src.scanner.scanner import run_scan
#import daemon
#from setproctitle import setproctitle

log_file = os.path.join('.', 'scan.log')


def main():
    input_directory = os.path.join('.', 'src', 'data', 'source')
    files = [f for f in os.listdir(input_directory) if f.endswith('.csv')]
    logging.info(f"Found {len(files)} files to scan.")

    if not files:
        logging.error(f"No CSV files found in '{input_directory}'. Please ensure the files are in the correct directory.")
        return
    if not config['user_agents']:
        logging.error("No user agents defined in config file (config.py).")
        return
    if not config['expected_headers']:
        logging.error("No expected headers defined in config file (config.py).")
        return

    daily_assessments = config.get("daily_assessments", 5)

    for i in range(daily_assessments):
        for file in files:
            file_path = os.path.join(input_directory, file)
            logging.info(f"({i + 1}/{daily_assessments}) - Scanning file: {file}")
            try:
                run_scan(file_path)
            except Exception as e:
                logging.error(f"Error scanning {file}: {e}")


def start_daemon():
    #setproctitle("security_header_scanner")
    logging.basicConfig(
        filename=log_file,
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    try:
        main()
        logging.info("Scan complete.")
    except Exception as e:
        logging.error(f"Unexpected error: {e}")


if __name__ == "__main__":
    #with open(log_file, 'a') as log_stream:
       # with daemon.DaemonContext(stdout=log_stream, stderr=log_stream, umask=0o002, working_directory='.',
                         #         detach_process=True):
          #  start_daemon()
    main()