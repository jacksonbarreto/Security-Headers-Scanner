import os

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from src.analyzer.calculator.headers_calc import HEADER_SCORE_BY_PLATFORM_COL
from src.config import config




def get_data(dataframe):
    presence_columns = [col for col in dataframe.columns if col.endswith("_presence")]

    medians = dataframe.groupby(["country", "platform", "ETER_ID"])[HEADER_SCORE_BY_PLATFORM_COL].transform("median")
    dataframe["abs_diff"] = (dataframe[HEADER_SCORE_BY_PLATFORM_COL] - medians).abs()

    min_diff_idx = dataframe.groupby(["country", "platform", "ETER_ID"])["abs_diff"].idxmin()

    selected_data = dataframe.loc[min_diff_idx].reset_index(drop=True)

    kpi_data = selected_data.groupby(["country", "platform"])[presence_columns].mean() * 100

    return kpi_data


def get_country(country):
    if country == "de":
        return "Germany"
    elif country == "fr":
        return "France"
    elif country == "it":
        return "Italy"
    return country


def create_radar_charts(kpi_data):
    # # Headers to highlight
    highlight_positive = config["critical_headers"]
    highlight_deprecated = config["deprecated_headers"]
    countries = kpi_data.index.get_level_values("country").unique()
    headers = list(config["expected_headers"].keys())
    num_headers = len(headers)
    angles = np.linspace(0, 2 * np.pi, num_headers, endpoint=False).tolist()
    angles += angles[:1]

    fig, axes = plt.subplots( len(countries), 1, subplot_kw=dict(polar=True), figsize=(8, 3.8 * len(countries)))

    if len(countries) == 1:
        axes = [axes]

    for i, country in enumerate(countries):
        ax = axes[i]

        country_data = kpi_data.loc[country]
        desktop_usage = country_data.loc["desktop"].values
        mobile_usage = country_data.loc["mobile"].values

        # close the circle
        desktop_usage = np.append(desktop_usage, desktop_usage[0])
        mobile_usage = np.append(mobile_usage, mobile_usage[0])

        # Plot the lines on the radar chart
        ax.plot(angles, desktop_usage, label="Desktop", color="blue")
        ax.fill(angles, desktop_usage, color="blue", alpha=0.25)
        ax.plot(angles, mobile_usage, label="Mobile", color="orange", linestyle="--")
        ax.fill(angles, mobile_usage, color="orange", alpha=0.25)

        # Configuring labels
        ax.set_xticks(angles[:-1])
        ax.set_yticks([20, 40, 60, 80, 100])
        ax.set_yticklabels(["20%", "40%", "60%", "80%", "100%"], fontsize=8)
        ax.set_title(f"{get_country(country)}", fontsize=14, pad=20, y=1.05)

        for j, angle in enumerate(angles[:-1]):  # Skip the last angle (circle closure)
            header = headers[j]

            if header in highlight_positive:
                ax.text(angle, 110, header, color="green", fontsize=9, ha='center', va='center')
            elif header in highlight_deprecated:
                ax.text(angle, 110, header, color="red", fontsize=9, ha='center', va='center')
            else:
                ax.text(angle, 105, header, fontsize=9, ha='center', va='center')

        ax.xaxis.set_tick_params(labelcolor='none')
        ax.grid(True)
        # legend
        ax.legend(loc="upper right", bbox_to_anchor=(1.5, 1.22))

    # General Title
    fig.text(
        0.5, 0.95,
        "Adoption of HTTP Security Headers (Desktop vs Mobile)",
        fontsize=16,
        fontweight="bold",
        ha="center"
    )

    plt.tight_layout(rect=[0, 0, 1, 0.94])
    filename = os.path.join(output_directory, "adoption_sh_by_platform.pdf")
    fig.savefig(filename, format="pdf", bbox_inches="tight")
    plt.show()


if __name__ == "__main__":
    input_directory = os.path.join('../../..', 'src', 'data', 'results', 'analysis', 'final_result_with_scores.csv')
    output_directory = os.path.join('../../..', 'src', 'data', 'results', 'analysis', 'graphs')
    df = pd.read_csv(input_directory)
    kpi = get_data(df)

    create_radar_charts(kpi)
