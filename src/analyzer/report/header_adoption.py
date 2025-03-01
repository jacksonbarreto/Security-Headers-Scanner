import os
import textwrap

import matplotlib.pyplot as plt
from matplotlib.patches import Polygon
from matplotlib.colors import Normalize
import matplotlib.cm as cm
from mpl_toolkits.axes_grid1 import make_axes_locatable

import numpy as np
import pandas as pd

from src.analyzer.report.setup import RESULT_FILE_PATH, TABLE_DIRECTORY, CHART_DIRECTORY, ROOT_DIRECTORY, \
    RESULT_PLATFORM_FILE_PATH
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


def get_stats(dataframe):
    expected_headers = [col.replace("_presence", "") for col in dataframe.columns if "_presence" in col]

    stats_by_nuts = dataframe.groupby(["country", "NUTS2_Label_2016"]).agg(
        total_schools=("ETER_ID", "count"),
        **{f"{header}_present": (f"{header}_presence", "sum") for header in expected_headers},
        **{f"{header}_strong": (f"{header}_config", lambda x: (x == "Strong").sum()) for header in expected_headers},
        **{f"{header}_weak": (f"{header}_config", lambda x: (x == "Weak").sum()) for header in expected_headers}
    ).reset_index()
    stats_by_nuts.rename(columns={"NUTS2_Label_2016": "nuts"}, inplace=True)
    stats_by_nuts["Category"] = None

    stats_by_nuts_category = dataframe.groupby(["country", "NUTS2_Label_2016", "Category"]).agg(
        total_schools=("ETER_ID", "count"),
        **{f"{header}_present": (f"{header}_presence", "sum") for header in expected_headers},
        **{f"{header}_strong": (f"{header}_config", lambda x: (x == "Strong").sum()) for header in expected_headers},
        **{f"{header}_weak": (f"{header}_config", lambda x: (x == "Weak").sum()) for header in expected_headers}
    ).reset_index()
    stats_by_nuts_category.rename(columns={"NUTS2_Label_2016": "nuts"}, inplace=True)

    stats_by_country = dataframe.groupby(["country"]).agg(
        total_schools=("ETER_ID", "count"),
        **{f"{header}_present": (f"{header}_presence", "sum") for header in expected_headers},
        **{f"{header}_strong": (f"{header}_config", lambda x: (x == "Strong").sum()) for header in expected_headers},
        **{f"{header}_weak": (f"{header}_config", lambda x: (x == "Weak").sum()) for header in expected_headers}
    ).reset_index()
    stats_by_country["nuts"] = None
    stats_by_country["Category"] = None
    stats_by_country["platform"] = None

    stats_by_country_category = dataframe.groupby(["country", "Category"]).agg(
        total_schools=("ETER_ID", "count"),
        **{f"{header}_present": (f"{header}_presence", "sum") for header in expected_headers},
        **{f"{header}_strong": (f"{header}_config", lambda x: (x == "Strong").sum()) for header in expected_headers},
        **{f"{header}_weak": (f"{header}_config", lambda x: (x == "Weak").sum()) for header in expected_headers}
    ).reset_index()
    stats_by_country_category["nuts"] = None

    stats_by_country_platform = dataframe.groupby(["country", "platform"]).agg(
        total_schools=("ETER_ID", "count"),
        **{f"{header}_present": (f"{header}_presence", "sum") for header in expected_headers},
        **{f"{header}_strong": (f"{header}_config", lambda x: (x == "Strong").sum()) for header in expected_headers},
        **{f"{header}_weak": (f"{header}_config", lambda x: (x == "Weak").sum()) for header in expected_headers}
    ).reset_index()
    stats_by_country_platform["nuts"] = None
    stats_by_country_platform["Category"] = None

    stats_by_country_category_platform = dataframe.groupby(["country", "Category", "platform"]).agg(
        total_schools=("ETER_ID", "count"),
        **{f"{header}_present": (f"{header}_presence", "sum") for header in expected_headers},
        **{f"{header}_strong": (f"{header}_config", lambda x: (x == "Strong").sum()) for header in expected_headers},
        **{f"{header}_weak": (f"{header}_config", lambda x: (x == "Weak").sum()) for header in expected_headers}
    ).reset_index()
    stats_by_country_category_platform["nuts"] = None

    for df in [stats_by_nuts, stats_by_nuts_category, stats_by_country_category, stats_by_country, stats_by_country_category_platform, stats_by_country_platform]:
        for header in expected_headers:
            df[f"{header}_present_percent"] = ((df[f"{header}_present"] / df["total_schools"]) * 100).fillna(0).replace(
                [np.inf, -np.inf], 0).round(2)
            df[f"{header}_strong_percent"] = ((df[f"{header}_strong"] / df[f"{header}_present"]) * 100).fillna(
                0).replace([np.inf, -np.inf], 0).round(2)
            df[f"{header}_weak_percent"] = ((df[f"{header}_weak"] / df[f"{header}_present"]) * 100).fillna(0).replace(
                [np.inf, -np.inf], 0).round(2)

    stats_by_nuts["level"] = "nuts"
    stats_by_nuts_category["level"] = "nuts_category"
    stats_by_country_category["level"] = "country_category"
    stats_by_country["level"] = "country"
    stats_by_country_category_platform["level"] = "country_category_platform"
    stats_by_country_platform["level"] = "country_platform"

    consolidated_stats = pd.concat(
        [stats_by_nuts, stats_by_nuts_category, stats_by_country_category, stats_by_country, stats_by_country_category_platform, stats_by_country_platform],
        axis=0,
        ignore_index=True
    )

    return consolidated_stats


def latex_header_table(dataframe, level, title, label, config_weak=False):
    expected_headers = list(config[EXPECTED_HEADERS_KEY].keys())
    expected_headers = [header.lower() for header in expected_headers]

    if level == "nuts":
        region = "nuts"
        rename_map = {
            "nuts": "NUTS2",
            **{f"{header}_present_percent": f"{header_short_names.get(header, header)["latex"]}" for header in
               expected_headers},
            **{f"{header}_weak_percent": f"{header_short_names.get(header, header)["latex"]} Weak" for header in
               expected_headers},
        }
    elif level == "nuts_category":
        region = "nuts"
        rename_map = {
            "nuts": "NUTS2",
            **{f"{header}_present_percent": f"{header_short_names.get(header, header)["latex"]}" for header in
               expected_headers},
            **{f"{header}_weak_percent": f"{header_short_names.get(header, header)["latex"]} Weak" for header in
               expected_headers},
        }
    elif level == "country":
        region = "country"
        rename_map = {
            "country": "Country",
            **{f"{header}_present_percent": f"{header_short_names.get(header, header)["latex"]}" for header in
               expected_headers},
            **{f"{header}_weak_percent": f"{header_short_names.get(header, header)["latex"]} Weak" for header in
               expected_headers},
        }
    else:
        raise ValueError("Invalid level. Use 'nuts' or 'country'.")

    if config_weak:
        columns_to_display = [region] + [f"{header}_weak_percent" for header in expected_headers]
    else:
        columns_to_display = [region] + [f"{header}_present_percent" for header in expected_headers]
    columns_to_remove = [col for col in columns_to_display if dataframe[col].sum() == 0]
    columns_to_display = [col for col in columns_to_display if col not in columns_to_remove]

    dataframe = dataframe[columns_to_display].rename(columns=rename_map)

    column_headers = " & ".join(f"\\rotatebox{{90}}{{\\makecell{{{col}}}}}" for col in dataframe.columns)

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


def generate_header_table(stats_dataframe):
    countries = stats_dataframe["country"].unique()
    critical_headers_presence = ["content-security-policy_present_percent", "strict-transport-security_present_percent"]
    critical_headers_weak = ["content-security-policy_weak_percent", "strict-transport-security_weak_percent"]
    print(f"Countries: {countries}")

    def save_table(table, path):
        with open(path, "w", encoding="utf-8") as tex_file:
            tex_file.write(table)

    for country in countries:
        filtered_df = stats_dataframe[
            (stats_dataframe["country"] == country) & (stats_dataframe["level"] == "nuts")].sort_values(
            by=critical_headers_presence, ascending=False)

        nuts2_table = latex_header_table(filtered_df, "nuts",
                                         f"Security Headers Adoption in {get_country(country)} by NUTS2 (\\%)",
                                         f"sh_adoption_{country.lower()}")
        save_table(nuts2_table, os.path.join(TABLE_DIRECTORY, f"sh_adoption_in_{country}_by_nuts2.tex"))
        filtered_df.sort_values(by=critical_headers_weak, ascending=True, inplace=True)
        nuts2_table = latex_header_table(filtered_df, "nuts",
                                         f"Security Headers Weak Configuration in {get_country(country)} by NUTS2 (\\%)",
                                         f"sh_weak_config_{country.lower()}",
                                         True)
        save_table(nuts2_table, os.path.join(TABLE_DIRECTORY, f"sh_weak_config_in_{country}_by_nuts2.tex"))

        for i, category in enumerate(["public", "private"]):
            filtered_df = stats_dataframe[
                (stats_dataframe["country"] == country) & (stats_dataframe["level"] == "nuts_category") & (
                        stats_dataframe["Category"] == category)].sort_values(by=critical_headers_presence,
                                                                              ascending=False)
            nuts2_table = latex_header_table(filtered_df, "nuts",
                                             f"Security Headers Adoption at {category.capitalize()} HEIs in {get_country(country)} by NUTS2 (\\%)",
                                             f"sh_adoption_{country.lower()}_{category}")
            save_table(nuts2_table, os.path.join(TABLE_DIRECTORY, f"sh_adoption_in_{country}_by_nuts2_{category}.tex"))
            filtered_df.sort_values(by=critical_headers_weak, ascending=True, inplace=True)
            nuts2_table = latex_header_table(filtered_df, "nuts",
                                             f"Security Headers Weak Configuration at {category.capitalize()} HEIs in {get_country(country)} by NUTS2 (\\%)",
                                             f"sh_weak_config_{country.lower()}_{category}",
                                             True)
            save_table(nuts2_table,
                       os.path.join(TABLE_DIRECTORY, f"sh_weak_config_in_{country}_by_nuts2_{category}.tex"))

    filtered_df = stats_dataframe[stats_dataframe["level"] == "country"].sort_values(by=critical_headers_presence,
                                                                                     ascending=False)
    country_table = latex_header_table(filtered_df, "country",
                                       "Security Headers Adoption by Country (\\%)", "sh_adoption_country")
    save_table(country_table, os.path.join(TABLE_DIRECTORY, "sh_adoption_by_country.tex"))
    filtered_df.sort_values(by=critical_headers_weak, ascending=True, inplace=True)
    country_table = latex_header_table(filtered_df, "country",
                                       "Security Headers Weak Configuration by Country (\\%)", "sh_weak_config_country",
                                       True)
    save_table(country_table, os.path.join(TABLE_DIRECTORY, "sh_weak_config_by_country.tex"))


def plot_heat_map(dataframe, level, title):
    expected_headers = list(config[EXPECTED_HEADERS_KEY].keys())
    expected_headers = [header.lower() for header in expected_headers]
    if level == "nuts":
        y_column = "nuts"
    elif level == "country":
        y_column = "country"
    else:
        raise ValueError("Invalid level. Use 'nuts' or 'country'.")
    presence_columns = [f"{header}_present_percent" for header in expected_headers]
    presence_columns = [col for col in presence_columns if dataframe[col].sum() > 0]
    weak_columns = [f"{header}_weak_percent" for header in expected_headers]
    dataframe = dataframe[[y_column] + presence_columns + weak_columns].set_index(y_column)

    fig, ax = plt.subplots(figsize=(11, max(len(dataframe), 6) * 0.5))

    num_y = len(dataframe)
    num_x = len(presence_columns)
    norm_blue = Normalize(vmin=0, vmax=100)
    norm_red = Normalize(vmin=0, vmax=100)
    cmap_blue = cm.Blues
    cmap_red = cm.Reds

    def get_text_color(rgb_color):
        r, g, b, _ = rgb_color  # Pegamos o valor RGB ignorando o alpha
        brightness = (0.299 * r + 0.587 * g + 0.114 * b) * 255  # Calculamos o brilho
        return "white" if brightness < 128 else "black"

    for i in range(num_y):
        for j in range(num_x):
            adoption_value = dataframe.iloc[i, j]
            weak_value = dataframe.iloc[i, j + num_x]

            #x, y = j, num_y - i - 1  # Coordenadas invertidas para alinhar ao eixo Y corretamente
            x, y = j, i

            # Triângulo Superior (Adoção - Azul)
            color_top = cmap_blue(norm_blue(adoption_value))
            triangle_top = [[x, y + 1], [x + 1, y + 1], [x + 1, y]]
            ax.add_patch(Polygon(triangle_top, closed=True, color=color_top, alpha=0.8))

            # Triângulo Inferior (Configuração Fraca - Vermelho)
            color_bottom = cmap_red(norm_red(weak_value))
            triangle_bottom = [[x, y + 1], [x, y], [x + 1, y]]
            ax.add_patch(Polygon(triangle_bottom, closed=True, color=color_bottom, alpha=0.8))



            text_color_top = get_text_color(color_top)
            text_color_bottom = get_text_color(color_bottom)

            # Texto dentro da célula
            af = "-" if adoption_value == 0 else f"{adoption_value:.0f}"
            wv = "-" if weak_value == 0 else f"{weak_value:.0f}"
            ax.text(x + 0.5, y + 0.75, f"{af}", ha="center", va="center", fontsize=8, color=text_color_top)
            ax.text(x + 0.5, y + 0.25, f"{wv}", ha="center", va="center", fontsize=8, color=text_color_bottom)

    # Ajuste dos eixos e labels
    ax.set_title(title, fontsize=16, pad=20, y=1)
    filtered_headers = [header for header in expected_headers if f"{header}_present_percent" in dataframe.columns]
    ax.set_xticks(np.arange(len(filtered_headers)) + 0.5)

    ax.set_xticklabels([header_short_names.get(header, header)["normal"] for header in filtered_headers], rotation=45,
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
        filtered_df = dataframe[(dataframe["country"] == country) & (dataframe["level"] == "nuts")]
        fig = plot_heat_map(filtered_df, "nuts",
                            f"Security Headers Adoption and Weak Config in {get_country(country)} by NUTS2 (%)"
                            )
        file_name = f"sh_adoption_weak_by_nuts2_in_{country}.pdf"
        path_to_save = os.path.join(CHART_DIRECTORY, file_name)
        fig.savefig(path_to_save, format="pdf", bbox_inches="tight")
        plt.show()
        plt.close(fig)
    filtered_df = dataframe[dataframe["level"] == "country"]
    fig = plot_heat_map(filtered_df, "country", "Security Headers Adoption and Weak Config by Country (%)")
    file_name = "sh_adoption_weak_by_country.pdf"
    path_to_save = os.path.join(CHART_DIRECTORY, file_name)
    fig.savefig(path_to_save, format="pdf", bbox_inches="tight")
    plt.show()
    plt.close(fig)



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
    headers = list(config["expected_headers"].keys())

    num_headers = len(headers)
    angles = np.linspace(0, 2 * np.pi, num_headers, endpoint=False).tolist()
    angles.append(angles[0])

    countries = kpi_data["country"].unique()

    for country in countries:
        country_data = kpi_data[(kpi_data["country"] == country) & (kpi_data["level"] == "country_category_platform")]

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
            f"Adoption of HTTP Security Headers (Desktop vs Mobile) in {get_country(country)} by Category",
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

        country_data = kpi_data[(kpi_data["country"] == country) & (kpi_data["level"] == "country_platform")]
        available_cols = [col for col in country_data.columns if col.endswith("_present_percent")]
        if len(available_cols) == 0:
            continue
        num_vars = len(available_cols)
        angles = np.linspace(0, 2 * np.pi, num_vars, endpoint=False).tolist()
        angles.append(angles[0])
        data_cols = [col for col in country_data.columns if col.endswith("_present_percent")]
        desktop_usage = country_data[country_data["platform"] == "desktop"][available_cols].values.flatten()
        mobile_usage = country_data[country_data["platform"] == "mobile"][available_cols].values.flatten()
        if desktop_usage.size == 0 or mobile_usage.size == 0:
            continue
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
    stats = get_stats(df)
    pd.set_option('display.max_columns', None)
    pd.set_option('display.width', None)


    generate_header_table(stats)
    generate_heatmap(stats)
    df_platform = pd.read_csv(RESULT_PLATFORM_FILE_PATH)
    stats_platform = get_stats(df_platform)
    print(stats_platform.head())
    print(stats_platform[stats_platform["level"] == "country"].tail(20))
    create_radar_charts(stats_platform)


if __name__ == "__main__":
    make_header_adoption()
