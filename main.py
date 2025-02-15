import logging
import os
import re

from src.analyzer.report.main import generate_reports
from src.config import config
from src.scanner.scanner import run_scan
from src.scanner.utils.utils import check_error_files, reset_error_files

#import daemon
#from setproctitle import setproctitle

log_file = os.path.join('.', 'scan.log')

error_directory = os.path.join('.', 'src', 'data', 'errors')
max_assessments = 10

def main():
    input_directory = os.path.join('.', 'src', 'data', 'source')
    files = [f for f in os.listdir(input_directory) if re.match(r'^[a-zA-Z]{2}-.*\.csv$', f)]
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

    assessments = 0
    while True:
        for file in files:
            file_path = os.path.join(input_directory, file)
            logging.info(f"(Scanning file: {file}")
            try:
                run_scan(file_path)
            except Exception as e:
                logging.error(f"Error scanning {file}: {e}")

        assessments += 1
        if check_error_files():
            if assessments >= max_assessments:
                logging.warning(f"Max attempts reached ({max_assessments}). Some errors may persist.")
                break
            logging.warning(f"Found {len(files)} error files in '{error_directory}'. Please check the files.")
            reset_error_files()
        else:
            break
    logging.info("Scanning completed successfully. Generating reports...")
    generate_reports()
    logging.info("Reports generated successfully.")



def start_daemon():
    #setproctitle("security_header_scanner")
    logging.basicConfig(
        filename=log_file,
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    try:
        main()
    except Exception as e:
        logging.error(f"Unexpected error: {e}")


if __name__ == "__main__":
    #with open(log_file, 'a') as log_stream:
       # with daemon.DaemonContext(stdout=log_stream, stderr=log_stream, umask=0o002, working_directory='.',
                         #         detach_process=True):
          #  start_daemon()
    main()