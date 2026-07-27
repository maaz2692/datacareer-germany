from pathlib import Path

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

st.set_page_config(
    page_title="DataCareer Germany",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

ROOT = Path(__file__).resolve().parent
DATA_PATH = ROOT / "data" / "processed" / "germany_state_snapshot_2022_scored.csv"

CATEGORY_LABELS = {
    "career_strength_score": "Career strength",
    "affordability_score": "Affordability",
    "income_economic_score": "Income and economy",
    "digital_readiness_score": "Digital readiness",
    "regional_momentum_score": "Regional momentum",
}

SCENARIO_WEIGHTS = {
    "Balanced": {
        "career_strength_score": 0.35,
        "affordability_score": 0.25,
        "income_economic_score": 0.20,
        "digital_readiness_score": 0.10,
        "regional_momentum_score": 0.10,
    },
    "Career first": {
        "career_strength_score": 0.55,
        "affordability_score": 0.10,
        "income_economic_score": 0.15,
        "digital_readiness_score": 0.10,
        "regional_momentum_score": 0.10,
    },
    "Affordability first": {
        "career_strength_score": 0.15,
        "affordability_score": 0.55,
        "income_economic_score": 0.10,
        "digital_readiness_score": 0.10,
        "regional_momentum_score": 0.10,
    },
    "Income first": {
        "career_strength_score": 0.15,
        "affordability_score": 0.10,
        "income_economic_score": 0.55,
        "digital_readiness_score": 0.10,
        "regional_momentum_score": 0.10,
    },
    "Growth first": {
        "career_strength_score": 0.15,
        "affordability_score": 0.10,
        "income_economic_score": 0.10,
        "digital_readiness_score": 0.10,
        "regional_momentum_score": 0.55,
    },
}

REQUIRED_COLUMNS = [
    "state_name",
    "population",
    "unemployment_rate",
    "employment_rate",
    "expert_level_employment",
    "it_science_service_employment",
    "median_income_academic",
    "asking_rent",
    "gdp_per_capita_eur",
    "broadband_100mbit",
    "population_change_10_years",
    "total_migration_balance",
    "rent_burden_50sqm_pct",
    "income_after_rent_50sqm",
    *CATEGORY_LABELS.keys(),
]

st.markdown(
    """
    <style>
    .block-container {max-width: 1450px; padding-top: 1.7rem;}
    [data-testid="stSidebar"] {border-right: 1px solid #E5E7EB;}
    .kicker {color:#0072B2; font-weight:700; letter-spacing:.08em;
             text-transform:uppercase; font-size:.8rem;}
    .subtitle {color:#5F6B7A; max-width:950px; margin-bottom:1rem;}
    .insight {background:#F7F9FB; border-left:4px solid #0072B2;
              padding:.8rem 1rem; border-radius:.4rem; margin:.5rem 0 1rem;}
    </style>
    """,
    unsafe_allow_html=True,
)


@st.cache_data
def load_data(path: Path) -> pd.DataFrame:
    if not path.exists():
        raise FileNotFoundError(f"Dataset not found: {path}")

    frame = pd.read_csv(path)
    missing = [column for column in REQUIRED_COLUMNS if column not in frame.columns]

    if missing:
        raise ValueError("Missing dashboard columns: " + ", ".join(missing))

    if frame["state_name"].nunique() != 16:
        raise ValueError("Expected exactly 16 German federal states.")

    return frame


try:
    base_data = load_data(DATA_PATH)
except (FileNotFoundError, ValueError) as error:
    st.error("The dashboard dataset is unavailable or incomplete.")
    st.code(str(error))
    st.info(
        "Export analysis_snapshot as "
        "data/processed/germany_state_snapshot_2022_scored.csv, "
        "then restart Streamlit."
    )
    st.stop()


st.sidebar.title("Decision settings")

profile_name = st.sidebar.selectbox(
    "Priority profile",
    [
        "Balanced",
        "Career first",
        "Affordability first",
        "Income first",
        "Growth first",
        "Custom",
    ],
)

state_options = sorted(base_data["state_name"].tolist())
focus_state = st.sidebar.selectbox(
    "Focus state",
    state_options,
    index=state_options.index("Berlin"),
)

if profile_name == "Custom":
    st.sidebar.caption("Weights are automatically normalised to 100%.")
    raw_weights = {
        "career_strength_score": st.sidebar.slider("Career strength", 0, 100, 35, 5),
        "affordability_score": st.sidebar.slider("Affordability", 0, 100, 25, 5),
        "income_economic_score": st.sidebar.slider("Income and economy", 0, 100, 20, 5),
        "digital_readiness_score": st.sidebar.slider("Digital readiness", 0, 100, 10, 5),
        "regional_momentum_score": st.sidebar.slider("Regional momentum", 0, 100, 10, 5),
    }
    raw_total = sum(raw_weights.values())
    if raw_total == 0:
        st.sidebar.error("At least one category must have a positive value.")
        st.stop()
    active_weights = {key: value / raw_total for key, value in raw_weights.items()}
else:
    active_weights = SCENARIO_WEIGHTS[profile_name]

with st.sidebar.expander("Current weights"):
    for column, weight in active_weights.items():
        st.write(f"**{CATEGORY_LABELS[column]}:** {weight:.0%}")

st.sidebar.divider()
st.sidebar.caption("Complete 2022 state snapshot · Source: INKAR 2025")


dashboard_data = base_data.copy()
dashboard_data["dashboard_score"] = sum(
    dashboard_data[column] * weight
    for column, weight in active_weights.items()
)
dashboard_data["dashboard_rank"] = (
    dashboard_data["dashboard_score"]
    .rank(ascending=False, method="min")
    .astype(int)
)
dashboard_data = dashboard_data.sort_values(
    ["dashboard_score", "career_strength_score", "state_name"],
    ascending=[False, False, True],
).reset_index(drop=True)

focus_row = dashboard_data.loc[
    dashboard_data["state_name"] == focus_state
].iloc[0]
leaders = dashboard_data.loc[dashboard_data["dashboard_rank"] == 1]
leader_names = " and ".join(leaders["state_name"].tolist())

strongest_column = max(CATEGORY_LABELS, key=lambda column: focus_row[column])
weakest_column = min(CATEGORY_LABELS, key=lambda column: focus_row[column])

st.markdown('<div class="kicker">Interactive regional career decision support</div>', unsafe_allow_html=True)
st.title("DataCareer Germany")
st.markdown(
    '<div class="subtitle">Compare Germany’s 16 federal states across career strength, '
    'affordability, income and economic performance, digital readiness, and regional momentum.</div>',
    unsafe_allow_html=True,
)

kpi1, kpi2, kpi3, kpi4 = st.columns(4)
kpi1.metric("Current leader", leader_names)
kpi2.metric(f"{focus_state} rank", f"#{int(focus_row['dashboard_rank'])} of 16")
kpi3.metric(f"{focus_state} score", f"{focus_row['dashboard_score']:.1f}")
kpi4.metric("Decision profile", profile_name)

st.markdown(
    f'<div class="insight">Under the <strong>{profile_name}</strong> profile, '
    f'<strong>{leader_names}</strong> lead. {focus_state} is strongest in '
    f'<strong>{CATEGORY_LABELS[strongest_column]}</strong> and weakest in '
    f'<strong>{CATEGORY_LABELS[weakest_column]}</strong>.</div>',
    unsafe_allow_html=True,
)

overview_tab, compare_tab, tradeoff_tab, methodology_tab = st.tabs(
    ["Overview", "Compare states", "Trade-offs", "Methodology"]
)

with overview_tab:
    left, right = st.columns([1.65, 1], gap="large")

    with left:
        st.subheader("Opportunity ranking")
        ranking = dashboard_data.sort_values("dashboard_score").copy()
        ranking["colour"] = np.select(
            [
                ranking["state_name"] == focus_state,
                ranking["dashboard_rank"] == 1,
            ],
            ["#D55E00", "#0072B2"],
            default="#C4CBD4",
        )

        fig_rank = go.Figure(
            go.Bar(
                x=ranking["dashboard_score"],
                y=ranking["state_name"],
                orientation="h",
                marker_color=ranking["colour"],
                text=ranking["dashboard_score"].map(lambda value: f"{value:.1f}"),
                textposition="outside",
                cliponaxis=False,
                customdata=ranking[
                    [
                        "dashboard_rank",
                        "career_strength_score",
                        "affordability_score",
                        "income_economic_score",
                        "digital_readiness_score",
                        "regional_momentum_score",
                    ]
                ],
                hovertemplate=(
                    "<b>%{y}</b><br>Rank: %{customdata[0]}<br>"
                    "Opportunity score: %{x:.1f}<br>Career: %{customdata[1]:.1f}<br>"
                    "Affordability: %{customdata[2]:.1f}<br>"
                    "Income and economy: %{customdata[3]:.1f}<br>"
                    "Digital: %{customdata[4]:.1f}<br>"
                    "Momentum: %{customdata[5]:.1f}<extra></extra>"
                ),
            )
        )
        fig_rank.update_layout(
            height=620,
            margin=dict(l=10, r=45, t=20, b=40),
            paper_bgcolor="white",
            plot_bgcolor="white",
            xaxis_title="Weighted opportunity score",
            yaxis_title="",
            showlegend=False,
        )
        fig_rank.update_xaxes(range=[0, ranking["dashboard_score"].max() + 8], showgrid=False)
        fig_rank.update_yaxes(showgrid=False)
        st.plotly_chart(fig_rank, width="stretch", config={"displayModeBar": False})
        st.caption("Blue marks the leader; orange marks the selected focus state.")

    with right:
        st.subheader(f"{focus_state} profile")
        profile = pd.DataFrame(
            {
                "Category": [CATEGORY_LABELS[column] for column in CATEGORY_LABELS],
                "Score": [focus_row[column] for column in CATEGORY_LABELS],
            }
        ).sort_values("Score")
        profile["colour"] = np.where(
            profile["Category"] == CATEGORY_LABELS[strongest_column],
            "#0072B2",
            "#C4CBD4",
        )

        fig_profile = go.Figure(
            go.Bar(
                x=profile["Score"],
                y=profile["Category"],
                orientation="h",
                marker_color=profile["colour"],
                text=profile["Score"].map(lambda value: f"{value:.1f}"),
                textposition="outside",
                cliponaxis=False,
                hovertemplate="<b>%{y}</b><br>Score: %{x:.1f}<extra></extra>",
            )
        )
        fig_profile.update_layout(
            height=360,
            margin=dict(l=10, r=40, t=10, b=35),
            paper_bgcolor="white",
            plot_bgcolor="white",
            xaxis_title="Relative score",
            yaxis_title="",
            showlegend=False,
        )
        fig_profile.update_xaxes(range=[0, 108], showgrid=False)
        fig_profile.update_yaxes(showgrid=False)
        st.plotly_chart(fig_profile, width="stretch", config={"displayModeBar": False})

        indicators = pd.DataFrame(
            {
                "Indicator": [
                    "Unemployment rate",
                    "IT/science employment",
                    "Academic median income",
                    "Asking rent",
                    "100 Mbit/s broadband",
                    "10-year population change",
                ],
                "Value": [
                    f"{focus_row['unemployment_rate']:.2f}%",
                    f"{focus_row['it_science_service_employment']:.2f}%",
                    f"€{focus_row['median_income_academic']:,.0f}/month",
                    f"€{focus_row['asking_rent']:.0f}/m²",
                    f"{focus_row['broadband_100mbit']:.2f}%",
                    f"{focus_row['population_change_10_years']:+.2f}%",
                ],
            }
        )
        st.dataframe(indicators, width="stretch", hide_index=True)

    st.subheader("Current top five")
    top_five = dashboard_data.head(5)[
        [
            "dashboard_rank",
            "state_name",
            "dashboard_score",
            "career_strength_score",
            "affordability_score",
            "income_economic_score",
            "digital_readiness_score",
            "regional_momentum_score",
        ]
    ].copy()
    top_five.columns = [
        "Rank",
        "State",
        "Opportunity score",
        "Career",
        "Affordability",
        "Income and economy",
        "Digital",
        "Momentum",
    ]
    for column in top_five.columns[2:]:
        top_five[column] = top_five[column].round(1)
    st.dataframe(top_five, width="stretch", hide_index=True)

    ranking_csv = dashboard_data[
        ["dashboard_rank", "state_name", "dashboard_score", *CATEGORY_LABELS.keys()]
    ].to_csv(index=False).encode("utf-8")
    st.download_button(
        "Download current ranking as CSV",
        ranking_csv,
        file_name=f"datacareer_{profile_name.lower().replace(' ', '_')}_ranking.csv",
        mime="text/csv",
    )

with compare_tab:
    st.subheader("Compare state profiles")
    defaults = []
    for state in [focus_state, leaders.iloc[0]["state_name"], "Berlin", "Bayern"]:
        if state not in defaults:
            defaults.append(state)

    selected_states = st.multiselect(
        "Select between two and five states",
        state_options,
        default=defaults[:4],
    )

    if len(selected_states) < 2:
        st.info("Select at least two states.")
    elif len(selected_states) > 5:
        st.warning("Select no more than five states for a readable comparison.")
    else:
        comparison = dashboard_data.loc[
            dashboard_data["state_name"].isin(selected_states)
        ].copy()
        comparison_long = comparison.melt(
            id_vars="state_name",
            value_vars=list(CATEGORY_LABELS.keys()),
            var_name="category",
            value_name="score",
        )
        comparison_long["category_label"] = comparison_long["category"].map(CATEGORY_LABELS)

        fig_compare = px.bar(
            comparison_long,
            x="category_label",
            y="score",
            color="state_name",
            barmode="group",
            labels={"category_label": "", "score": "Relative score", "state_name": "State"},
            category_orders={"category_label": list(CATEGORY_LABELS.values())},
        )
        fig_compare.update_layout(
            height=540,
            margin=dict(l=20, r=20, t=25, b=55),
            paper_bgcolor="white",
            plot_bgcolor="white",
            legend=dict(orientation="h", y=1.02, x=0),
        )
        fig_compare.update_xaxes(showgrid=False, tickangle=-12)
        fig_compare.update_yaxes(range=[0, 105], gridcolor="#EEF1F4")
        st.plotly_chart(fig_compare, width="stretch", config={"displayModeBar": False})

        compare_table = comparison[
            [
                "dashboard_rank",
                "state_name",
                "dashboard_score",
                "unemployment_rate",
                "median_income_academic",
                "asking_rent",
                "rent_burden_50sqm_pct",
                "broadband_100mbit",
                "population_change_10_years",
            ]
        ].copy()
        compare_table.columns = [
            "Rank",
            "State",
            "Score",
            "Unemployment %",
            "Academic income €/month",
            "Asking rent €/m²",
            "Illustrative rent burden %",
            "Broadband %",
            "10-year population change %",
        ]
        st.dataframe(compare_table.round(2), width="stretch", hide_index=True)

with tradeoff_tab:
    st.subheader("Income and housing-cost trade-off")
    tradeoff = dashboard_data.copy()
    tradeoff["label"] = np.where(tradeoff["state_name"] == focus_state, focus_state, "")

    fig_tradeoff = px.scatter(
        tradeoff,
        x="asking_rent",
        y="median_income_academic",
        size="population",
        color="dashboard_score",
        text="label",
        hover_name="state_name",
        hover_data={
            "population": ":,.0f",
            "rent_burden_50sqm_pct": ":.2f",
            "income_after_rent_50sqm": ":,.0f",
            "dashboard_score": ":.1f",
            "label": False,
        },
        color_continuous_scale="Cividis",
        labels={
            "asking_rent": "Asking rent (€ per m²)",
            "median_income_academic": "Median monthly academic income (€)",
            "dashboard_score": "Opportunity score",
            "rent_burden_50sqm_pct": "Illustrative rent burden (%)",
            "income_after_rent_50sqm": "Gross income after illustrative rent (€)",
        },
    )
    fig_tradeoff.update_traces(textposition="top center", marker=dict(line=dict(color="white", width=1.2)))
    fig_tradeoff.add_vline(x=tradeoff["asking_rent"].median(), line_dash="dot", line_color="#9CA3AF")
    fig_tradeoff.add_hline(y=tradeoff["median_income_academic"].median(), line_dash="dot", line_color="#9CA3AF")
    fig_tradeoff.update_layout(
        height=610,
        margin=dict(l=20, r=20, t=20, b=55),
        paper_bgcolor="white",
        plot_bgcolor="white",
    )
    fig_tradeoff.update_xaxes(showgrid=False)
    fig_tradeoff.update_yaxes(gridcolor="#EEF1F4", tickprefix="€", tickformat=",.0f")
    st.plotly_chart(fig_tradeoff, width="stretch", config={"displayModeBar": False})
    st.caption("Bubble size represents population. Dotted lines show the state medians.")

    table_left, table_right = st.columns(2)
    with table_left:
        st.markdown("#### Strongest affordability positions")
        affordable = dashboard_data.nsmallest(5, "rent_burden_50sqm_pct")[[
            "state_name", "rent_burden_50sqm_pct", "asking_rent", "median_income_academic"
        ]].copy()
        affordable.columns = ["State", "Rent burden %", "Rent €/m²", "Academic income €/month"]
        st.dataframe(affordable.round(2), width="stretch", hide_index=True)

    with table_right:
        st.markdown("#### Strongest career markets")
        careers = dashboard_data.nlargest(5, "career_strength_score")[[
            "state_name", "career_strength_score", "unemployment_rate", "it_science_service_employment"
        ]].copy()
        careers.columns = ["State", "Career score", "Unemployment %", "IT/science employment %"]
        st.dataframe(careers.round(2), width="stretch", hide_index=True)

with methodology_tab:
    st.subheader("How the opportunity score works")
    st.markdown(
        """
        Indicators are converted into percentile scores across Germany’s 16 states.
        Higher values receive stronger scores for positive indicators such as employment,
        income, broadband and growth. Lower values receive stronger scores for unemployment,
        asking rent and illustrative rent burden.
        """
    )

    weights_table = pd.DataFrame(
        {
            "Category": [CATEGORY_LABELS[column] for column in active_weights],
            "Weight": [f"{active_weights[column]:.0%}" for column in active_weights],
        }
    )
    st.dataframe(weights_table, width="stretch", hide_index=True)
    st.code("Opportunity score = Σ(category score × selected category weight)", language=None)

    st.markdown("#### Important limitations")
    st.markdown(
        """
        - State-level analysis does not capture differences between cities within a state.
        - Academic median income is a broad proxy, not a salary measure specifically for data roles.
        - The 50 m² rent calculation excludes taxes, utilities and household-specific costs.
        - Scenario weights are analytical assumptions rather than official standards.
        - Scores are relative to the 16 states and are not absolute quality ratings.
        """
    )

    with st.expander("View processed dashboard data"):
        st.dataframe(dashboard_data, width="stretch", hide_index=True)

st.divider()
st.caption(
    "DataCareer Germany · INKAR 2025 · Main comparison year: 2022 · "
    "Built with Python, Pandas, Plotly and Streamlit"
)