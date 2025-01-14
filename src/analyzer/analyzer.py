import os

from src.analyzer.calc import calculate_final_scores
from src.analyzer.utils import load_results


def main():
    input_directory = os.path.join('../..', 'src', 'data', 'results')
    consolidated_data = load_results(input_directory)

    if consolidated_data.empty:
        print("No data to process.")
        return

    #consolidated_data.to_csv(os.path.join(input_directory, 'consolidated_results.csv'), index=False)
    #print("Consolidated results saved. Ready for scoring.")

    final_scores = calculate_final_scores(consolidated_data)
    final_scores.to_csv(os.path.join(input_directory, 'final_scores.csv'), index=False)
    print("Final scores saved.")


if __name__ == "__main__":
    main()
