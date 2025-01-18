import os

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from src.analyzer.calculator.headers_calc import HEADER_COMPONENT_SCORE_COL, HEADER_SCORE_COL
from src.config import config

input_directory = os.path.join('../..', 'src', 'data', 'results', 'analysis', 'final_result_with_scores.csv')
output_directory = os.path.join('../..', 'src', 'data', 'results', 'analysis', 'graphs')
df = pd.read_csv(input_directory)


def get_data(dataframe):
    presence_columns = [col for col in dataframe.columns if col.endswith("_presence")]

    def select_representative_row(group):
        idx = (group[HEADER_SCORE_COL] - group[HEADER_SCORE_COL].median()).abs().idxmin()
        return group.loc[idx]

    selected_data = dataframe.groupby(["country", "platform", "ETER_ID"]).apply(select_representative_row).reset_index(
        drop=True)

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
    angles += angles[:1]  # Fechar o círculo

    # Criar uma figura com subplots horizontais
    fig, axes = plt.subplots(1, len(countries), subplot_kw=dict(polar=True), figsize=(6 * len(countries), 6))

    if len(countries) == 1:  # Caso haja apenas um país
        axes = [axes]

    for i, country in enumerate(countries):
        ax = axes[i]

        # Obter os dados para o país
        country_data = kpi_data.loc[country]
        desktop_usage = country_data.loc["desktop"].values
        mobile_usage = country_data.loc["mobile"].values

        # Fechar o círculo
        desktop_usage = np.append(desktop_usage, desktop_usage[0])
        mobile_usage = np.append(mobile_usage, mobile_usage[0])

        # Plotar as linhas no gráfico radar
        ax.plot(angles, desktop_usage, label="Desktop", color="blue")
        ax.fill(angles, desktop_usage, color="blue", alpha=0.25)
        ax.plot(angles, mobile_usage, label="Mobile", color="orange", linestyle="--")
        ax.fill(angles, mobile_usage, color="orange", alpha=0.25)

        # Configurar os rótulos
        ax.set_xticks(angles[:-1])
        ax.set_yticks([20, 40, 60, 80, 100])
        ax.set_yticklabels(["20%", "40%", "60%", "80%", "100%"], fontsize=10)
        ax.set_title(f"{get_country(country)}", fontsize=14, pad=20, y=1.05)

        for i, angle in enumerate(angles[:-1]):  # Skip the last angle (circle closure)
            header = headers[i]
            if header in highlight_positive:
                ax.text(angle, 110, header, color="green", fontsize=10, ha='center', va='center')
            elif header in highlight_deprecated:
                ax.text(angle, 110, header, color="red", fontsize=10, ha='center', va='center')
            else:
                ax.text(angle, 105, header, fontsize=10, ha='center', va='center')

        ax.xaxis.set_tick_params(labelcolor='none')
        ax.grid(True)
        # Adicionar a legenda
        ax.legend(loc="upper right", bbox_to_anchor=(1.2, 1.17))

    # Adicionar título geral para a figura

    fig.text(
        0.5, 0.95,  # Posição do título no eixo (x, y)
        "Usage of HTTP Security Headers (Desktop vs Mobile)",
        fontsize=16,
        fontweight="bold",
        ha="center"
    )
    # Ajustar espaçamento
    plt.tight_layout(rect=[0, 0, 1, 0.90])
    # fig.subplots_adjust(top=0.75, wspace=0.65)
    filename = os.path.join(output_directory, "radar_chart.pdf")
    fig.savefig(filename, format="pdf", bbox_inches="tight")
    plt.show()


if __name__ == "__main__":
    kpi = get_data(df)
    create_radar_charts(kpi)
