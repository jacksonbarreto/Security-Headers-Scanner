from src.config import config, EXPECTED_HEADERS, DEPRECATED_HEADERS, HEADERS_MULTIPLIERS, CRITICAL_HEADERS

total_valid_headers = len(config[EXPECTED_HEADERS]) - len(config[DEPRECATED_HEADERS])
HEADER_PRESENCE = 100 / total_valid_headers
STRONG_CONFIGURATION = 1.4
WEAK_CONFIGURATION = 0.15
PENALTY_DEPRECATED_HEADER = 0.4
PENALTY_SAME_PLATFORM_CRITICAL = 0.1
PENALTY_SAME_PLATFORM_NON_CRITICAL = 0.05
PENALTY_BETWEEN_PLATFORMS_CRITICAL = 0.15
PENALTY_BETWEEN_PLATFORMS_NON_CRITICAL = 0.10
HEADER_SCORE_COL = "daily_header_score"
DAILY_SCORE_BY_PLATFORM_COL = "daily_header_score_by_platform"
DAILY_SCORE_INTER_PLATFORMS_COL = "daily_header_score_inter_platforms"
HEADER_COMPONENT_SCORE_COL = "header_component_score"


def calculate_header_scores(dataframe):
    expected_headers = list({k.lower(): v for k, v in config[EXPECTED_HEADERS].items()}.keys())
    platform_counts = dataframe["platform"].nunique()
    dataframe[HEADER_SCORE_COL] = 0
    dataframe[DAILY_SCORE_BY_PLATFORM_COL] = 0
    dataframe[DAILY_SCORE_INTER_PLATFORMS_COL] = 0
    dataframe[HEADER_COMPONENT_SCORE_COL] = 0

    dataframe[HEADER_SCORE_COL] = dataframe.apply(
        lambda x: sum(calculate_header_presence_and_config(header, x) for header in expected_headers),
        axis=1
    ).round(2)

    dataframe[DAILY_SCORE_BY_PLATFORM_COL] = dataframe.groupby(
        ["ETER_ID", "assessment_date", "platform"]
    )[HEADER_SCORE_COL].transform("median").round(2)

    dataframe[DAILY_SCORE_INTER_PLATFORMS_COL] = dataframe.groupby(
        ["ETER_ID", "assessment_date"]
    )[DAILY_SCORE_BY_PLATFORM_COL].transform("mean").round(2)

    check_inconsistencies(dataframe)

    penalty_same_platform = (
            dataframe["critical_inconsistency_same_platform"] * PENALTY_SAME_PLATFORM_CRITICAL +
            dataframe["header_inconsistency_same_platform"] * PENALTY_SAME_PLATFORM_NON_CRITICAL
    )

    penalty_between_platforms = (
            dataframe[
                "critical_inconsistency_between_platforms"] * PENALTY_BETWEEN_PLATFORMS_CRITICAL * (
                    platform_counts / 100) +
            dataframe[
                "header_inconsistency_between_platforms"] * PENALTY_BETWEEN_PLATFORMS_NON_CRITICAL * (
                    platform_counts / 100)
    )

    dataframe[HEADER_COMPONENT_SCORE_COL] = (
        round(dataframe.groupby("ETER_ID")[DAILY_SCORE_INTER_PLATFORMS_COL].transform("mean") *
              (1 - (penalty_same_platform + penalty_between_platforms)), 2)
    )

    return dataframe


def calculate_header_presence_and_config(header, row):
    deprecated_headers = [h.lower() for h in config[DEPRECATED_HEADERS]]
    multipliers = {k.lower(): v for k, v in config[HEADERS_MULTIPLIERS].items()}
    presence_col = f"{header}_presence"
    config_col = f"{header}_config"
    header_score = 0

    if row.get(presence_col, False):
        header_score += HEADER_PRESENCE

        if header in deprecated_headers:
            header_score *= PENALTY_DEPRECATED_HEADER

        config_value = row.get(config_col, "Missing")
        if config_value.lower() == "strong":
            header_score *= STRONG_CONFIGURATION
        elif config_value.lower() == "weak":
            header_score *= WEAK_CONFIGURATION

        header_score *= multipliers.get(header, 1)

    return round(min(header_score, 100), 2)


def check_inconsistencies(dataframe):
    dataframe["critical_inconsistency_same_platform"] = False
    dataframe["critical_inconsistency_between_platforms"] = False
    dataframe["header_inconsistency_between_platforms"] = False
    dataframe["header_inconsistency_same_platform"] = False

    expected_headers = list({k.lower(): v for k, v in config[EXPECTED_HEADERS].items()}.keys())
    critical_headers = [header.lower() for header in config[CRITICAL_HEADERS]]

    same_platform_inconsistencies = dataframe.groupby(["ETER_ID", "platform"])[
                                        [f"{header}_presence" for header in expected_headers] +
                                        [f"{header}_config" for header in expected_headers]
                                        ].nunique() > 1

    dataframe["header_inconsistency_same_platform"] = dataframe.apply(
        lambda x: same_platform_inconsistencies.loc[
            (x["ETER_ID"], x["platform"])
        ].any(),
        axis=1
    )

    between_platforms_inconsistencies = dataframe.groupby("ETER_ID")[
                                            [f"{header}_presence" for header in expected_headers] +
                                            [f"{header}_config" for header in expected_headers]
                                            ].nunique() > 1

    dataframe["header_inconsistency_between_platforms"] = dataframe.apply(
        lambda x: between_platforms_inconsistencies.loc[
            x["ETER_ID"]
        ].any(),
        axis=1
    )

    same_platform_critical_inconsistencies = dataframe.groupby(["ETER_ID", "platform"])[
                                                 [f"{header}_presence" for header in critical_headers] +
                                                 [f"{header}_config" for header in critical_headers]
                                                 ].nunique() > 1

    dataframe["critical_inconsistency_same_platform"] = dataframe.apply(
        lambda x: same_platform_critical_inconsistencies.loc[
            (x["ETER_ID"], x["platform"])
        ].any(),
        axis=1
    )

    between_platforms_critical_inconsistencies = dataframe.groupby("ETER_ID")[
                                                     [f"{header}_presence" for header in critical_headers] +
                                                     [f"{header}_config" for header in critical_headers]
                                                     ].nunique() > 1

    dataframe["critical_inconsistency_between_platforms"] = dataframe.apply(
        lambda x: between_platforms_critical_inconsistencies.loc[
            x["ETER_ID"]
        ].any(),
        axis=1
    )
