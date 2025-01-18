import pandas as pd

from src.analyzer.headers_calc import calculate_header_scores, HEADER_COMPONENT_SCORE_COL
from src.analyzer.http import calculate_http_scores, HTTP_COMPONENT_SCORE_COL
from src.analyzer.redirect import calculate_redirect_scores, REDIRECT_COMPONENT_SCORE_COL

WEIGHT_HEADERS = 0.4
WEIGHT_HTTP = 0.4
WEIGHT_REDIRECT = 0.2


def calculate_final_scores(dataframe):
    dataframe["assessment_date"] = pd.to_datetime(dataframe["assessment_datetime"]).dt.date
    dataframe["analysis_datetime"] = pd.Timestamp.now()

    dataframe = calculate_header_scores(dataframe)
    dataframe = calculate_http_scores(dataframe)
    dataframe = calculate_redirect_scores(dataframe)

    dataframe["final_score"] = (
        (dataframe[HEADER_COMPONENT_SCORE_COL] * WEIGHT_HEADERS +
         dataframe[HTTP_COMPONENT_SCORE_COL] * WEIGHT_HTTP +
         dataframe[REDIRECT_COMPONENT_SCORE_COL] * WEIGHT_REDIRECT).round(2)
    )

    dataframe["grade"] = dataframe["final_score"].apply(
        lambda
            score: "A" if score >= 81 else "B" if score >= 61 else "C" if score >= 41 else "D" if score >= 21 else "F"
    )

    return dataframe
