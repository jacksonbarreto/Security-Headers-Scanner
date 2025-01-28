import os
import pandas as pd

from src.analyzer.report.graph_generator import get_country


def generate_nuts_heatmap_csvs(dataframe, output="output"):
    os.makedirs(output, exist_ok=True)

    countries = dataframe["country"].unique()
    for country in countries:
        country_data = dataframe[dataframe["country"] == country]

        nuts_mean_scores = country_data.groupby("NUTS2_Label_2016")["final_score"].mean().reset_index()

        output_file = os.path.join(output, f"{country}_nuts_scores.csv")
        nuts_mean_scores.to_csv(output_file, index=False)
        print(f"Saved file: {output_file}")
        output_table_file = os.path.join(output, '..', 'tables')
        generate_latex_table_from_csv(output_file, country, output_table_file)

def generate_latex_table_from_csv(csv_file, country, output="output"):
    os.makedirs(output, exist_ok=True)

    dataframe = pd.read_csv(csv_file)
    dataframe = dataframe.sort_values(by="final_score", ascending=False)

    table_rows = "\n".join(
        f"            {row['NUTS2_Label_2016']} & {row['final_score']:.2f} \\\\"
        for _, row in dataframe.iterrows()
    )

    latex_table = f"""
    \\begin{{table}}[ht]
        \\centering
        \\caption{{Security Headers Final Scores for NUTS2 in {get_country(country)}}}
        \\label{{tab:final_grades_sh_{country.lower()}}}
        \\rowcolors{{2}}{{white}}{{gray!15}}
        \\begin{{tabular}}{{lr}}
            \\toprule
            \\textbf{{NUTS2}} & \\textbf{{Score}} \\\\
            \\midrule
{table_rows}
            \\bottomrule
        \\end{{tabular}}
    \\end{{table}}
    """

    output_file = os.path.join(output, f"{country}_sh_nuts_table.tex")
    with open(output_file, "w", encoding="utf-8") as f:
        f.write(latex_table)

    print(f"LaTeX table saves in: {output_file}")


if __name__ == "__main__":
    input_directory = os.path.join('../../..', 'src', 'data', 'results', 'analysis', 'final_result_with_scores.csv')
    output_directory = os.path.join('../../..', 'src', 'data', 'results', 'analysis', 'choropleth_map')
    df = pd.read_csv(input_directory)
    generate_nuts_heatmap_csvs(df, output_directory)


