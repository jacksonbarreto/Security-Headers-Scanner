from src.config import COL_REDIRECT_INCONSISTENCY_BETWEEN_PLATFORMS

REDIRECT_TO_SAME_DOMAIN = 100
REDIRECT_TO_OTHER_DOMAIN = 70
PENALTY_BETWEEN_PLATFORMS = 0.1
REDIRECT_SCORE_BY_PLATFORM_COL = "redirect_score_by_platform"
REDIRECT_AVG_SCORE_BTW_PLATFORMS_COL = "redirect_avg_score_btw_platforms"
REDIRECT_COMPONENT_SCORE_COL = "redirect_component_score"


def calculate_redirect_scores(dataframe):
    platform_counts = dataframe["platform"].nunique()
    dataframe[REDIRECT_SCORE_BY_PLATFORM_COL] = 0
    dataframe[REDIRECT_COMPONENT_SCORE_COL] = 0
    dataframe[REDIRECT_AVG_SCORE_BTW_PLATFORMS_COL] = 0

    dataframe[REDIRECT_SCORE_BY_PLATFORM_COL] = (
            (dataframe["redirected_to_https"] & dataframe[
                "redirected_https_to_same_domain"]) * REDIRECT_TO_SAME_DOMAIN +
            (dataframe["redirected_to_https"] & ~dataframe[
                "redirected_https_to_same_domain"]) * REDIRECT_TO_OTHER_DOMAIN
    )

    dataframe[REDIRECT_AVG_SCORE_BTW_PLATFORMS_COL] = (dataframe.groupby(["ETER_ID"])[REDIRECT_SCORE_BY_PLATFORM_COL]
                                                       .transform("mean").round(2))

    check_inconsistencies(dataframe)

    penalty_combined = (
            dataframe[COL_REDIRECT_INCONSISTENCY_BETWEEN_PLATFORMS]
            * PENALTY_BETWEEN_PLATFORMS
            * (platform_counts / 100)
    )
    penalty_combined = penalty_combined.where(penalty_combined > 0, 1)
    dataframe[REDIRECT_COMPONENT_SCORE_COL] = (
            dataframe[REDIRECT_AVG_SCORE_BTW_PLATFORMS_COL]
            * penalty_combined
    ).clip(upper=100).round(2)

    return dataframe


def check_inconsistencies(dataframe):
    group_by = dataframe.groupby(["ETER_ID"])[["redirected_to_https", "redirected_https_to_same_domain"]].nunique() > 1

    dataframe[COL_REDIRECT_INCONSISTENCY_BETWEEN_PLATFORMS] = dataframe["ETER_ID"].map(group_by.any(axis=1))
