import os

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

from src.analyzer.graph_generator import get_country


def process_inconsistency_data(dataframe, ct):
    country_data = dataframe
    if ct != "":
        country_data = dataframe[dataframe["country"] == ct]
    unique_data = country_data.drop_duplicates(subset=["ETER_ID"])

    inconsistency_columns = [
        "critical_header_inconsistency_same_platform",
        "critical_header_inconsistency_between_platforms",
        "header_inconsistency_same_platform",
        "header_inconsistency_between_platforms",
        "http_inconsistency_same_platform",
        "http_inconsistency_between_platforms",
        "redirect_inconsistency_same_platform",
        "redirect_inconsistency_between_platforms",
    ]

    if ct != "":
        aggregated = unique_data.groupby("NUTS2_Label_2016")[inconsistency_columns].mean() * 100
    else:
        aggregated = unique_data.groupby("country")[inconsistency_columns].mean() * 100
    aggregated = aggregated.reset_index()
    return aggregated


def plot_dot_chart(aggregated_data, ct, output="output"):
    melted_data = aggregated_data.melt(id_vars="NUTS2_Label_2016", var_name="Inconsistency Type", value_name="Value")
    melted_data["Inconsistency Type"] = melted_data["Inconsistency Type"].str.replace("_", " ").str.capitalize()
    nuts2_mapping = {label: idx for idx, label in enumerate(melted_data["NUTS2_Label_2016"].unique())}
    melted_data["y_position"] = melted_data["NUTS2_Label_2016"].map(nuts2_mapping)
    melted_data["y_position"] += np.random.uniform(-0.3, 0.3, size=len(melted_data))

    fig, ax = plt.subplots(figsize=(10, 10))

    for inconsistency_type in melted_data["Inconsistency Type"].unique():
        subset = melted_data[melted_data["Inconsistency Type"] == inconsistency_type]
        ax.scatter(subset["Value"], subset["y_position"], label=inconsistency_type)

    ax.set_title(f"Security Headers Inconsistencies by NUTS2 in {get_country(ct)}", fontsize=16, pad=20, y=1)
    ax.set_xlabel("Proportion of Inconsistencies", fontsize=12, labelpad=15)
    ax.set_ylabel("NUTS2", fontsize=12)
    ax.set_yticks(list(nuts2_mapping.values()))
    ax.set_yticklabels(list(nuts2_mapping.keys()))
    ax.legend(title="Inconsistency Type", bbox_to_anchor=(1.05, 1), loc='upper left')
    ax.grid(axis='x', linestyle='--', alpha=0.7)

    plt.tight_layout()
    filename = os.path.join(output, f"{ct}_inconsistency.pdf")
    fig.savefig(filename, format="pdf", bbox_inches="tight")
    plt.show()


def plot_country_inconsistencies(aggregated_data, output="output"):
    melted_data = aggregated_data.melt(id_vars="country", var_name="Inconsistency Type", value_name="Value")
    melted_data["Inconsistency Type"] = melted_data["Inconsistency Type"].str.replace("_", " ").str.capitalize()
    melted_data["country"] = melted_data["country"].apply(get_country)
    country_mapping = {label: idx for idx, label in enumerate(melted_data["country"].unique())}
    melted_data["y_position"] = melted_data["country"].map(country_mapping)
    melted_data["y_position"] += np.random.uniform(-0.2, 0.2, size=len(melted_data))
    fig, ax = plt.subplots(figsize=(10, 3))

    for inconsistency_type in melted_data["Inconsistency Type"].unique():
        subset = melted_data[melted_data["Inconsistency Type"] == inconsistency_type]
        ax.scatter(subset["Value"], subset["y_position"], label=inconsistency_type)

    ax.set_title("Security Headers Inconsistencies by Country", fontsize=16, pad=20, y=1)
    ax.set_xlabel("Percentage of Inconsistencies", fontsize=12)
    ax.set_ylabel("Country", fontsize=12)
    ax.set_yticks(list(country_mapping.values()))
    ax.set_yticklabels(list(country_mapping.keys()))
    ax.legend(title="Inconsistency Type", bbox_to_anchor=(1.05, 1), loc='upper left')
    ax.grid(axis='x', linestyle='--', alpha=0.7)

    plt.tight_layout()
    filename = os.path.join(output, "country_inconsistencies.pdf")
    fig.savefig(filename, format="pdf", bbox_inches="tight")
    plt.show()


def generate_latex_table(dataframe, level, filename, title, label):
    dataframe = dataframe.pivot(index=level, columns="Inconsistency Type", values="Value").fillna(0)
    dataframe = dataframe.sort_values(
        by=["critical_header_inconsistency_between_platforms", "critical_header_inconsistency_same_platform"]
    )
    abbreviations = {
        "critical_header_inconsistency_same_platform": "Crit. hdr inc. same plt.",
        "critical_header_inconsistency_between_platforms": "Crit. hdr inc. btw plt.",
        "header_inconsistency_same_platform": "Hdr inc. same plt.",
        "header_inconsistency_between_platforms": "Hdr inc. btw plt.",
        "http_inconsistency_same_platform": "HTTP inc. same plt.",
        "http_inconsistency_between_platforms": "HTTP inc. btw plt.",
        "redirect_inconsistency_same_platform": "Redir. inc. same plt.",
        "redirect_inconsistency_between_platforms": "Redir. inc. btw plt.",
    }

    column_headers = " & ".join(
        f"\\rotatebox{{90}}{{\\makecell{{{abbreviations.get(col, col)}}}}}"
        for col in dataframe.columns
    )
    table_rows = "\n".join(
        f"            {row if level != 'country' else get_country(row)} & " + " & ".join(
            "-" if value == 0 else f"{int(value)}" if value == int(value) else f"{value:.2f}"
            for value in dataframe.loc[row]
        ) + " \\\\"
        for row in dataframe.index
    )

    latex_table = f"""
    \\begin{{table}}[H]
        \\centering
        \\caption{{{title}}}
        \\label{{tab:{label}}}
        \\rowcolors{{2}}{{white}}{{gray!15}}
        \\begin{{tabularx}}{{\\textwidth}}{{X{'c' * len(dataframe.columns)}}}
            \\toprule
            \\textbf{{{'NUTS2' if level != 'country' else 'Country'}}} & {column_headers} \\\\
             \\midrule
    {table_rows}
            \\bottomrule
        \\end{{tabularx}}
    \\end{{table}}
    """
    with open(filename, "w", encoding="utf-8") as tex_file:
        tex_file.write(latex_table)


if __name__ == "__main__":

    input_directory = os.path.join('../..', 'src', 'data', 'results', 'analysis', 'final_result_with_scores.csv')
    output_directory = os.path.join('../..', 'src', 'data', 'results', 'analysis', 'graphs')
    df = pd.read_csv(input_directory)
    countries = df["country"].unique()
    for country in countries:
        data = process_inconsistency_data(df, country)
        plot_dot_chart(data, country, output_directory)
        output_file_nuts = os.path.join(output_directory, '..', 'tables', f"{country}_nuts_inconsistencies.tex")
        generate_latex_table(
            data.melt(id_vars="NUTS2_Label_2016", var_name="Inconsistency Type", value_name="Value"),
            level="NUTS2_Label_2016",
            filename=output_file_nuts,
            title=f"Security Headers Inconsistencies by NUTS2 in {get_country(country)}",
            label=f"nuts2_inconsistencies_{country}"
        )
    aggregated_data_with_country = process_inconsistency_data(df, "")
    plot_country_inconsistencies(aggregated_data_with_country, output_directory)
    generate_latex_table(
        aggregated_data_with_country.melt(id_vars="country", var_name="Inconsistency Type", value_name="Value"),
        level="country",
        filename=os.path.join(output_directory, '..', 'tables', 'country_sh_inconsistencies_table.tex'),
        title="Security Headers Inconsistencies by Country",
        label="country_inconsistencies"
    )
