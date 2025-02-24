import os

from src.analyzer.calculator.calc import calculate_final_scores
from src.analyzer.utils.utils import load_results


def score_analyze():
    input_directory = os.path.join('../../..', 'src', 'data', 'results')
    output_directory = os.path.join(input_directory, 'analysis')
    filename_output = 'sh_final_result_with_scores'

    consolidated_data = load_results(input_directory)

    if consolidated_data.empty:
        print("No data to process.")
        return

    final_scores = calculate_final_scores(consolidated_data)
    final_scores.to_csv(os.path.join(output_directory, f'{filename_output}.csv'), index=False)

    already_to_analyze = final_scores.loc[final_scores.groupby("ETER_ID")["final_score"].idxmin()]
    already_to_analyze.to_csv(os.path.join(output_directory, f'{filename_output}_unique_hei.csv'), index=False)
    print("Final scores saved.")


if __name__ == "__main__":
    score_analyze()
