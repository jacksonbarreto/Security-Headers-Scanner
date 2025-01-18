REDIRECT_TO_SAME_DOMAIN = 100
REDIRECT_TO_OTHER_DOMAIN = 0.7 * REDIRECT_TO_SAME_DOMAIN
PENALTY_WITHOUT_REDIRECT = 0.3
PENALTY_SAME_PLATFORM = 0.05
PENALTY_BETWEEN_PLATFORMS = 0.1
REDIRECT_SCORE_COL = "daily_redirect_score"
DAILY_SCORE_BY_PLATFORM_COL = "daily_redirect_score_by_platform"
DAILY_SCORE_INTER_PLATFORMS_COL = "daily_redirect_score_inter_platforms"
REDIRECT_COMPONENT_SCORE_COL = "redirect_component_score"


def calculate_redirect_scores(dataframe):
    platform_counts = dataframe["platform"].nunique()
    dataframe[REDIRECT_SCORE_COL] = 0
    dataframe[REDIRECT_COMPONENT_SCORE_COL] = 0

    dataframe[REDIRECT_SCORE_COL] = dataframe.apply(
        lambda row: (
            REDIRECT_TO_SAME_DOMAIN if row["redirected_to_https"] and row["redirected_https_to_same_domain"]
            else REDIRECT_TO_OTHER_DOMAIN if row["redirected_to_https"]
            else PENALTY_WITHOUT_REDIRECT
        ),
        axis=1
    )

    dataframe[DAILY_SCORE_BY_PLATFORM_COL] = dataframe.groupby(
        ["ETER_ID", "assessment_date", "platform"]
    )[REDIRECT_SCORE_COL].transform("median")

    dataframe[DAILY_SCORE_INTER_PLATFORMS_COL] = dataframe.groupby(
        ["ETER_ID", "assessment_date"]
    )[DAILY_SCORE_BY_PLATFORM_COL].transform("mean")

    check_inconsistencies(dataframe)

    dataframe[REDIRECT_COMPONENT_SCORE_COL] = (
            dataframe.groupby("ETER_ID")[DAILY_SCORE_INTER_PLATFORMS_COL].transform("mean") *
            (1 - (dataframe["redirect_inconsistency_same_platform"] * PENALTY_SAME_PLATFORM +
                  dataframe["redirect_inconsistency_between_platforms"] * PENALTY_BETWEEN_PLATFORMS * (
                          platform_counts / 100)))
    )

    return dataframe


def check_inconsistencies(dataframe):
    dataframe["redirect_inconsistency_same_platform"] = False
    dataframe["redirect_inconsistency_between_platforms"] = False

    dataframe["redirect_inconsistency_same_platform"] = dataframe.groupby(
        ["ETER_ID", "platform"]
    )["redirected_to_https"].transform(lambda x: x.nunique() > 1)

    dataframe["redirect_inconsistency_between_platforms"] = dataframe.groupby(
        ["ETER_ID", "assessment_date"]
    )["redirected_to_https"].transform(lambda x: x.nunique() > 1)

    return dataframe
