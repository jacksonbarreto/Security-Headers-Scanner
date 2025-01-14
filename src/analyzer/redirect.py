import pandas as pd

from src.config import config

UB = config.get("basic_point_unit", 10)
REDIRECT_TO_SAME_DOMAIN = 1.5 * UB
REDIRECT_TO_OTHER_DOMAIN = UB
WITHOUT_REDIRECT = -3 * UB
PENALTY_SAME_PLATFORM = -1 * UB
PENALTY_BETWEEN_PLATFORMS = -2 * UB


def calculate_redirect_scores(dataframe):
    platform_counts = dataframe["platform"].nunique()
    dataframe["redirect_score"] = 0
    dataframe["total_redirect_score"] = 0

    dataframe["redirect_score"] += dataframe.apply(
        lambda row: (
            REDIRECT_TO_SAME_DOMAIN if row["redirected_to_https"] and row["redirected_https_to_same_domain"]
            else REDIRECT_TO_OTHER_DOMAIN if row["redirected_to_https"]
            else WITHOUT_REDIRECT
        ),
    axis=1
    )

    dataframe = calculate_redirect_inconsistencies(dataframe)

    # Calcula a mediana diária para cada plataforma
    median_rows = (
        dataframe.groupby(["ETER_ID", "assessment_date", "platform"])["redirect_score"]
        .apply(lambda x: x.idxmax() if len(x) == 1 else x.sort_values().iloc[len(x) // 2:].index[0])  # Mediana
        .reset_index(name="median_index")
    )

    # Soma as medianas de todos os dias
    daily_medians = dataframe.loc[median_rows["median_index"]].groupby(["ETER_ID", "assessment_date"])[
        "redirect_score"].mean()

    # Calcula a média das medianas diárias para cada ETER_ID
    average_median_score = daily_medians.groupby("ETER_ID").mean()

    # Calcula as penalidades por ETER_ID
    penalties = dataframe.groupby("ETER_ID").apply(
        lambda group: {
            "same_platform_penalty": (
                PENALTY_SAME_PLATFORM
                if group["redirect_inconsistency_same_platform"].any() or group[
                    "redirect_same_domain_inconsistency_same_platform"].any()
                else 0
            ),
            "between_platforms_penalty": (
                PENALTY_BETWEEN_PLATFORMS
                if group["redirect_inconsistency_between_platforms"].any() or group[
                    "redirect_same_domain_inconsistency_between_platforms"].any()
                else 0
            )
        }
    )

    # Combina a média das medianas com as penalidades
    dataframe["total_redirect_score"] = dataframe["ETER_ID"].map(
        lambda eter_id: average_median_score[eter_id]
                        + penalties[eter_id]["same_platform_penalty"]
                        + penalties[eter_id]["between_platforms_penalty"] * platform_counts
    )

    return dataframe


def calculate_redirect_inconsistencies(dataframe):
    # Calcula inconsistências
    redirect_inconsistency_same_platform = (
        dataframe.groupby(["ETER_ID", "assessment_date", "platform"])["redirected_to_https"]
        .transform(lambda x: x.nunique() > 1)
    )

    redirect_inconsistency_between_platforms = (
        dataframe.groupby(["ETER_ID", "assessment_date"])["redirected_to_https"]
        .transform(lambda x: x.nunique() > 1)
    )

    redirect_same_domain_inconsistency_same_platform = (
        dataframe.groupby(["ETER_ID", "assessment_date", "platform"])["redirected_https_to_same_domain"]
        .transform(lambda x: x.nunique() > 1)
    )

    redirect_same_domain_inconsistency_between_platforms = (
        dataframe.groupby(["ETER_ID", "assessment_date"])["redirected_https_to_same_domain"]
        .transform(lambda x: x.nunique() > 1)
    )

    # Concatena as novas colunas ao DataFrame de uma vez
    new_columns = pd.DataFrame({
        "redirect_inconsistency_same_platform": redirect_inconsistency_same_platform,
        "redirect_inconsistency_between_platforms": redirect_inconsistency_between_platforms,
        "redirect_same_domain_inconsistency_same_platform": redirect_same_domain_inconsistency_same_platform,
        "redirect_same_domain_inconsistency_between_platforms": redirect_same_domain_inconsistency_between_platforms,
    })

    dataframe = pd.concat([dataframe, new_columns], axis=1)
    return dataframe
