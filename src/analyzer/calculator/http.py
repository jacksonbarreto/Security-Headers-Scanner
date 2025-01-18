HTTP_V2_POINTS = 1.1
HTTP_V3_POINTS = 1.3
HTTPS_PRESENCE = 100 / HTTP_V3_POINTS
PENALTY_SAME_PLATFORM = 0.05
PENALTY_BETWEEN_PLATFORMS = 0.1
HTTP_DAILY_SCORE_COL = "daily_http_score"
DAILY_SCORE_BY_PLATFORM_COL = "daily_http_score_by_platform"
DAILY_SCORE_INTER_PLATFORMS_COL = "daily_http_score_inter_platforms"
HTTP_COMPONENT_SCORE_COL = "http_component_score"


def calculate_http_scores(dataframe):
    platform_counts = dataframe["platform"].nunique()
    dataframe[HTTP_DAILY_SCORE_COL] = 0
    dataframe[HTTP_COMPONENT_SCORE_COL] = 0

    dataframe[HTTP_DAILY_SCORE_COL] = dataframe.apply(calculate_http_presence_and_version, axis=1)

    dataframe[DAILY_SCORE_BY_PLATFORM_COL] = dataframe.groupby(
        ["ETER_ID", "assessment_date", "platform"]
    )[HTTP_DAILY_SCORE_COL].transform("median")

    dataframe[DAILY_SCORE_INTER_PLATFORMS_COL] = dataframe.groupby(
        ["ETER_ID", "assessment_date"]
    )[DAILY_SCORE_BY_PLATFORM_COL].transform("mean").round(2)

    check_inconsistencies(dataframe)

    dataframe[HTTP_COMPONENT_SCORE_COL] = (
        round(dataframe.groupby("ETER_ID")[DAILY_SCORE_INTER_PLATFORMS_COL].transform("mean") *
              (1 - (dataframe["http_inconsistency_same_platform"] * PENALTY_SAME_PLATFORM +
                    dataframe["http_inconsistency_between_platforms"] * PENALTY_BETWEEN_PLATFORMS * (
                            platform_counts / 100))), 2)
    )

    return dataframe


def calculate_http_presence_and_version(row):
    http_score = 0

    if row["final_url"].lower().startswith("https://"):
        http_score += HTTPS_PRESENCE
    elif not row["final_url"].lower().startswith("http://"):
        print(f"final_url is not HTTP or HTTPS ({row['final_url']}) at: {row['ETER_ID']} - {row['Url']}")

    if row["protocol_http"].lower() == "h2":
        http_score *= HTTP_V2_POINTS
    elif row["protocol_http"].lower() == "h3":
        http_score *= HTTP_V3_POINTS
    elif row["protocol_http"].lower() != "http/1.1":
        print(f"Unknown HTTP version ({row['protocol_http']}) at: {row['ETER_ID']} - {row['Url']}")

    return round(http_score, 2)


def check_inconsistencies(dataframe):
    dataframe["http_inconsistency_same_platform"] = False
    dataframe["http_inconsistency_between_platforms"] = False

    dataframe["http_inconsistency_same_platform"] = dataframe.groupby(
        ["ETER_ID", "platform"]
    )["final_url"].transform(
        lambda x: x.str.startswith("https://").nunique() > 1
    )

    dataframe["http_inconsistency_between_platforms"] = dataframe.groupby(
        ["ETER_ID"]
    )["final_url"].transform(
        lambda x: x.str.startswith("https://").nunique() > 1
    )

    return dataframe
