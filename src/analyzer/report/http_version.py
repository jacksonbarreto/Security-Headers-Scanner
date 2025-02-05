import os

import pandas as pd
import matplotlib.pyplot as plt
from src.analyzer.report.header_adoption import get_country
from src.analyzer.report.setup import RESULT_FILE_PATH, TABLE_DIRECTORY, CHART_DIRECTORY

HTTP_VERSIONS = ["http/3", "http/2", "http/1.1", "http/1.0"]


def prepare_http_stats(dataframe):
    dataframe["protocol_http"] = dataframe["protocol_http"].replace({"h2": "http/2", "h3": "http/3"})
    stats_by_nuts = dataframe.groupby(["country", "NUTS2_Label_2016"])["protocol_http"].value_counts().unstack().fillna(
        0)
    stats_by_nuts = stats_by_nuts[HTTP_VERSIONS]
    stats_by_nuts["total_schools_nuts"] = stats_by_nuts.sum(axis=1)

    stats_by_country = dataframe.groupby("country")["protocol_http"].value_counts().unstack().fillna(0)
    stats_by_country = stats_by_country[HTTP_VERSIONS]
    stats_by_country["total_schools_country"] = stats_by_country.sum(axis=1)

    for version in HTTP_VERSIONS:
        stats_by_nuts[f"{version}_percent_nuts"] = (stats_by_nuts[version] / stats_by_nuts["total_schools_nuts"]) * 100

    for version in HTTP_VERSIONS:
        stats_by_country[f"{version}_percent_country"] = (stats_by_country[version] / stats_by_country[
            "total_schools_country"]) * 100

    stats_by_nuts = stats_by_nuts.reset_index()
    stats_by_country = stats_by_country.reset_index()

    stats_by_nuts.rename(columns={"NUTS2_Label_2016": "nuts"}, inplace=True)

    consolidated_stats = stats_by_nuts.merge(
        stats_by_country,
        on="country",
        how="left",
        suffixes=("_nuts", "_country")
    )

    return consolidated_stats


def latex_http_table(dataframe, level, title, label):
    if level == "nuts":
        columns_to_display = ["nuts"] + [f"{col}_percent_nuts" for col in HTTP_VERSIONS]
        dataframe = dataframe.sort_values(by=[f"{col}_percent_nuts" for col in HTTP_VERSIONS], ascending=False)
        rename_map = {
            "nuts": "NUTS2",
            **{f"{col}_percent_nuts": col.upper().replace("/", "-") for col in HTTP_VERSIONS}
        }
    elif level == "country":
        dataframe = dataframe.drop_duplicates(subset=["country"])
        columns_to_display = ["country"] + [f"{col}_percent_country" for col in HTTP_VERSIONS]
        dataframe = dataframe.sort_values(by=[f"{col}_percent_country" for col in HTTP_VERSIONS], ascending=False)
        rename_map = {
            "country": "Country",
            **{f"{col}_percent_country": col.upper().replace("/", "-") for col in HTTP_VERSIONS}
        }
    else:
        raise ValueError("Invalid level. Use 'nuts' or 'country'.")

    dataframe = dataframe[columns_to_display].rename(columns=rename_map)

    column_headers = " & ".join(f"\\makecell{{{col}}}" for col in dataframe.columns)

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


def generate_http_adoption_tables(stats_dataframe):
    countries = stats_dataframe["country"].unique()

    for country in countries:
        filtered_df = stats_dataframe[stats_dataframe["country"] == country]
        nuts2_table = latex_http_table(filtered_df, "nuts",
                                       f"HTTP Version Adoption in {get_country(country)} by NUTS2 (\\%)",
                                       f"nuts2_http_version_adoption_in_{country.lower()}")
        path_to_save = os.path.join(TABLE_DIRECTORY, f"sh_http_version_adoption_in_{country}_by_nuts2.tex")
        with open(path_to_save, "w", encoding="utf-8") as tex_file:
            tex_file.write(nuts2_table)

    country_table = latex_http_table(stats_dataframe, "country", "HTTP Version Adoption by Country (\\%)",
                                     "country_http_version_adoption")
    path_to_save = os.path.join(TABLE_DIRECTORY, "sh_http_version_adoption_by_country.tex")
    with open(path_to_save, "w", encoding="utf-8") as tex_file:
        tex_file.write(country_table)


def plot_http_adoption_chart(dataframe, level, title, country_filter=None):
    if level == "nuts":
        if country_filter:
            dataframe = dataframe[dataframe["country"] == country_filter]
        y_column = "nuts"
        columns_to_plot = [f"{col}_percent_nuts" for col in HTTP_VERSIONS]
        num_rows = dataframe[y_column].nunique()
        size_box = (10, max(6, num_rows * 0.32))
    elif level == "country":
        dataframe["country"] = dataframe["country"].apply(get_country)
        dataframe = dataframe.drop_duplicates(subset=["country"])
        y_column = "country"
        columns_to_plot = [f"{col}_percent_country" for col in HTTP_VERSIONS]
        num_rows = dataframe[y_column].nunique()
        size_box = (10, max(3, num_rows * 0.8))
    else:
        raise ValueError("Invalid level. Use 'nuts' or 'country'.")

    dataframe = dataframe[[y_column] + columns_to_plot].set_index(y_column)
    fig, ax = plt.subplots(figsize=size_box)

    # colorblind-friendly do ggplot2
    custom_colors = {
        "http/3_percent_nuts": "#009E73",
        "http/2_percent_nuts": "#0072B2",
        "http/1.1_percent_nuts": "#E69F00",
        "http/1.0_percent_nuts": "#D55E00",
        "http/3_percent_country": "#009E73",
        "http/2_percent_country": "#0072B2",
        "http/1.1_percent_country": "#E69F00",
        "http/1.0_percent_country": "#D55E00",
    }

    dataframe.plot(kind='barh', stacked=True, color=[custom_colors[col] for col in columns_to_plot],
                   edgecolor="black", ax=ax)

    ax.set_xlabel("Adoption of HTTP Versions (%)", fontsize=12)
    ax.set_ylabel("NUTS2" if level == "nuts" else "Country", fontsize=12)
    ax.set_title(title, fontsize=16, pad=50, y=1)
    ax.legend(HTTP_VERSIONS, title="HTTP Version", loc="lower left", bbox_to_anchor=(0, 1), ncol=4, frameon=False)
    ax.grid(axis="x", linestyle="--", alpha=0.5)

    plt.tight_layout()
    return fig


def generate_http_adoption_chart(dataframe):
    total_countries = dataframe["country"].unique()
    for country in total_countries:
        fig = plot_http_adoption_chart(dataframe, "nuts",
                                       f"HTTP Version Adoption by NUTS2 in {get_country(country)}",
                                       country)
        file_name = f"sh_http_version_adoption_by_nuts2_in_{country}.pdf"
        path_to_save = os.path.join(CHART_DIRECTORY, file_name)
        fig.savefig(path_to_save, format="pdf", bbox_inches="tight")
        plt.show()

    fig = plot_http_adoption_chart(dataframe, "country", "HTTP Version Adoption by Country")
    file_name = "sh_http_version_adoption_by_country.pdf"
    path_to_save = os.path.join(CHART_DIRECTORY, file_name)
    fig.savefig(path_to_save, format="pdf", bbox_inches="tight")
    plt.show()


def make_http_version_adoption():
    df = pd.read_csv(RESULT_FILE_PATH)
    stats = prepare_http_stats(df)
    generate_http_adoption_tables(stats)
    generate_http_adoption_chart(stats)



if __name__ == "__main__":
    make_http_version_adoption()
