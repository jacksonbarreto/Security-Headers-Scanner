import os

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from src.analyzer.headers_calc import HEADER_COMPONENT_SCORE_COL
from src.config import config

input_directory = os.path.join('.', 'src', 'data', 'results', 'final_scores.csv')
df = pd.read_csv(input_directory)

def get_data(dataframe):
    presence_columns = [col for col in dataframe.columns if col.endswith("_presence")]

    # Aplicar a lógica diretamente no apply
    selected_data = dataframe.groupby(["country", "platform", "ETER_ID"]).apply(
        lambda group: group.loc[
            group[HEADER_COMPONENT_SCORE_COL] == group[HEADER_COMPONENT_SCORE_COL].median()
            ].iloc[0]
    )

    # Resetar o índice após o agrupamento
    selected_data.reset_index(drop=True, inplace=True)

    # Agregar dados para calcular KPIs
    kpi_data = selected_data.groupby(["country", "platform"])[presence_columns].mean() * 100

    # Retornar os dados processados e prontos para visualização
    return kpi_data, selected_data

def get_country(country):
    if country == "de":
        return "Germany"
    elif country == "fr":
        return "France"
    elif country == "it":
        return "Italy"
    return country

kpi, selectedData = get_data(df)



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
                 ax.text(angle, 110, header, color="red",  fontsize=10, ha='center', va='center')
             else:
                 ax.text(angle, 105, header, fontsize=10, ha='center', va='center')

        ax.xaxis.set_tick_params(labelcolor='none')
        ax.grid(True)
        # Adicionar a legenda
        ax.legend(loc="upper right", bbox_to_anchor=(1.2, 1.1))

    # Adicionar título geral para a figura

    fig.text(
        0.5, 0.9,  # Posição do título no eixo (x, y)
        "Usage of HTTP Security Headers (Desktop vs Mobile)",
        fontsize=16,
        fontweight="bold",
        ha="center"
    )
    # Ajustar espaçamento
    #plt.tight_layout(rect=[0, 0, 1, 0.95])
    fig.subplots_adjust(top=0.75)
    plt.show()

# Simulated data for radar chart
# headers = list(config["expected_headers"].keys())
# num_headers = len(headers)
#
# # Simulate data for Desktop and Mobile usage (percentage)
# desktop_usage = np.random.uniform(50, 100, num_headers)  # Example percentages for desktop
# mobile_usage = np.random.uniform(30, 90, num_headers)  # Example percentages for mobile
#
# # Radar chart setup
# angles = np.linspace(0, 2 * np.pi, num_headers, endpoint=False).tolist()
# angles += angles[:1]  # Close the circle
#
# desktop_usage = np.append(desktop_usage, desktop_usage[0])  # Close the circle
# mobile_usage = np.append(mobile_usage, mobile_usage[0])  # Close the circle

# # Headers to highlight
# highlight_positive = config["critical_headers"]
# highlight_deprecated = config["deprecated_headers"]
#
# # Create the figure and axis
# fig, ax = plt.subplots(figsize=(8, 8), subplot_kw={"projection": "polar"})
#
# # Plot data
# ax.plot(angles, desktop_usage, label="Desktop", linewidth=2)
# ax.fill(angles, desktop_usage, alpha=0.25)
#
# ax.plot(angles, mobile_usage, label="Mobile", linewidth=2, linestyle='--')
# ax.fill(angles, mobile_usage, alpha=0.25)
#
# # Add header labels to the chart
# ax.set_yticks([20, 40, 60, 80, 100])  # Custom percentage ticks
# ax.set_yticklabels(["20%", "40%", "60%", "80%", "100%"], fontsize=10)
# ax.set_xticks(angles[:-1])
# #ax.set_xticklabels(headers, fontsize=10, ha='center')
#
# # Customize header labels
# for i, angle in enumerate(angles[:-1]):  # Skip the last angle (circle closure)
#     header = headers[i]
#     if header in highlight_positive:
#         ax.text(angle, 110, header, color="green", fontsize=10, ha='center', va='center')
#     elif header in highlight_deprecated:
#         ax.text(angle, 110, header, color="red",  fontsize=10, ha='center', va='center')
#     else:
#         ax.text(angle, 105, header, fontsize=10, ha='center', va='center')
#
# # Remove os ticks dos ângulos (90°, 135°, etc.)
# #ax.set_thetagrids([], labels=[])
# ax.xaxis.set_tick_params(labelcolor='none')
# ax.grid(True)
# # Style adjustments
# ax.set_title("Usage of HTTP Security Headers (Desktop vs Mobile) in Germany", size=14, y=1.1)
# ax.legend(loc="upper right", bbox_to_anchor=(1.2, 1.1))
#
# # Show chart
# plt.tight_layout()
# plt.show()


create_radar_charts(kpi)