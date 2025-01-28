from src.config import COL_HTTP_INCONSISTENCY_BETWEEN_PLATFORMS

HTTP_V2_POINTS = 1.1
HTTP_V3_POINTS = 1.3
HTTPS_PRESENCE = 100 / HTTP_V3_POINTS
PENALTY_BETWEEN_PLATFORMS = 0.1
HTTP_SCORE_BY_PLATFORM_COL = "http_score_by_platform"
HTTP_AVG_SCORE_BTW_PLATFORMS_COL = "http_avg_score_btw_platforms"
HTTP_COMPONENT_SCORE_COL = "http_component_score"


def calculate_http_scores(dataframe):
    platform_counts = dataframe["platform"].nunique()
    dataframe[HTTP_SCORE_BY_PLATFORM_COL] = 0
    dataframe[HTTP_COMPONENT_SCORE_COL] = 0
    dataframe[HTTP_AVG_SCORE_BTW_PLATFORMS_COL] = 0

    dataframe[HTTP_SCORE_BY_PLATFORM_COL] = dataframe.apply(calculate_http_presence_and_version, axis=1)

    dataframe[HTTP_AVG_SCORE_BTW_PLATFORMS_COL] = (dataframe.groupby(["ETER_ID"])[HTTP_SCORE_BY_PLATFORM_COL]
                                                   .transform("mean").round(2))

    check_inconsistencies(dataframe)

    penalty_combined = (
            dataframe[COL_HTTP_INCONSISTENCY_BETWEEN_PLATFORMS]
            * PENALTY_BETWEEN_PLATFORMS
            * (platform_counts / 100)
    )
    penalty_combined = penalty_combined.where(penalty_combined > 0, 1)
    dataframe[HTTP_COMPONENT_SCORE_COL] = (
            dataframe[HTTP_AVG_SCORE_BTW_PLATFORMS_COL]
            * penalty_combined
    ).clip(upper=100).round(2)

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
    elif row["protocol_http"].lower() != "http/1.1" and row["protocol_http"].lower() != "http/1.0":
        print(f"Unknown HTTP version ({row['protocol_http']}) at: {row['ETER_ID']} - {row['Url']}")

    return max(round(http_score, 2), 1)


def check_inconsistencies(dataframe):
    dataframe["final_url"] = dataframe["final_url"].astype(str)
    dataframe[COL_HTTP_INCONSISTENCY_BETWEEN_PLATFORMS] = dataframe.groupby(
        ["ETER_ID"]
    )["final_url"].transform(
        lambda x: x.str.startswith("https://").nunique() > 1
    )
