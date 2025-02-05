import os

import pandas as pd
import matplotlib.pyplot as plt

from src.analyzer.report.header_adoption import get_country
from src.analyzer.report.setup import TABLE_DIRECTORY, CHART_DIRECTORY, RESULT_FILE_PATH
from src.config import COL_REDIRECT_INCONSISTENCY_BETWEEN_PLATFORMS, COL_HEADER_INCONSISTENCY_BETWEEN_PLATFORMS, \
    COL_CRITICAL_HEADER_INCONSISTENCY_BETWEEN_PLATFORMS

inconsistency_columns = [
    COL_CRITICAL_HEADER_INCONSISTENCY_BETWEEN_PLATFORMS,
    COL_HEADER_INCONSISTENCY_BETWEEN_PLATFORMS,
    COL_REDIRECT_INCONSISTENCY_BETWEEN_PLATFORMS
]


def prepare_inconsistency_stats(dataframe):
    _stats_by_nuts = dataframe.groupby(["country", "NUTS2_Label_2016"]).agg(
        total_schools_nuts=("ETER_ID", "count"),
        **{f"{col}_schools_nuts": (col, "sum") for col in inconsistency_columns},
    ).reset_index()

    _stats_by_country = dataframe.groupby("country").agg(
        total_schools_country=("ETER_ID", "count"),
        **{f"{col}_schools_country": (col, "sum") for col in inconsistency_columns},
    ).reset_index()
    consolidated_stats = _stats_by_nuts.merge(
        _stats_by_country,
        on="country",
        how="left"
    )
    for col in inconsistency_columns:
        consolidated_stats[f"{col}_percent_nuts"] = (
                (consolidated_stats[f"{col}_schools_nuts"] / consolidated_stats["total_schools_nuts"]) * 100
        ).round(2)

        consolidated_stats[f"{col}_percent_country"] = (
                (consolidated_stats[f"{col}_schools_country"] / consolidated_stats["total_schools_country"]) * 100
        ).round(2)

        consolidated_stats.rename(columns={"NUTS2_Label_2016": "nuts"}, inplace=True)

    return consolidated_stats


def latex_table(dataframe, level, title, label, country_filter=None):
    if level == "nuts":
        if country_filter:
            dataframe = dataframe[dataframe["country"] == country_filter]
        columns_to_display = ["nuts"] + [f"{col}_percent_nuts" for col in inconsistency_columns]
        rename_map = {
            "nuts": "NUTS2",
            **{f"{col}_percent_nuts": col.replace("_", " ").title().replace(" Between Platforms", "") for col in
               inconsistency_columns},
        }
    elif level == "country":
        dataframe = dataframe.drop_duplicates(subset=["country"])
        columns_to_display = ["country"] + [f"{col}_percent_country" for col in inconsistency_columns]
        rename_map = {
            "country": "Country",
            **{f"{col}_percent_country": col.replace("_", " ").title().replace(" Between Platforms", "") for col in
               inconsistency_columns},
        }
    else:
        raise ValueError("Invalid level. Use 'nuts' or 'country'.")

    dataframe = dataframe[columns_to_display].rename(columns=rename_map)
    dataframe = dataframe.sort_values(by=[
        col.replace("_", " ").title().replace(" Between Platforms", "") for col in inconsistency_columns
    ], ascending=False, kind="mergesort")

    column_headers = " & ".join(f"\\makecell{{{col.replace(' Inconsistency','')}}}" for col in dataframe.columns)

    table_rows = "\n".join(
        f"            {row[0] if level != 'country' else get_country(row[0])} & " + " & ".join(
            "-" if pd.isna(value) or value == 0
            else f"{int(value)}" if isinstance(value, (float, int)) and value == int(value)
            else f"{value:.2f}" if isinstance(value, float)
            else str(value)
            for value in row[1:]
        ) + " \\\\"
        for row in dataframe.itertuples(index=False, name=None)
    )

    latex_table = f"""
\\begin{{table}}[H]
    \\centering
    \\caption{{{title}}}
    \\label{{tab:{label}}}
    \\rowcolors{{2}}{{white}}{{gray!15}}
    \\begin{{tabularx}}{{\\textwidth}}{{X{'c' * len(dataframe.columns)}}}
        \\toprule
        {column_headers} \\\\
        \\midrule
{table_rows}
        \\bottomrule
    \\end{{tabularx}}
\\end{{table}}
    """
    return latex_table


def generate_latex_table(dataframe):
    total_countries = dataframe["country"].unique()
    for country in total_countries:
        nuts2_table = latex_table(dataframe, "nuts",
                                  f"Security Headers Inconsistencies in {get_country(country)} by NUTS2 (\\%)",
                                  f"nuts2_inconsistencies_{country}", country)
        file_name = f"sh_inconsistencies_in_{country}_by_nuts2.tex"
        path_to_save = os.path.join(TABLE_DIRECTORY, file_name)
        with open(path_to_save, "w", encoding="utf-8") as tex_file:
            tex_file.write(nuts2_table)

    country_table = latex_table(dataframe, "country", "Security Headers Inconsistencies by Country (\\%)",
                                "country_inconsistencies")
    file_name = "sh_inconsistencies_by_country.tex"
    path_to_save = os.path.join(TABLE_DIRECTORY, file_name)
    with open(path_to_save, "w", encoding="utf-8") as tex_file:
        tex_file.write(country_table)


def plot_dot_chart(dataframe, level, title, country_filter=None):
    if level == "nuts":
        if country_filter:
            dataframe = dataframe[dataframe["country"] == country_filter]
        y_column = "nuts"
        columns_to_plot = [f"{col}_percent_nuts" for col in inconsistency_columns]
        num_rows = dataframe[y_column].nunique()
        size_box = (10, max(6, num_rows * 0.3))
    elif level == "country":
        dataframe["country"] = dataframe["country"].apply(get_country)
        dataframe = dataframe.drop_duplicates(subset=["country"])
        y_column = "country"
        columns_to_plot = [f"{col}_percent_country" for col in inconsistency_columns]
        num_rows = dataframe[y_column].nunique()
        size_box = (10, max(3, num_rows * 0.5))
    else:
        raise ValueError("Invalid level. Use 'nuts' or 'country'.")

    dataframe = dataframe[[y_column] + columns_to_plot]
    for col in columns_to_plot:
        dataframe[col] = dataframe[col].astype(float)

    melted_data = dataframe.melt(
        id_vars=[y_column],
        value_vars=columns_to_plot,
        var_name="Inconsistency Type",
        value_name="Percentage"
    )

    melted_data[y_column] = pd.Categorical(
        melted_data[y_column],
        categories=melted_data.groupby(y_column)["Percentage"].sum().sort_values(ascending=False).index,
        ordered=True
    )
    fig, ax = plt.subplots(figsize=size_box)
    markers = ["o", "s", "^"]
    colors = ["#D55E00", "#E69F00", "#0072B2"]
    labels = ["Critical Header Inconsistency", "Header Inconsistency", "Redirect Inconsistency"]
    for col, marker, color, label in zip(columns_to_plot, markers, colors, labels):
        subset = melted_data[melted_data["Inconsistency Type"] == col]
        ax.scatter(subset["Percentage"], subset[y_column], marker=marker, label=label, alpha=0.7, color=color, s=100)

    ax.set_xlabel("Inconsistencies Between Platforms (%)", fontsize=12)
    ax.set_ylabel("NUTS2" if level == "nuts" else "Country", fontsize=12)
    ax.set_title(title, fontsize=16, pad=20, y=1)
    ax.legend(title="Inconsistency Type", bbox_to_anchor=(1.05, 1), loc="upper left")
    ax.grid(axis="x", linestyle="--", alpha=0.7)

    plt.tight_layout()
    return fig


def generate_plot_dot_chart(dataframe):
    total_countries = dataframe["country"].unique()
    print(f"countries: {total_countries}")
    for country in total_countries:
        fig = plot_dot_chart(dataframe, "nuts",
                                          f"Security Headers Inconsistencies by NUTS2 in {get_country(country)}",
                                          country)
        file_name = f"sh_chart_inconsistencies_by_nuts2_{country}.pdf"
        path_to_save = os.path.join(CHART_DIRECTORY, file_name)
        fig.savefig(path_to_save, format="pdf", bbox_inches="tight")
        plt.show()
    fig = plot_dot_chart(dataframe, "country", "Security Headers Inconsistencies by Country")
    file_name = "sh_chart_inconsistencies_by_country.pdf"
    path_to_save = os.path.join(CHART_DIRECTORY, file_name)
    fig.savefig(path_to_save, format="pdf", bbox_inches="tight")
    plt.show()


def make_inconsistencies():
    df = pd.read_csv(RESULT_FILE_PATH)
    stats = prepare_inconsistency_stats(df)
    generate_latex_table(stats)
    generate_plot_dot_chart(stats)


if __name__ == "__main__":
    make_inconsistencies()
