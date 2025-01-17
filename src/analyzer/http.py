import pandas as pd

from src.config import config, BASIC_POINT_UNIT

UB = config.get(BASIC_POINT_UNIT, 10)
HTTPS_PRESENCE = 2 * UB
HTTPS_NOT_DETECTED = -5 * UB
HTTP_V2 = UB
HTTP_V3 = 1.5 * UB
PENALTY_SAME_PLATFORM = -1 * UB
PENALTY_BETWEEN_PLATFORMS = -2 * UB

def calculate_http_scores(dataframe):
    platform_counts = dataframe["platform"].nunique()
    dataframe["http_score"] = 0
    dataframe["total_http_score"] = 0

    dataframe["http_score"] += dataframe["protocol_http"].apply(
        lambda x: HTTP_V2 if str(x).lower() == "h2" else HTTP_V3 if str(x).lower() == "h3" else 0)
    dataframe["http_score"] += dataframe["final_url"].apply(
        lambda x: HTTPS_PRESENCE if str(x).lower().startswith("https://") else HTTPS_NOT_DETECTED)

    check_https_inconsistencies(dataframe)

    # Calcula a mediana diária para cada plataforma
    median_rows = (
        dataframe.groupby(["ETER_ID", "assessment_date", "platform"])["http_score"]
        .apply(lambda x: x.idxmax() if len(x) == 1 else x.sort_values().iloc[len(x) // 2:].index[0])  # Mediana
        .reset_index(name="median_index")
    )

    # Soma as medianas de todos os dias
    daily_medians = dataframe.loc[median_rows["median_index"]].groupby(["ETER_ID", "assessment_date"])[
        "http_score"].mean()

    # Calcula a média das medianas diárias para cada ETER_ID
    average_median_score = daily_medians.groupby("ETER_ID").mean()

    # Calcula as penalidades por ETER_ID
    penalties = dataframe.groupby("ETER_ID").apply(
        lambda group: {
            "same_platform_penalty": (
                PENALTY_SAME_PLATFORM if group["http_inconsistency_same_platform"].any() else 0
            ),
            "between_platforms_penalty": (
                PENALTY_BETWEEN_PLATFORMS if group["http_inconsistency_between_platforms"].any() else 0
            )
        }
    )
    # Combina a média das medianas com as penalidades
    dataframe["total_http_score"] = dataframe["ETER_ID"].map(
        lambda eter_id: average_median_score[eter_id]
                        + penalties[eter_id]["same_platform_penalty"]
                        + penalties[eter_id]["between_platforms_penalty"] * platform_counts
    )

    return dataframe


def check_https_inconsistencies(dataframe):
    dataframe["http_inconsistency_same_platform"] = False
    dataframe["http_inconsistency_between_platforms"] = False

    https_inconsistencies_same_platform = dataframe.groupby(
        ["ETER_ID", "assessment_date", "platform"]
    )["final_url"].transform(
        lambda x: x.str.startswith("https://").nunique() > 1
    )
    dataframe["http_inconsistency_same_platform"] = https_inconsistencies_same_platform

    https_inconsistencies_between_platforms = dataframe.groupby(
        ["ETER_ID", "assessment_date"]
    )["final_url"].transform(
        lambda x: x.str.startswith("https://").nunique() > 1
    )
    dataframe["http_inconsistency_between_platforms"] = https_inconsistencies_between_platforms

    return dataframe
