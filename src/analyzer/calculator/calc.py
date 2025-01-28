import pandas as pd

from src.analyzer.calculator.headers_calc import calculate_header_scores, HEADER_COMPONENT_SCORE_COL
from src.analyzer.calculator.redirect import calculate_redirect_scores, REDIRECT_COMPONENT_SCORE_COL

WEIGHT_HEADERS = 0.6
WEIGHT_REDIRECT = 0.4


def calculate_final_scores(dataframe):
    dataframe["analysis_datetime"] = pd.Timestamp.now()

    dataframe = calculate_header_scores(dataframe)
    dataframe = calculate_redirect_scores(dataframe)

    dataframe["final_score"] = (
        (dataframe[HEADER_COMPONENT_SCORE_COL] * WEIGHT_HEADERS +
         dataframe[REDIRECT_COMPONENT_SCORE_COL] * WEIGHT_REDIRECT).round(2)
    )

    bins = [0, 20, 35, 50, 65, 80, 100]
    labels = ["F", "E", "D", "C", "B", "A"]
    dataframe["grade"] = pd.cut(dataframe["final_score"], bins=bins, labels=labels, right=False)

    return dataframe
