"""
PISA Scores Across Time and Countries
-------------------------------------
A minimalistic interactive Streamlit app to explore OECD PISA scores
by country, domain, student group and year.

Run locally with:
    python -m streamlit run app.py

Requirements: streamlit, pandas, plotly
"""

import os
import glob

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

# --------------------------------------------------------------------------- #
# Page configuration
# --------------------------------------------------------------------------- #
st.set_page_config(
    page_title="PISA Scores Across Time and Countries",
    layout="wide",
)

# --------------------------------------------------------------------------- #
# Label mappings
# --------------------------------------------------------------------------- #
DOMAIN_LABELS = {
    "PISAMATH": "Mathematics",
    "PISAREAD": "Reading",
    "PISASCIENCE": "Science",
}

GROUP_LABELS = {
    "BOY": "Male",
    "GIRL": "Female",
    "TOT": "Total",
}

COUNTRY_LABELS = {
    "CHE": "Switzerland",
    "DEU": "Germany",
    "AUT": "Austria",
    "FIN": "Finland",
    "USA": "United States",
    "CAN": "Canada",
    "JPN": "Japan",
    "KOR": "Korea",
    "SGP": "Singapore",
    "GBR": "United Kingdom",
    "FRA": "France",
    "ITA": "Italy",
    "ESP": "Spain",
    "NLD": "Netherlands",
    "BEL": "Belgium",
    "SWE": "Sweden",
    "NOR": "Norway",
    "DNK": "Denmark",
    "AUS": "Australia",
    "NZL": "New Zealand",
    "OECD": "OECD average",
    "OAVG": "OECD average",
    "BRA": "Brazil",
    "CHL": "Chile",
    "COL": "Colombia",
    "CRI": "Costa Rica",
    "CZE": "Czechia",
    "EST": "Estonia",
    "GRC": "Greece",
    "HKG": "Hong Kong",
    "HUN": "Hungary",
    "IDN": "Indonesia",
    "IRL": "Ireland",
    "ISL": "Iceland",
    "ISR": "Israel",
    "LTU": "Lithuania",
    "LUX": "Luxembourg",
    "LVA": "Latvia",
    "MAC": "Macao",
    "MEX": "Mexico",
    "PER": "Peru",
    "POL": "Poland",
    "PRT": "Portugal",
    "RUS": "Russia",
    "SVK": "Slovakia",
    "SVN": "Slovenia",
    "TUR": "Turkey",
    "TWN": "Chinese Taipei",
}

DOMAIN_ORDER = ["Mathematics", "Reading", "Science"]

THEME_COLOR = "#104862"

GROUP_COLORS = {
    "Total": "#000000",
    "Male": "#1B4F9C",
    "Female": "#E85A9E",
}

AXIS_COLOR = "#B5BEC4"

CSV_CANDIDATES = ["OECD PISA data.csv", "OECD_PISA_data.csv"]

# --------------------------------------------------------------------------- #
# Custom UI styling
# --------------------------------------------------------------------------- #
st.markdown(
    f"""
    <style>
    :root {{
        --primary-color: {THEME_COLOR};
    }}

    button[kind="primary"] {{
        background-color: {THEME_COLOR};
        border-color: {THEME_COLOR};
    }}

    span[data-baseweb="tag"] {{
        background-color: {THEME_COLOR}22;
        color: {THEME_COLOR};
        border-color: {THEME_COLOR};
    }}

    a {{
        color: {THEME_COLOR};
    }}
    </style>
    """,
    unsafe_allow_html=True,
)


# --------------------------------------------------------------------------- #
# Data loading & preparation
# --------------------------------------------------------------------------- #
def _find_csv_path():
    """Return the first existing CSV file from the known candidates."""
    here = os.path.dirname(os.path.abspath(__file__))

    for name in CSV_CANDIDATES:
        candidate = os.path.join(here, name)
        if os.path.exists(candidate):
            return candidate

    matches = glob.glob(os.path.join(here, "*PISA*.csv"))
    return matches[0] if matches else None


@st.cache_data
def load_data():
    """Load and clean the PISA dataset, returning a tidy DataFrame."""
    path = _find_csv_path()

    if path is None:
        return None

    df = pd.read_csv(path)

    required = ["LOCATION", "INDICATOR", "SUBJECT", "TIME", "Value"]
    missing = [c for c in required if c not in df.columns]

    if missing:
        return None

    df = df[required].copy()

    df["TIME"] = pd.to_numeric(df["TIME"], errors="coerce")
    df["Value"] = pd.to_numeric(df["Value"], errors="coerce")

    df = df.dropna(subset=["LOCATION", "INDICATOR", "SUBJECT", "TIME", "Value"])

    df["TIME"] = df["TIME"].astype(int)

    df["Country"] = df["LOCATION"].map(COUNTRY_LABELS).fillna(df["LOCATION"])
    df["Domain"] = df["INDICATOR"].map(DOMAIN_LABELS).fillna(df["INDICATOR"])
    df["Group"] = df["SUBJECT"].map(GROUP_LABELS).fillna(df["SUBJECT"])

    df = df.sort_values("TIME").reset_index(drop=True)

    return df


def pick_default(options, preferred):
    """Return the first preferred option that exists, else the first option."""
    for p in preferred:
        if p in options:
            return p

    return options[0] if options else None


def style_axes(fig):
    """Remove gridlines and add subtle axis lines."""
    fig.update_xaxes(
        showgrid=False,
        zeroline=False,
        showline=True,
        linecolor=AXIS_COLOR,
        linewidth=1,
        ticks="outside",
        tickcolor=AXIS_COLOR,
    )

    fig.update_yaxes(
        showgrid=False,
        zeroline=False,
        showline=True,
        linecolor=AXIS_COLOR,
        linewidth=1,
        ticks="outside",
        tickcolor=AXIS_COLOR,
    )

    fig.update_layout(
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
    )

    return fig


# --------------------------------------------------------------------------- #
# Header
# --------------------------------------------------------------------------- #
st.title("PISA Scores Across Time and Countries")

st.write(
    "Explore OECD PISA scores through two interactive views: a stratified country "
    "overview and a ranked country comparison. The controls filter the data and "
    "change the visualization directly, going beyond hover and zoom. "
    "The default view uses Total to reduce cognitive load; Male and Female can be added for comparison."
)

st.caption(
    "Data source: Kaggle – PISA Performance Scores by Country, based on OECD PISA "
    "performance scores for reading, mathematics and science across countries, 2000–2018."
)

data = load_data()

if data is None or data.empty:
    st.error(
        "Could not load the dataset. Please make sure the CSV file "
        "(`OECD PISA data.csv` or `OECD_PISA_data.csv`) is in the same folder "
        "as `app.py`."
    )
    st.stop()

# --------------------------------------------------------------------------- #
# Divider and view selection
# --------------------------------------------------------------------------- #
st.divider()

VIEWS = ["Country overview", "Country comparison"]

if hasattr(st, "segmented_control"):
    view = st.segmented_control(
        "View",
        VIEWS,
        default="Country overview",
        label_visibility="collapsed",
    )

    if view is None:
        view = "Country overview"
else:
    view = st.radio(
        "View",
        VIEWS,
        index=0,
        horizontal=True,
        label_visibility="collapsed",
    )


# =========================================================================== #
# VIEW 1: COUNTRY OVERVIEW
# =========================================================================== #
def render_country_overview(df):
    countries = sorted(df["Country"].unique())
    default_country = pick_default(countries, ["Switzerland"])

    c1, c2 = st.columns([1.2, 1.8])

    with c1:
        country = st.selectbox(
            "Country",
            countries,
            index=countries.index(default_country),
        )

    country_df = df[df["Country"] == country]

    group_options = sorted(country_df["Group"].unique())
    default_group = pick_default(group_options, ["Total", "Male"])

    with c2:
        groups = st.multiselect(
            "Student groups",
            group_options,
            default=[default_group] if default_group else [],
            help="Add Male, Female or Total to compare lines.",
        )

    if not groups:
        st.warning("Please select at least one student group to display the chart.")
        return

    plot_df = country_df[country_df["Group"].isin(groups)].copy()

    if plot_df.empty:
        st.warning("No data available for the current selection.")
        return

    domains_present = [d for d in DOMAIN_ORDER if d in plot_df["Domain"].unique()]

    fig = px.line(
        plot_df,
        x="TIME",
        y="Value",
        color="Group",
        facet_col="Domain",
        markers=True,
        category_orders={
            "Domain": domains_present,
            "Group": ["Total", "Male", "Female"],
        },
        color_discrete_map=GROUP_COLORS,
        labels={
            "TIME": "Year",
            "Value": "PISA score",
            "Group": "Student group",
        },
        title=f"PISA scores in {country} over time",
    )

    fig.for_each_annotation(lambda a: a.update(text=a.text.split("=")[-1]))

    y_min = max(0, int(((df["Value"].min() - 10) // 10) * 10))
    y_max = int(((df["Value"].max() + 10) // 10 + 1) * 10)

    visible_years = sorted(plot_df["TIME"].unique())

    fig.update_xaxes(
        title_text="",
        tickmode="array",
        tickvals=visible_years,
        ticktext=[str(year) for year in visible_years],
        showticklabels=True,
    )

    if len(domains_present) >= 3:
        fig.update_xaxes(title_text="Year", col=2)
    else:
        fig.update_xaxes(title_text="Year", col=1)

    fig.update_yaxes(
        matches="y",
        range=[y_min, y_max],
        showticklabels=False,
        title_text="",
    )

    fig.update_yaxes(
        title_text="PISA score",
        showticklabels=True,
        col=1,
    )

    for col in range(2, len(domains_present) + 1):
        fig.update_yaxes(
            title_text="",
            showticklabels=False,
            col=col,
        )

    fig.update_layout(
        margin=dict(t=70, b=40),
        legend_title_text="Student group",
    )

    style_axes(fig)

    st.plotly_chart(fig, use_container_width=True)


# =========================================================================== #
# VIEW 2: COUNTRY COMPARISON
# =========================================================================== #
def render_country_comparison(df):
    domains = [d for d in DOMAIN_ORDER if d in df["Domain"].unique()]
    default_domain = pick_default(domains, ["Mathematics"])

    c1, c2, c3 = st.columns(3)

    with c1:
        domain = st.selectbox(
            "PISA domain",
            domains,
            index=domains.index(default_domain),
        )

    group_options = sorted(df["Group"].unique())
    default_group = pick_default(group_options, ["Total", "Male"])

    with c2:
        group = st.selectbox(
            "Student group",
            group_options,
            index=group_options.index(default_group),
        )

    scope = df[(df["Domain"] == domain) & (df["Group"] == group)].copy()
    years = sorted(scope["TIME"].unique())

    with c3:
        if not years:
            st.warning("No data available for this domain and group combination.")
            return

        if len(years) == 1:
            year = years[0]
            st.caption(f"Year: {year} (only one year available)")
        else:
            year = st.select_slider(
                "Year",
                options=years,
                value=years[-1],
            )

    # Countries come from the full dataset, not from the selected domain/year.
    # This keeps selected countries stable when domain, group or year changes.
    all_countries = sorted(df["Country"].unique())

    preferred = [
        "Switzerland",
        "Germany",
        "Austria",
        "Finland",
        "United States",
    ]

    default_countries = [c for c in preferred if c in all_countries]

    if not default_countries:
        default_countries = all_countries[:8]

    countries = st.multiselect(
        "Countries",
        all_countries,
        default=default_countries,
        key="comparison_countries",
    )

    if not countries:
        st.warning("Please select at least one country to display the chart.")
        return

    plot_df = scope[
        (scope["TIME"] == year)
        & (scope["Country"].isin(countries))
    ].copy()

    if plot_df.empty:
        st.warning(
            "No data available for the selected countries in this year, domain and group. "
            "Try another year, domain, group or select different countries."
        )
        return

    missing_countries = sorted(set(countries) - set(plot_df["Country"].unique()))

    if missing_countries:
        st.info(
            "Some selected countries have no data for this selection and are not shown: "
            + ", ".join(missing_countries)
        )

    plot_df = plot_df.sort_values("Value", ascending=True)

    point_color = GROUP_COLORS.get(group, THEME_COLOR)

    x_base = max(0, int((plot_df["Value"].min() // 10) * 10) - 10)
    x_max = int(((plot_df["Value"].max() + 10) // 10 + 1) * 10)

    chart_height = max(420, 34 * len(plot_df) + 140)

    fig = go.Figure()

    for _, row in plot_df.iterrows():
        fig.add_trace(
            go.Scatter(
                x=[x_base, row["Value"]],
                y=[row["Country"], row["Country"]],
                mode="lines",
                line=dict(color=AXIS_COLOR, width=2),
                hoverinfo="skip",
                showlegend=False,
            )
        )

    fig.add_trace(
        go.Scatter(
            x=plot_df["Value"],
            y=plot_df["Country"],
            mode="markers+text",
            marker=dict(
                size=11,
                color=point_color,
            ),
            text=[f"{v:.0f}" for v in plot_df["Value"]],
            textposition="middle right",
            textfont=dict(size=12),
            customdata=plot_df[["Domain", "Group", "TIME"]],
            hovertemplate=(
                "<b>%{y}</b><br>"
                "PISA score: %{x:.0f}<br>"
                "Domain: %{customdata[0]}<br>"
                "Group: %{customdata[1]}<br>"
                "Year: %{customdata[2]}"
                "<extra></extra>"
            ),
            showlegend=False,
        )
    )

    fig.update_layout(
        title=f"Country comparison: {domain}, {group}, {year}",
        margin=dict(t=70, b=40, l=90, r=40),
        height=chart_height,
        xaxis_title="PISA score",
        yaxis_title="Country",
    )

    fig.update_xaxes(range=[x_base, x_max])

    style_axes(fig)

    st.plotly_chart(fig, use_container_width=True)

    highest = plot_df.loc[plot_df["Value"].idxmax()]
    lowest = plot_df.loc[plot_df["Value"].idxmin()]
    difference_percent = ((highest["Value"] - lowest["Value"]) / lowest["Value"]) * 100

    m1, m2, m3 = st.columns(3)

    with m1:
        st.markdown(
            f"""
            <div style="text-align: center;">
                <div style="font-size: 0.9rem; color: #6B7280;">Highest score</div>
                <div style="font-size: 2rem; font-weight: 600;">{highest['Value']:.0f}</div>
                <div style="font-size: 0.95rem;">{highest['Country']}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with m2:
        st.markdown(
            f"""
            <div style="text-align: center;">
                <div style="font-size: 0.9rem; color: #6B7280;">Lowest score</div>
                <div style="font-size: 2rem; font-weight: 600;">{lowest['Value']:.0f}</div>
                <div style="font-size: 0.95rem;">{lowest['Country']}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with m3:
        st.markdown(
            f"""
            <div style="text-align: center;">
                <div style="font-size: 0.9rem; color: #6B7280;">Difference</div>
                <div style="font-size: 2rem; font-weight: 600;">{difference_percent:.1f}%</div>
                <div style="font-size: 0.95rem;">Relative to lowest score</div>
            </div>
            """,
            unsafe_allow_html=True,
        )


# --------------------------------------------------------------------------- #
# Render selected view
# --------------------------------------------------------------------------- #
if view == "Country overview":
    render_country_overview(data)
else:
    render_country_comparison(data)
