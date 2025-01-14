import pandas as pd

from src.config import config

UB = config.get("basic_point_unit", 10)
PENALTY_DEPRECATED_HEADER = -2.5 * UB
PENALTY_SAME_PLATFORM_CRITICAL = -1.5 * UB
PENALTY_SAME_PLATFORM_NON_CRITICAL = -1 * UB
PENALTY_BETWEEN_PLATFORMS_CRITICAL = -2 * UB
PENALTY_BETWEEN_PLATFORMS_NON_CRITICAL = -1.5 * UB
STRONG_CONFIGURATION = 0.5 * UB
WEAK_CONFIGURATION = -2 * UB


def calculate_header_scores(dataframe):
    expected_headers = list({k.lower(): v for k, v in config['expected_headers'].items()}.keys())
    platform_counts = dataframe["platform"].nunique()
    dataframe["header_score"] = 0
    dataframe["total_header_score"] = 0
    check_inconsistencies(dataframe)

    for header in expected_headers:
        dataframe[f"{header}_score"] = dataframe.apply(lambda x: calculate_header_presence_and_config(header, x),
                                                       axis=1)
    for header in expected_headers:
        dataframe["header_score"] += dataframe[f"{header}_score"]

    # Escolha da Medição Diária por Plataforma:
    # Identifica a linha mediana do header_score para cada dia e plataforma
    median_rows = (
        dataframe.groupby(["ETER_ID", "assessment_date", "platform"])["header_score"]
        .apply(lambda x: x.idxmax() if len(x) == 1 else x.sort_values().iloc[len(x) // 2:].index[0])  # Mediana
        .reset_index(name="median_index")
    )

    # Pontuação Total Diária por Cabeçalho:
    # Penalidades
    penalties = dataframe.groupby("ETER_ID").apply(
        lambda group: {
            "same_platform_penalty": (
                PENALTY_SAME_PLATFORM_CRITICAL
                if group["critical_inconsistency_same_platform"].any()
                else PENALTY_SAME_PLATFORM_NON_CRITICAL
                if group["header_inconsistency_same_platform"].any()
                else 0
            ),
            "between_platforms_penalty": (
                PENALTY_BETWEEN_PLATFORMS_CRITICAL
                if group["critical_inconsistency_between_platforms"].any()
                else PENALTY_BETWEEN_PLATFORMS_NON_CRITICAL
                if group["header_inconsistency_between_platforms"].any()
                else 0
            ),
        }
    )

    # Aplicação de penalidades diretamente no cálculo
    daily_scores_with_penalties = (
        dataframe.loc[median_rows["median_index"]]
        .groupby(["ETER_ID", "assessment_date"])
        .agg(daily_header_score=("daily_header_score", "mean"))
        .reset_index()
        .assign(
            penalty_same_platform=lambda df: df["ETER_ID"].map(
                lambda eter_id: penalties[eter_id]["same_platform_penalty"]),
            penalty_between_platforms=lambda df: df["ETER_ID"].map(
                lambda eter_id: penalties[eter_id]["between_platforms_penalty"] * platform_counts
            ),
        )
        .eval("daily_header_score = daily_header_score + penalty_same_platform + penalty_between_platforms")
    )

    # Pontuação Total dos Cabeçalhos:
    # a pontuação total do cabeçalho é a mediana das pontuações totais diárias:
    final_header_score = (
        daily_scores_with_penalties.groupby("ETER_ID")["final_score"]
        .median()  # Aqui escolhemos a mediana entre os dias avaliados
        .reset_index(name="total_header_score")
    )
    dataframe = dataframe.merge(final_header_score, on="ETER_ID", how="left")
    return dataframe



def calculate_header_presence_and_config(header, row):
    deprecated_headers = [h.lower() for h in config["deprecated_headers"]]
    multipliers = {k.lower(): v for k, v in config['header_multipliers'].items()}
    presence_col = f"{header}_presence"
    config_col = f"{header}_config"
    header_score = 0

    if row.get(presence_col, False):
        header_score += UB

        if header in deprecated_headers:
            header_score += PENALTY_DEPRECATED_HEADER

        config_value = row.get(config_col, "Missing")
        if config_value.lower() == "strong":
            header_score += STRONG_CONFIGURATION
        elif config_value.lower() == "weak":
            header_score += WEAK_CONFIGURATION

        header_score *= multipliers.get(header, 1)

    return header_score


def check_inconsistencies(dataframe):
    dataframe["critical_inconsistency_same_platform"] = False
    dataframe["critical_inconsistency_between_platforms"] = False
    dataframe["header_inconsistency_between_platforms"] = False
    dataframe["header_inconsistency_same_platform"] = False

    expected_headers = list({k.lower(): v for k, v in config['expected_headers'].items()}.keys())
    critical_headers = [header.lower() for header in config["critical_headers"]]

    for header in expected_headers:
        presence_inconsistency_same_platform_col = f"{header}_presence_inconsistency_same_platform"
        dataframe[presence_inconsistency_same_platform_col] = False
        presence_inconsistency_between_platforms_col = f"{header}_presence_inconsistency_between_platforms"
        dataframe[presence_inconsistency_between_platforms_col] = False
        config_inconsistency_same_platform_col = f"{header}_config_inconsistency_same_platform"
        dataframe[config_inconsistency_same_platform_col] = False
        config_inconsistency_between_platforms_col = f"{header}_config_inconsistency_between_platforms"
        dataframe[config_inconsistency_between_platforms_col] = False

        # Verifica inconsistências na mesma plataforma
        same_platform_presence_inconsistencies = (
            dataframe.groupby(["ETER_ID", "assessment_date", "platform"])[f"{header}_presence"]
            .transform(lambda x: x.nunique() > 1)
        )
        dataframe[presence_inconsistency_same_platform_col] = same_platform_presence_inconsistencies

        same_platform_config_inconsistencies = (
            dataframe.groupby(["ETER_ID", "assessment_date", "platform"])[f"{header}_config"]
            .transform(lambda x: x.nunique() > 1)
        )
        dataframe[config_inconsistency_same_platform_col] = same_platform_config_inconsistencies

        # Verifica inconsistências entre plataformas
        between_platforms_presence_inconsistencies = (
            dataframe.groupby(["ETER_ID", "assessment_date"])[f"{header}_presence"]
            .transform(lambda x: x.nunique() > 1)
        )
        dataframe[presence_inconsistency_between_platforms_col] = between_platforms_presence_inconsistencies

        between_platforms_config_inconsistencies = (
            dataframe.groupby(["ETER_ID", "assessment_date"])[f"{header}_config"]
            .transform(lambda x: x.nunique() > 1)
        )
        dataframe[config_inconsistency_between_platforms_col] = between_platforms_config_inconsistencies

    # Calcula inconsistências críticas na mesma plataforma
    critical_inconsistencies_same_platform_cols = [
                                                      f"{header}_presence_inconsistency_same_platform" for header in
                                                      critical_headers
                                                  ] + [
                                                      f"{header}_config_inconsistency_same_platform" for header in
                                                      critical_headers
                                                  ]
    critical_inconsistencies_same_platform = (
        dataframe.groupby(["ETER_ID", "assessment_date", "platform"])[critical_inconsistencies_same_platform_cols]
        .any()
        .any(axis=1)
        .reset_index(name="temp_critical_inconsistency_same_platform")
    )

    dataframe = dataframe.merge(
        critical_inconsistencies_same_platform,
        on=["ETER_ID", "assessment_date", "platform"],
        how="left"
    )

    dataframe["critical_inconsistency_same_platform"] = dataframe[
                                                            "critical_inconsistency_same_platform"
                                                        ] | dataframe[
                                                            "temp_critical_inconsistency_same_platform"].fillna(False)

    inconsistent_same_platform = dataframe[dataframe["critical_inconsistency_same_platform"]]
    for _, row in inconsistent_same_platform.iterrows():
        dataframe.loc[
            (dataframe["ETER_ID"] == row["ETER_ID"]) &
            (dataframe["assessment_date"] == row["assessment_date"]) &
            (dataframe["platform"] == row["platform"]),
            "header_inconsistency_same_platform"
        ] = True

    dataframe.drop(columns=["temp_critical_inconsistency_same_platform"], inplace=True)

    # Calcula inconsistências críticas entre plataformas
    critical_inconsistencies_between_platforms_cols = [
                                                          f"{header}_presence_inconsistency_between_platforms" for
                                                          header in
                                                          critical_headers
                                                      ] + [
                                                          f"{header}_config_inconsistency_between_platforms" for header
                                                          in
                                                          critical_headers
                                                      ]
    critical_inconsistencies_between_platforms = (
        dataframe.groupby(["ETER_ID", "assessment_date"])[critical_inconsistencies_between_platforms_cols]
        .any()
        .any(axis=1)
        .reset_index(name="temp_critical_inconsistency_between_platforms")
    )

    dataframe = dataframe.merge(
        critical_inconsistencies_between_platforms,
        on=["ETER_ID", "assessment_date"],
        how="left"
    )

    dataframe["critical_inconsistency_between_platforms"] = dataframe[
                                                                "critical_inconsistency_between_platforms"
                                                            ] | dataframe[
                                                                "temp_critical_inconsistency_between_platforms"].fillna(
        False)

    inconsistent_between_platforms = dataframe[dataframe["critical_inconsistency_between_platforms"]]
    for _, row in inconsistent_between_platforms.iterrows():
        dataframe.loc[
            (dataframe["ETER_ID"] == row["ETER_ID"]),
            "header_inconsistency_between_platforms"
        ] = True

    dataframe.drop(columns=["temp_critical_inconsistency_between_platforms"], inplace=True)
