import os
import textwrap

import matplotlib.pyplot as plt
from matplotlib.patches import Polygon
from matplotlib.colors import Normalize
import matplotlib.cm as cm
from mpl_toolkits.axes_grid1 import make_axes_locatable

import numpy as np
import pandas as pd

from src.analyzer.report.setup import RESULT_FILE_PATH, TABLE_DIRECTORY, CHART_DIRECTORY, ROOT_DIRECTORY
from src.config import config, EXPECTED_HEADERS_KEY

header_short_names = {
    "strict-transport-security": {
        "latex": "\\gls{hsts}",
        "normal": "HSTS"
    },
    "x-xss-protection": {
        "latex": "XXP",
        "normal": "XXP"
    },
    "x-frame-options": {
        "latex": "\\gls{xfo}",
        "normal": "XFO"
    },
    "x-content-type-options": {
        "latex": "XCTO",
        "normal": "XCTO"
    },
    "referrer-policy": {
        "latex": "RP",
        "normal": "RP"
    },
    "cross-origin-opener-policy": {
        "latex": "\\gls{coop}",
        "normal": "COOP"
    },
    "cross-origin-embedder-policy": {
        "latex": "\\gls{coep}",
        "normal": "COEP"
    },
    "cross-origin-resource-policy": {
        "latex": "\\gls{corp}",
        "normal": "CORP"
    },
    "access-control-allow-origin": {
        "latex": "\\gls{cors}",
        "normal": "CORS"
    },
    "content-security-policy": {
        "latex": "\\gls{csp}",
        "normal": "CSP"
    },
    "set-cookie": {
        "latex": "SC",
        "normal": "SC"
    }
}


def prepare_header_adoption_stats(dataframe):
    expected_headers = [col.replace("_presence", "") for col in dataframe.columns if "_presence" in col]

    stats_by_nuts = dataframe.groupby(["country", "NUTS2_Label_2016"]).agg(
        total_schools_nuts=("ETER_ID", "count"),
        **{f"{header}_present_nuts": (f"{header}_presence", "sum") for header in expected_headers},
        **{f"{header}_strong_nuts": ((f"{header}_config", lambda x: (x == "Strong").sum())) for header in
           expected_headers},
        **{f"{header}_weak_nuts": ((f"{header}_config", lambda x: (x == "Weak").sum())) for header in expected_headers},
        **{f"{header}_missing_nuts": ((f"{header}_config", lambda x: (x == "Missing").sum())) for header in
           expected_headers},
    ).reset_index()

    stats_by_country = dataframe.groupby("country").agg(
        total_schools_country=("ETER_ID", "count"),
        **{f"{header}_present_country": (f"{header}_presence", "sum") for header in expected_headers},
        **{f"{header}_strong_country": ((f"{header}_config", lambda x: (x == "Strong").sum())) for header in
           expected_headers},
        **{f"{header}_weak_country": ((f"{header}_config", lambda x: (x == "Weak").sum())) for header in
           expected_headers},
        **{f"{header}_missing_country": ((f"{header}_config", lambda x: (x == "Missing").sum())) for header in
           expected_headers},
    ).reset_index()

    for header in expected_headers:
        stats_by_nuts[f"{header}_present_percent_nuts"] = (
                stats_by_nuts[f"{header}_present_nuts"] / stats_by_nuts["total_schools_nuts"] * 100
        ).round(2)

        stats_by_country[f"{header}_present_percent_country"] = (
                stats_by_country[f"{header}_present_country"] / stats_by_country["total_schools_country"] * 100
        ).round(2)

        stats_by_nuts[f"{header}_strong_percent_nuts"] = (
                                                                 stats_by_nuts[f"{header}_strong_nuts"] / stats_by_nuts[
                                                             f"{header}_present_nuts"]
                                                         ).fillna(0).replace([np.inf, -np.inf], 0) * 100

        stats_by_nuts[f"{header}_weak_percent_nuts"] = (
                                                               stats_by_nuts[f"{header}_weak_nuts"] / stats_by_nuts[
                                                           f"{header}_present_nuts"]
                                                       ).fillna(0).replace([np.inf, -np.inf], 0) * 100

        stats_by_country[f"{header}_strong_percent_country"] = (
                                                                       stats_by_country[f"{header}_strong_country"] /
                                                                       stats_by_country[f"{header}_present_country"]
                                                               ).fillna(0).replace([np.inf, -np.inf], 0) * 100

        stats_by_country[f"{header}_weak_percent_country"] = (
                                                                     stats_by_country[f"{header}_weak_country"] /
                                                                     stats_by_country[f"{header}_present_country"]
                                                             ).fillna(0).replace([np.inf, -np.inf], 0) * 100

        stats_by_nuts[f"{header}_missing_percent_nuts"] = (
                stats_by_nuts[f"{header}_missing_nuts"] / stats_by_nuts["total_schools_nuts"] * 100
        ).round(2)

        stats_by_country[f"{header}_missing_percent_country"] = (
                stats_by_country[f"{header}_missing_country"] / stats_by_country["total_schools_country"] * 100
        ).round(2)

    stats_by_nuts.rename(columns={"NUTS2_Label_2016": "nuts"}, inplace=True)

    consolidated_stats = stats_by_nuts.merge(
        stats_by_country,
        on="country",
        how="left",
        suffixes=("_nuts", "_country")
    )

    return consolidated_stats


def latex_header_table(dataframe, level, title, label, config_weak=False):
    expected_headers = list(config[EXPECTED_HEADERS_KEY].keys())
    expected_headers = [header.lower() for header in expected_headers]

    if level == "nuts":
        if config_weak:
            columns_to_display = ["nuts"] + [f"{header}_weak_percent_nuts" for header in expected_headers]
        else:
            columns_to_display = ["nuts"] + [f"{header}_present_percent_nuts" for header in expected_headers]
        rename_map = {
            "nuts": "NUTS2",
            **{f"{header}_present_percent_nuts": f"{header_short_names.get(header, header)["latex"]}" for header in
               expected_headers},
            **{f"{header}_weak_percent_nuts": f"{header_short_names.get(header, header)["latex"]} Weak" for header in
               expected_headers},
        }
    elif level == "country":
        if config_weak:
            columns_to_display = ["country"] + [f"{header}_weak_percent_country" for header in expected_headers]
        else:
            columns_to_display = ["country"] + [f"{header}_present_percent_country" for header in expected_headers]

        rename_map = {
            "country": "Country",
            **{f"{header}_present_percent_country": f"{header_short_names.get(header, header)["latex"]}" for header in
               expected_headers},
            **{f"{header}_weak_percent_country": f"{header_short_names.get(header, header)["latex"]} Weak" for header in
               expected_headers},
        }
    else:
        raise ValueError("Invalid level. Use 'nuts' or 'country'.")

    dataframe = dataframe[columns_to_display].rename(columns=rename_map)

    column_headers = " & ".join(f"\\rotatebox{{90}}{{\\makecell{{{col}}}}}" for col in dataframe.columns)

    table_rows = "\n".join(
        f"            {row[0]} & " + " & ".join(
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


def generate_header_table(stats_dataframe):
    countries = stats_dataframe["country"].unique()
    print(f"Countries: {countries}")

    for country in countries:
        filtered_df = stats_dataframe[stats_dataframe["country"] == country]
        nuts2_table = latex_header_table(filtered_df, "nuts",
                                         f"Security Headers Adoption in {get_country(country)} by NUTS2 (\\%)",
                                         f"sh_adoption_{country.lower()}")

        path_to_save = os.path.join(TABLE_DIRECTORY, f"sh_adoption_in_{country}_by_nuts2.tex")
        with open(path_to_save, "w", encoding="utf-8") as tex_file:
            tex_file.write(nuts2_table)
        nuts2_table = latex_header_table(filtered_df, "nuts",
                                         f"Security Headers Weak Configuration in {get_country(country)} by NUTS2 (\\%)",
                                         f"sh_weak_config_{country.lower()}",
                                         True)
        path_to_save = os.path.join(TABLE_DIRECTORY, f"sh_weak_config_in_{country}_by_nuts2.tex")
        with open(path_to_save, "w", encoding="utf-8") as tex_file:
            tex_file.write(nuts2_table)
    country_table = latex_header_table(stats_dataframe, "country",
                                       "Security Headers Adoption by Country (\\%)", "sh_adoption_country")
    path_to_save = os.path.join(TABLE_DIRECTORY, "sh_adoption_by_country.tex")
    with open(path_to_save, "w", encoding="utf-8") as tex_file:
        tex_file.write(country_table)
    country_table = latex_header_table(stats_dataframe, "country",
                                       "Security Headers Weak Configuration by Country (\\%)", "sh_adoption_country",
                                       True)
    path_to_save = os.path.join(TABLE_DIRECTORY, "sh_weak_config_by_country.tex")
    with open(path_to_save, "w", encoding="utf-8") as tex_file:
        tex_file.write(country_table)


def plot_heat_map(dataframe, level, title, country_filter=None):
    expected_headers = list(config[EXPECTED_HEADERS_KEY].keys())
    expected_headers = [header.lower() for header in expected_headers]
    if level == "nuts":
        if country_filter:
            dataframe = dataframe[dataframe["country"] == country_filter]
        y_column = "nuts"
        presence_columns = [f"{header}_present_percent_nuts" for header in expected_headers]
        weak_columns = [f"{header}_weak_percent_nuts" for header in expected_headers]
    elif level == "country":
        dataframe = dataframe.drop_duplicates(subset=["country"])
        y_column = "country"
        presence_columns = [f"{header}_present_percent_country" for header in expected_headers]
        weak_columns = [f"{header}_weak_percent_country" for header in expected_headers]
    else:
        raise ValueError("Invalid level. Use 'nuts' or 'country'.")

    dataframe = dataframe[[y_column] + presence_columns + weak_columns].set_index(y_column)

    fig, ax = plt.subplots(figsize=(19, max(len(dataframe), 5) * 0.6))

    num_y = len(dataframe)
    num_x = len(expected_headers)
    norm_blue = Normalize(vmin=0, vmax=100)
    norm_red = Normalize(vmin=0, vmax=100)
    cmap_blue = cm.Blues
    cmap_red = cm.Reds

    for i in range(num_y):
        for j in range(num_x):
            adoption_value = dataframe.iloc[i, j]
            weak_value = dataframe.iloc[i, j + num_x]

            x, y = j, num_y - i - 1  # Coordenadas invertidas para alinhar ao eixo Y corretamente

            # Triângulo Superior (Adoção - Azul)
            triangle_top = [[x, y + 1], [x + 1, y + 1], [x + 1, y]]
            ax.add_patch(Polygon(triangle_top, closed=True, color=cmap_blue(norm_blue(adoption_value)), alpha=0.8))

            # Triângulo Inferior (Configuração Fraca - Vermelho)
            triangle_bottom = [[x, y + 1], [x, y], [x + 1, y]]
            ax.add_patch(Polygon(triangle_bottom, closed=True, color=cmap_red(norm_red(weak_value)), alpha=0.8))

            # Texto dentro da célula
            af = "-" if adoption_value == 0 else f"{adoption_value:.0f}"
            wv = "-" if weak_value == 0 else f"{weak_value:.0f}"
            ax.text(x + 0.5, y + 0.75, f"{af}", ha="center", va="center", fontsize=10, color="black")
            ax.text(x + 0.5, y + 0.25, f"{wv}", ha="center", va="center", fontsize=10, color="black")

    # Ajuste dos eixos e labels
    ax.set_title(title, fontsize=16, pad=20, y=1)
    ax.set_xticks(np.arange(num_x) + 0.5)
    ax.set_xticklabels([header_short_names.get(header, header)["normal"] for header in expected_headers], rotation=45,
                       ha="right")
    ax.set_yticks(np.arange(num_y) + 0.5)

    def wrap_labels(labels, width=15):
        return ['\n'.join(textwrap.wrap(label, width)) for label in labels]

    ax.set_yticklabels(wrap_labels(dataframe.index if level == "nuts" else dataframe.index.map(get_country)))

    ax.set_xlim(0, num_x)
    ax.set_ylim(0, num_y)
    plt.subplots_adjust(right=0.99)
    divider = make_axes_locatable(ax)

    cbar_ax1 = divider.append_axes("right", size="2%", pad=0.08)  # Barra da adoção
    cbar_ax2 = divider.append_axes("right", size="2%", pad=0.6)  # Barra da fraqueza

    cbar1 = plt.colorbar(cm.ScalarMappable(norm=norm_blue, cmap=cmap_blue), cax=cbar_ax1)
    cbar2 = plt.colorbar(cm.ScalarMappable(norm=norm_red, cmap=cmap_red), cax=cbar_ax2)

    cbar1.set_label("Adoption (%)", fontsize=9)
    cbar2.set_label("Weak Config. (%)", fontsize=9)

    ax.set_xlabel("Security Headers", fontsize=12)
    ax.set_ylabel("NUTS2" if level == "nuts" else "Country", fontsize=12)

    plt.tight_layout()
    return fig


def generate_heatmap(dataframe):
    total_countries = dataframe["country"].unique()
    for country in total_countries:
        fig = plot_heat_map(dataframe, "nuts",
                            f"Security Headers Adoption and Weak Config in {get_country(country)} by NUTS2 (%)",
                            country)
        file_name = f"sh_adoption_weak_by_nuts2_in_{country}.pdf"
        path_to_save = os.path.join(CHART_DIRECTORY, file_name)
        fig.savefig(path_to_save, format="pdf", bbox_inches="tight")
        plt.show()
    fig = plot_heat_map(dataframe, "country", "Security Headers Adoption and Weak Config by Country (%)")
    file_name = "sh_adoption_weak_by_country.pdf"
    path_to_save = os.path.join(CHART_DIRECTORY, file_name)
    fig.savefig(path_to_save, format="pdf", bbox_inches="tight")
    plt.show()


def get_data(dataframe):
    expected_headers = list(config[EXPECTED_HEADERS_KEY].keys())
    expected_headers = [header.lower() for header in expected_headers]
    dataframe["country"] = dataframe["country"].apply(get_country)

    stats_by_platform_category = dataframe.groupby(["country", "platform", "Category"]).agg(
        total_schools=("ETER_ID", "count"),
        **{f"{header}_present": (f"{header}_presence", "sum") for header in expected_headers},
    ).reset_index()

    # Agora calcular as porcentagens de presença
    for header in expected_headers:
        stats_by_platform_category[f"{header}_present_percent"] = (
                                                                          stats_by_platform_category[
                                                                              f"{header}_present"] /
                                                                          stats_by_platform_category["total_schools"]
                                                                  ) * 100

    stats_by_platform = dataframe.groupby(["country", "platform"]).agg(
        total_schools=("ETER_ID", "count"),
        **{f"{header}_present": (f"{header}_presence", "sum") for header in expected_headers},
    ).reset_index()

    for header in expected_headers:
        stats_by_platform[f"{header}_present_percent"] = (
                                                                 stats_by_platform[f"{header}_present"] /
                                                                 stats_by_platform["total_schools"]
                                                         ) * 100

    stats_by_country = dataframe.groupby("country").agg(
        total_schools=("ETER_ID", "count"),
        **{f"{header}_present": (f"{header}_presence", "sum") for header in expected_headers},
    ).reset_index()

    for header in expected_headers:
        stats_by_country[f"{header}_present_percent"] = (
                                                                stats_by_country[f"{header}_present"] /
                                                                stats_by_country["total_schools"]
                                                        ) * 100

    stats_by_platform_category["level"] = "platform_category"
    stats_by_platform["level"] = "platform"
    stats_by_country["level"] = "country"

    consolidated_stats = pd.concat(
        [stats_by_platform_category, stats_by_platform, stats_by_country],
        ignore_index=True
    )

    return consolidated_stats


def get_country(country):
    if country == "de":
        return "Germany"
    elif country == "fr":
        return "France"
    elif country == "it":
        return "Italy"
    return country

def get_reverse_country(country):
    if country == "Germany":
        return "de"
    elif country == "France":
        return "fr"
    elif country == "Italy":
        return "it"
    return country

def create_radar_charts(kpi_data):
    highlight_positive = config["critical_headers"]
    highlight_deprecated = config["deprecated_headers"]
    headers = list(config["expected_headers"].keys())  # Garantir que a lista de headers esteja correta

    num_headers = len(headers)
    angles = np.linspace(0, 2 * np.pi, num_headers, endpoint=False).tolist()
    angles.append(angles[0])  # Fechar o gráfico radar

    countries = kpi_data["country"].unique()

    for country in countries:
        country_data = kpi_data[kpi_data["country"] == country]

        fig, axes = plt.subplots(1, 2, subplot_kw=dict(polar=True), figsize=(14, 7))

        categories = ["public", "private"]
        for i, category in enumerate(categories):
            ax = axes[i]
            category_data = country_data[country_data["Category"] == category]

            if category_data.empty:
                continue

            # Filtrar apenas os headers que queremos (sem total_schools)
            data_cols = [col for col in category_data.columns if col.endswith("_present_percent")]

            # Obter os valores para desktop e mobile
            desktop_usage = category_data[category_data["platform"] == "desktop"][data_cols].values.flatten()
            mobile_usage = category_data[category_data["platform"] == "mobile"][data_cols].values.flatten()

            # Fechar o círculo para radar chart
            desktop_usage = np.append(desktop_usage, desktop_usage[0])
            mobile_usage = np.append(mobile_usage, mobile_usage[0])

            # Plotar os dados
            ax.plot(angles, desktop_usage, label="Desktop", color="blue")
            ax.fill(angles, desktop_usage, color="blue", alpha=0.25)
            ax.plot(angles, mobile_usage, label="Mobile", color="orange", linestyle="--")
            ax.fill(angles, mobile_usage, color="orange", alpha=0.25)

            # Configuração dos labels
            ax.set_xticks(angles[:-1])
            ax.set_xticklabels(headers, fontsize=8)
            ax.set_yticks([20, 40, 60, 80, 100])
            ax.set_yticklabels(["20%", "40%", "60%", "80%", "100%"], fontsize=8)
            ax.set_title(f"{category.capitalize()} HEIs", fontsize=12, pad=15, y=1.05)

            # Destacar headers críticos e obsoletos
            for j, angle in enumerate(angles[:-1]):
                header = headers[j]
                if header in highlight_positive:
                    ax.text(angle, 110, header, color="green", fontsize=9, ha='center', va='center')
                elif header in highlight_deprecated:
                    ax.text(angle, 110, header, color="red", fontsize=9, ha='center', va='center')
                else:
                    ax.text(angle, 105, header, fontsize=9, ha='center', va='center')

            ax.xaxis.set_tick_params(labelcolor='none')
            ax.grid(True)
            ax.legend(loc="upper right", bbox_to_anchor=(1.2, 1.1))

        fig.text(
            0.5, 0.95,
            f"Adoption of HTTP Security Headers (Desktop vs Mobile) in {country} by Category",
            fontsize=16,
            fontweight="bold",
            ha="center"
        )
        plt.tight_layout()
        filename = os.path.join(CHART_DIRECTORY, f"sh_adoption_by_category_{get_reverse_country(country)}.pdf")
        fig.savefig(filename, format="pdf", bbox_inches="tight")
        plt.show()
        plt.close(fig)

    # Criar o gráfico vertical com todos os países
    fig, axes = plt.subplots(len(countries), 1, subplot_kw=dict(polar=True), figsize=(8, 4.5 * len(countries)))

    if len(countries) == 1:
        axes = [axes]

    for i, country in enumerate(countries):
        ax = axes[i]

        country_data = kpi_data[(kpi_data["country"] == country) & (kpi_data["level"] == "platform")]
        data_cols = [col for col in country_data.columns if col.endswith("_present_percent")]
        desktop_usage = country_data[country_data["platform"] == "desktop"][data_cols].values.flatten()
        mobile_usage = country_data[country_data["platform"] == "mobile"][data_cols].values.flatten()

        # Fechar o círculo para radar chart
        desktop_usage = np.append(desktop_usage, desktop_usage[0])
        mobile_usage = np.append(mobile_usage, mobile_usage[0])

        # Plotar os dados gerais
        ax.plot(angles, desktop_usage, label="Desktop", color="blue")
        ax.fill(angles, desktop_usage, color="blue", alpha=0.25)
        ax.plot(angles, mobile_usage, label="Mobile", color="orange", linestyle="--")
        ax.fill(angles, mobile_usage, color="orange", alpha=0.25)

        ax.set_xticks(angles[:-1])
        ax.set_xticklabels(headers, fontsize=8)
        ax.set_yticks([20, 40, 60, 80, 100])
        ax.set_yticklabels(["20%", "40%", "60%", "80%", "100%"], fontsize=8)
        ax.set_title(f"{get_country(country)} - Overall", fontsize=12, pad=10, y=1.05)

        for j, angle in enumerate(angles[:-1]):
            header = headers[j]

            if header in highlight_positive:
                ax.text(angle, 110, header, color="green", fontsize=9, ha='center', va='center')
            elif header in highlight_deprecated:
                ax.text(angle, 110, header, color="red", fontsize=9, ha='center', va='center')
            else:
                ax.text(angle, 105, header, fontsize=9, ha='center', va='center')
        ax.xaxis.set_tick_params(labelcolor='none')
        ax.grid(True)
        ax.legend(loc="upper right", bbox_to_anchor=(1.5, 1.1))

    fig.text(
        0.5, 0.98,
        "Adoption of HTTP Security Headers (Desktop vs Mobile)",
        fontsize=16,
        fontweight="bold",
        ha="center",
    )
    plt.tight_layout(rect=[0, 0, 1, 0.94])
    filename = os.path.join(CHART_DIRECTORY, "sh_adoption_by_platform_by_countries.pdf")
    fig.savefig(filename, format="pdf", bbox_inches="tight")
    plt.show()


def make_header_adoption():
    df = pd.read_csv(RESULT_FILE_PATH)
    stats = prepare_header_adoption_stats(df)
    pd.set_option('display.max_columns', None)
    pd.set_option('display.width', None)

    generate_header_table(stats)
    generate_heatmap(stats)

    df2 = pd.read_csv(
        os.path.join(ROOT_DIRECTORY, 'src', 'data', 'results', 'analysis', 'sh_final_result_with_scores.csv'))
    kpi = get_data(df2)
    create_radar_charts(kpi)


if __name__ == "__main__":
    make_header_adoption()
