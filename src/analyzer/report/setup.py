import os

RESULT_FILENAME = 'sh_final_result_with_scores_unique_hei.csv'
ROOT_DIRECTORY = os.path.join('..', '..', '..')
RESULT_FILE_PATH = os.path.join(ROOT_DIRECTORY, 'src', 'data', 'results', 'analysis', RESULT_FILENAME)
OUTPUT_ANALYSIS_BASE_DIRECTORY = os.path.join(ROOT_DIRECTORY, 'src', 'data', 'results', 'analysis')
TABLE_DIRECTORY = os.path.join(OUTPUT_ANALYSIS_BASE_DIRECTORY, 'tables')
CHART_DIRECTORY = os.path.join(OUTPUT_ANALYSIS_BASE_DIRECTORY, 'charts')
os.makedirs(TABLE_DIRECTORY, exist_ok=True)
os.makedirs(CHART_DIRECTORY, exist_ok=True)