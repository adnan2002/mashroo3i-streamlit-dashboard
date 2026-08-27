"""Mashroo3i applicants dashboard.

Converted from ``Dashboard_Mashroo3i.ipynb`` into a plain Python application.

Run locally::

    python app.py --no-ngrok

Run with an ngrok tunnel::

    python app.py          # needs NGROK_AUTHTOKEN in the environment or .env

Serve with a production WSGI server::

    gunicorn app:server
"""

from __future__ import annotations

import argparse
import base64
import io
import os
import sys
import time

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from dash import Dash, Input, Output, State, dcc, html


# ---------------------------------------------------------------------------
# Global application state
# ---------------------------------------------------------------------------

DF_GLOBAL = None

C_ORANGE = "#FF6B2E"
C_ORANGE_DARK = "#E6531F"
C_ORANGE_LIGHT = "#FF8C42"
C_YELLOW = "#FFC96B"
C_ORANGE_SOFT = "#FFB27A"
C_PEACH = "#FDDCC9"
C_PEACH_LIGHT = "#FFF4EE"
C_GRAY = "#D0D0D0"
C_TEXT = "#4B4038"
CHART_FONT = "'Inter', 'Segoe UI', system-ui, sans-serif"
COHORT_COLORS = {"Arabic": C_YELLOW, "English": C_ORANGE}
# A restrained orange palette that matches the dashboard's theme everywhere.
SECTOR_COLORS = [
    C_ORANGE_DARK,
    C_ORANGE,
    C_ORANGE_LIGHT,
    C_YELLOW,
    C_ORANGE_SOFT,
    "#C96F45",
]
AGE_ORDER = ["18-24", "25-34", "35-44", "45+", "Not Specified"]

# Columns the dashboard needs from an uploaded file (kept even if the source
# file contains many more columns).
REQUIRED_COLUMNS = [
    "year",
    "cohort",
    "Sector",
    "outcome_clean",
    "Business Stage",
    "Age Group",
    "applicant_type",
    "team_member_count",
    "employment_status",
    "has_commercial_registration",
    "education",
    "major",
    "nationality",
]

ATTENDANCE_COLUMNS = [
    "sessions_scheduled",
    "team_days_present",
    "team_days_virtual",
    "team_attendance_rate",
    "member_attendance_rate",
]
REQUIRED_COLUMNS.extend(ATTENDANCE_COLUMNS)

btn_w = {
    "background": "white",
    "color": "#4B4038",
    "border": f"1px solid {C_PEACH}",
    "borderRadius": "12px",
    "padding": "11px 12px",
    "fontWeight": "700",
    "cursor": "pointer",
    "fontSize": "12px",
    "textAlign": "left",
    "transition": "all .18s ease",
    "boxShadow": "0 1px 2px rgba(64, 41, 24, .04)",
}
btn_a = {
    "background": C_ORANGE,
    "color": "white",
    "border": "none",
    "borderRadius": "12px",
    "padding": "11px 12px",
    "fontWeight": "700",
    "cursor": "pointer",
    "fontSize": "12px",
    "textAlign": "left",
    "boxShadow": "0 8px 18px rgba(255, 107, 46, .22)",
}


def _clean_cohort(value):
    """Normalize cohort labels to 'Arabic' / 'English' when recognizable."""
    if pd.isna(value):
        return value
    text = str(value).strip().lower()
    if "arab" in text:
        return "Arabic"
    if "eng" in text:
        return "English"
    return str(value).strip()


def _clean_applicant_type(value):
    """Normalize applicant_type values to 'Individual' / 'Team'."""
    if pd.isna(value):
        return value
    text = str(value).strip().lower().replace("_", " ")
    if "solo" in text or "individual" in text or text == "ind":
        return "Individual"
    if "team" in text or "group" in text:
        return "Team"
    return str(value).strip().replace("_", " ").title()


def _attendance_pct(series):
    """Convert attendance rates to percentages (0-1 values become 0-100)."""
    values = pd.to_numeric(series, errors="coerce")
    if values.notna().any() and values.max() <= 1.0:
        values = values * 100
    return values


def _age_order(index):
    """Order age-group labels youngest-first, with unknown labels after."""
    known = [age for age in AGE_ORDER if age in index]
    unknown = sorted([age for age in index if age not in AGE_ORDER])
    return known + unknown


def build_layout():
    """Build the complete Dash layout."""
    return html.Div(
        className="app-shell",
        style={
            "fontFamily": "'Inter', 'Segoe UI', system-ui, -apple-system, sans-serif",
            "display": "flex",
            "minHeight": "100vh",
            "background": "#FBF6F2",
        },
        children=[
            html.Div(
                className="sidebar",
                style={
                    "background": "white",
                    "padding": "20px 16px",
                    "display": "flex",
                    "flexDirection": "column",
                    "gap": "8px",
                },
                children=[
                    html.Div(
                        "🏗️ Mashroo3i",
                        className="sidebar-brand",
                        style={
                            "color": C_ORANGE,
                            "fontSize": "22px",
                            "fontWeight": "800",
                            "letterSpacing": "-.3px",
                            "padding": "2px 4px 4px",
                        },
                    ),
                    html.Div(
                        "Applicant & cohort insights",
                        style={
                            "color": "#9B8B82",
                            "fontSize": "11px",
                            "fontWeight": "600",
                            "padding": "0 4px 10px",
                            "marginTop": "-7px",
                        },
                    ),
                    dcc.Upload(
                        id="upload-csv",
                        children=html.Div(
                            ["⬆️ Upload CSV"],
                            style={
                                "textAlign": "center",
                                "fontWeight": "800",
                                "fontSize": "13px",
                                "color": C_ORANGE_DARK,
                            },
                        ),
                        className="upload-zone",
                        style={
                            "width": "100%",
                            "height": "44px",
                            "lineHeight": "44px",
                            "borderWidth": "1.5px",
                            "borderStyle": "dashed",
                            "borderColor": "#F3B38F",
                            "borderRadius": "13px",
                            "background": C_PEACH_LIGHT,
                            "cursor": "pointer",
                        },
                        multiple=False,
                    ),
                    html.Div(id="upload-status"),
                    html.Hr(style={"margin": "10px 0 8px", "border": "0", "borderTop": f"1px solid {C_PEACH}"}),
                    html.Button("1 - Overview", id="btn-p1", n_clicks=0, style=btn_a),
                    html.Button("2 - Applicant Profile", id="btn-p2", n_clicks=0, style=btn_w),
                    html.Button("3 - Sectors & Applicant Type", id="btn-p3", n_clicks=0, style=btn_w),
                    html.Button("4 - Cohort Comparison", id="btn-p4", n_clicks=0, style=btn_w),
                    html.Button("5 - Attendance", id="btn-p5", n_clicks=0, style=btn_w),
                    html.Hr(style={"margin": "10px 0 8px", "border": "0", "borderTop": f"1px solid {C_PEACH}"}),
                    html.Div(
                        "Filters",
                        style={
                            "fontSize": "10px",
                            "fontWeight": "800",
                            "letterSpacing": "1.2px",
                            "textTransform": "uppercase",
                            "color": "#A18F86",
                            "padding": "2px 4px",
                        },
                    ),
                    dcc.Dropdown(id="f-year", options=[], multi=True, placeholder="All Years"),
                    dcc.Dropdown(id="f-cohort", options=[], multi=True, placeholder="All Cohorts"),
                    dcc.Dropdown(id="f-outcome", options=[], multi=True, placeholder="All Outcomes"),
                    dcc.Dropdown(id="f-sector", options=[], multi=True, placeholder="All Sectors"),
                    dcc.Dropdown(id="f-type", options=[], multi=True, placeholder="Individual or Team"),
                ],
            ),
            html.Div(
                className="main-area",
                style={
                    "flex": "1",
                    "minWidth": "0",
                    "background": "#FBF6F2",
                    "boxSizing": "border-box",
                    "display": "flex",
                    "flexDirection": "column",
                },
                children=[
                    dcc.Loading(
                        className="page-loader",
                        type="circle",
                        color=C_ORANGE,
                        style={"flex": "1", "minWidth": "0", "display": "flex", "flexDirection": "column"},
                        children=html.Div(
                            id="page-content",
                            className="page-content",
                            style={"width": "100%", "minWidth": "0"},
                        ),
                    )
                ],
            ),
            dcc.Store(id="current-page", data="page1"),
        ],
    )


app = Dash(__name__)
app.title = "Mashroo3i Dashboard"
app.layout = build_layout()
server = app.server


@app.callback(
    Output("current-page", "data"),
    Output("btn-p1", "style"),
    Output("btn-p2", "style"),
    Output("btn-p3", "style"),
    Output("btn-p4", "style"),
    Output("btn-p5", "style"),
    Input("btn-p1", "n_clicks"),
    Input("btn-p2", "n_clicks"),
    Input("btn-p3", "n_clicks"),
    Input("btn-p4", "n_clicks"),
    Input("btn-p5", "n_clicks"),
)
def switch_page(b1, b2, b3, b4, b5):
    from dash import ctx

    if not ctx.triggered:
        return "page1", btn_a, btn_w, btn_w, btn_w, btn_w
    pages = {
        "btn-p1": "page1",
        "btn-p2": "page2",
        "btn-p3": "page3",
        "btn-p4": "page4",
        "btn-p5": "page5",
    }
    page = pages.get(ctx.triggered_id, "page1")
    return (
        page,
        btn_a if page == "page1" else btn_w,
        btn_a if page == "page2" else btn_w,
        btn_a if page == "page3" else btn_w,
        btn_a if page == "page4" else btn_w,
        btn_a if page == "page5" else btn_w,
    )


@app.callback(
    Output("upload-status", "children"),
    Output("f-year", "options"),
    Output("f-cohort", "options"),
    Output("f-outcome", "options"),
    Output("f-sector", "options"),
    Output("f-type", "options"),
    Input("upload-csv", "contents"),
    State("upload-csv", "filename"),
)
def handle_upload(contents, filename):
    global DF_GLOBAL
    if contents is None:
        return "", [], [], [], [], []
    _, content_string = contents.split(",")
    decoded = base64.b64decode(content_string)
    if filename.lower().endswith(".csv"):
        df_up = pd.read_csv(io.BytesIO(decoded), encoding="utf-8-sig")
    else:
        df_up = pd.read_excel(io.BytesIO(decoded))
    keep = [c for c in REQUIRED_COLUMNS if c in df_up.columns]
    DF_GLOBAL = df_up[keep].copy()

    # Years must be integers, never floats.
    if "year" in DF_GLOBAL.columns:
        DF_GLOBAL["year"] = pd.to_numeric(DF_GLOBAL["year"], errors="coerce").astype("Int64")
    if "cohort" in DF_GLOBAL.columns:
        DF_GLOBAL["cohort"] = DF_GLOBAL["cohort"].map(_clean_cohort)
    if "applicant_type" in DF_GLOBAL.columns:
        DF_GLOBAL["applicant_type"] = DF_GLOBAL["applicant_type"].map(_clean_applicant_type)

    msg = html.Div(
        f"✅ {len(DF_GLOBAL)} rows",
        className="upload-status",
        style={
            "background": C_PEACH_LIGHT,
            "borderRadius": "10px",
            "padding": "8px 10px",
            "border": f"1px solid {C_PEACH}",
            "fontSize": "11px",
            "fontWeight": "700",
            "textAlign": "center",
            "color": C_ORANGE_DARK,
        },
    )
    year_opts = [
        {"label": str(int(y)), "value": int(y)}
        for y in sorted(DF_GLOBAL["year"].dropna().unique())
    ]
    cohort_opts = [
        {"label": str(c), "value": c} for c in DF_GLOBAL["cohort"].dropna().unique()
    ]
    outcome_opts = [
        {"label": str(o), "value": o} for o in DF_GLOBAL["outcome_clean"].dropna().unique()
    ]
    sector_opts = [
        {"label": str(s), "value": s} for s in DF_GLOBAL["Sector"].dropna().unique()
    ]
    type_opts = [
        {"label": str(t), "value": t} for t in DF_GLOBAL["applicant_type"].dropna().unique()
    ]
    return msg, year_opts, cohort_opts, outcome_opts, sector_opts, type_opts


def _bar_fig(x, y, orientation="v", text=None, color=C_ORANGE, radius=14):
    """Compact single-color bar chart that fills its container."""
    trace = {
        "marker": dict(color=color, cornerradius=radius),
    }
    if text is not None:
        trace["text"] = text
        trace["textposition"] = "outside"
        trace["cliponaxis"] = False
    fig = go.Figure(go.Bar(x=x, y=y, orientation=orientation, **trace))
    if orientation == "h":
        fig.update_layout(
            margin=dict(l=10, r=80, t=30, b=10),
            xaxis=dict(title="", visible=False),
            yaxis=dict(title="", showgrid=False, tickfont=dict(family=CHART_FONT, size=11, color=C_TEXT)),
        )
    else:
        fig.update_layout(
            margin=dict(l=10, r=60, t=32, b=10),
            xaxis=dict(title="", showgrid=False, tickfont=dict(family=CHART_FONT, size=11, color=C_TEXT)),
            yaxis=dict(title="", visible=False),
        )
    fig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(
            family=CHART_FONT,
            size=11,
            color=C_TEXT,
        ),
        hoverlabel=dict(
            bgcolor="white",
            bordercolor=C_PEACH,
            font=dict(family=CHART_FONT, size=11, color="#2D2926"),
        ),
        showlegend=False,
    )
    return fig


def _card(title, fig, flex="1"):
    """Modern card with a consistent chart height, so nothing gets clipped."""
    return html.Div(
        className="chart-card",
        style={
            "flex": flex,
            "minWidth": "0",
            "background": "white",
            "borderRadius": "16px",
            "border": f"1px solid {C_PEACH}",
            "boxShadow": "0 10px 24px rgba(99, 51, 18, .06)",
            "overflow": "hidden",
            "display": "flex",
            "flexDirection": "column",
        },
        children=[
            html.Div(
                title,
                className="chart-card-title",
                style={"flexShrink": "0"},
            ),
            html.Div(
                className="chart-card-body",
                style={"flex": "1", "minHeight": "0"},
                children=[
                    dcc.Graph(
                        figure=fig,
                        style={"height": "320px", "width": "100%"},
                        config={"displayModeBar": False},
                    )
                ],
            ),
        ],
    )


def _row(*cards):
    """One responsive chart row."""
    return html.Div(
        className="chart-row",
        style={"display": "flex", "gap": "16px", "minWidth": "0"},
        children=list(cards),
    )


def _page_shell(title, kpis, *rows):
    return [
        html.Div(
            className="page-heading",
            style={"padding": "0 2px 16px"},
            children=[
                html.Div(title, className="page-title"),
                html.Div(
                    "Live insights from the uploaded dataset",
                    className="page-subtitle",
                ),
            ],
        ),
        kpis,
        html.Div(
            className="chart-rows",
            style={
                "display": "flex",
                "flexDirection": "column",
                "gap": "16px",
                "minWidth": "0",
            },
            children=list(rows),
        ),
    ]


def _empty_state(icon, title, copy=None):
    """Shared empty state used before upload and when filters match nothing."""
    return html.Div(
        className="empty-state",
        children=[
            html.Div(icon, className="empty-icon"),
            html.Div(title, className="empty-title"),
            html.Div(copy or "", className="empty-copy") if copy else None,
        ],
    )


@app.callback(
    Output("page-content", "children"),
    Input("current-page", "data"),
    # Re-render immediately after an upload by watching the upload status.
    Input("upload-status", "children"),
    Input("f-year", "value"),
    Input("f-cohort", "value"),
    Input("f-outcome", "value"),
    Input("f-sector", "value"),
    Input("f-type", "value"),
)
def update_page(
    page,
    _upload_trigger,
    years,
    cohorts,
    outcomes,
    sectors,
    types,
    df_input=None,
):
    global DF_GLOBAL
    dff = DF_GLOBAL if df_input is None else df_input
    if dff is None:
        return [
            _empty_state(
                "📤",
                "Upload your dataset to get started",
                "Drop a CSV or Excel file into the upload area to unlock the dashboard.",
            )
        ]

    if years:
        dff = dff[dff["year"].isin(years)]
    if cohorts:
        dff = dff[dff["cohort"].isin(cohorts)]
    if outcomes:
        dff = dff[dff["outcome_clean"].isin(outcomes)]
    if sectors:
        dff = dff[dff["Sector"].isin(sectors)]
    if types:
        dff = dff[dff["applicant_type"].isin(types)]
    if len(dff) == 0:
        return [
            _empty_state(
                "🔍",
                "No data for this filter",
                "Try removing one or more filters to see matching applicant records.",
            )
        ]

    total = len(dff)
    accepted = len(dff[dff["outcome_clean"] == "Accepted"])
    rate = round(accepted / total * 100, 1) if total else 0
    bah_rate = (
        round(
            len(
                dff[dff["nationality"].astype(str).str.contains("bahrain", case=False, na=False)]
            )
            / total
            * 100,
            1,
        )
        if total
        else 0
    )

    kpis = html.Div(
        className="kpi-grid",
        children=[
            html.Div(
                className="kpi-card",
                style={"padding": "14px 16px", "display": "flex", "flexDirection": "column", "gap": "7px"},
                children=[
                    html.Div("👥", className="kpi-icon"),
                    html.Div(f"{total}", className="kpi-value"),
                    html.Div("Total Applicants", className="kpi-label"),
                ],
            ),
            html.Div(
                className="kpi-card",
                style={"padding": "14px 16px", "display": "flex", "flexDirection": "column", "gap": "7px"},
                children=[
                    html.Div("✅", className="kpi-icon"),
                    html.Div(f"{accepted}", className="kpi-value"),
                    html.Div("Accepted", className="kpi-label"),
                ],
            ),
            html.Div(
                className="kpi-card",
                style={"padding": "14px 16px", "display": "flex", "flexDirection": "column", "gap": "7px"},
                children=[
                    html.Div("📈", className="kpi-icon"),
                    html.Div(f"{rate}%", className="kpi-value"),
                    html.Div("Acceptance Rate", className="kpi-label"),
                ],
            ),
            html.Div(
                className="kpi-card",
                style={"padding": "14px 16px", "display": "flex", "flexDirection": "column", "gap": "7px"},
                children=[
                    html.Img(
                        src="https://flagcdn.com/w80/bh.png",
                        className="kpi-icon",
                        style={"width": "32px", "height": "21px", "borderRadius": "4px", "objectFit": "cover"},
                    ),
                    html.Div(f"{bah_rate}%", className="kpi-value"),
                    html.Div("Bahraini Nationals", className="kpi-label"),
                ],
            ),
        ],
    )

    if page == "page1":
        df_yc = dff.groupby(["year", "cohort"]).size().reset_index(name="Total")
        fig_y = px.bar(
            df_yc,
            x="year",
            y="Total",
            color="cohort",
            barmode="stack",
            color_discrete_map=COHORT_COLORS,
            text="Total",
            category_orders={"cohort": ["Arabic", "English"]},
        )
        fig_y.update_traces(marker=dict(cornerradius=12), textposition="outside", cliponaxis=False)
        fig_y.update_layout(
            margin=dict(l=10, r=40, t=40, b=10),
            legend_title_text="Cohort",
            legend=dict(orientation="h", y=1.2, x=0.5, xanchor="center", font=dict(family=CHART_FONT, size=10)),
            xaxis=dict(title="", showgrid=False, tickfont=dict(family=CHART_FONT, size=11, color=C_TEXT), tickformat="d"),
            yaxis=dict(title="", visible=False),
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            font=dict(family=CHART_FONT, size=11, color=C_TEXT),
        )

        acc_by_year = (
            dff[dff["outcome_clean"] == "Accepted"].groupby("year").size().reset_index(name="Accepted")
        )
        fig_acc = go.Figure(
            go.Scatter(
                x=acc_by_year["year"],
                y=acc_by_year["Accepted"],
                mode="lines+markers+text",
                text=acc_by_year["Accepted"],
                textposition="top center",
                line=dict(color=C_ORANGE, width=3),
                marker=dict(size=9, color=C_ORANGE),
            )
        )
        fig_acc.update_layout(
            margin=dict(l=10, r=30, t=35, b=10),
            xaxis=dict(title="", showgrid=False, tickfont=dict(family=CHART_FONT, size=11, color=C_TEXT), tickformat="d"),
            yaxis=dict(title="", showgrid=True, gridcolor="#F0E2D8", zeroline=False),
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            font=dict(family=CHART_FONT, size=11, color=C_TEXT),
        )

        cnt_type = dff["applicant_type"].value_counts().sort_values(ascending=False)
        fig_type = _bar_fig(cnt_type.index, cnt_type.values, text=cnt_type.values)

        cnt_nat = dff["nationality"].value_counts().head(5).sort_values()
        fig_nat = _bar_fig(
            cnt_nat.values, cnt_nat.index, orientation="h", text=cnt_nat.values
        )

        return _page_shell(
            "Overview",
            kpis,
            _row(
                _card("Applications by Year & Cohort", fig_y, flex="2"),
                _card("Accepted Applications Over Years", fig_acc),
            ),
            _row(
                _card("Applicant Type Breakdown", fig_type),
                _card("Top Nationalities", fig_nat),
            ),
        )

    elif page == "page2":
        cnt_stage = dff["Business Stage"].value_counts().sort_values(ascending=False)
        fig_stage = _bar_fig(cnt_stage.index, cnt_stage.values, text=cnt_stage.values)

        cnt_age = dff["Age Group"].value_counts().reindex(_age_order(dff["Age Group"].dropna().unique())).dropna()
        fig_age = _bar_fig(cnt_age.index, cnt_age.values, text=cnt_age.values)

        cnt_out = dff["outcome_clean"].value_counts().sort_values(ascending=False)
        fig_out = _bar_fig(cnt_out.index, cnt_out.values, text=cnt_out.values)

        cnt_cr = dff["has_commercial_registration"].value_counts().sort_values(ascending=False)
        fig_cr = _bar_fig(cnt_cr.index, cnt_cr.values, text=cnt_cr.values)

        cnt_emp = dff["employment_status"].value_counts().sort_values(ascending=False)
        fig_emp = _bar_fig(cnt_emp.index, cnt_emp.values, text=cnt_emp.values)

        cnt_edu = dff["education"].value_counts().sort_values().tail(6)
        fig_edu = _bar_fig(cnt_edu.values, cnt_edu.index, orientation="h", text=cnt_edu.values)

        cnt_major = dff["major"].value_counts().sort_values().tail(6)
        fig_major = _bar_fig(cnt_major.values, cnt_major.index, orientation="h", text=cnt_major.values)

        return _page_shell(
            "Applicant Profile",
            kpis,
            _row(
                _card("Business Stage", fig_stage),
                _card("Age Group", fig_age),
                _card("Outcome", fig_out),
            ),
            _row(
                _card("Commercial Registration", fig_cr),
                _card("Employment Status", fig_emp),
                _card("Education", fig_edu),
            ),
            _row(_card("Major", fig_major)),
        )

    elif page == "page3":
        df_type_out = dff.groupby(["applicant_type", "outcome_clean"]).size().reset_index(name="Total")
        fig_type_out = px.bar(
            df_type_out,
            y="applicant_type",
            x="Total",
            color="outcome_clean",
            orientation="h",
            barmode="stack",
            color_discrete_map={
                "Accepted": C_ORANGE_DARK,
                "Rejected": C_ORANGE_LIGHT,
                "Not Specified": C_GRAY,
            },
            text="Total",
        )
        fig_type_out.update_traces(marker=dict(cornerradius=14), textposition="inside")
        fig_type_out.update_layout(
            margin=dict(l=10, r=30, t=40, b=10),
            legend_title_text="Outcome",
            legend=dict(orientation="h", y=1.2, x=0.5, xanchor="center", font=dict(family=CHART_FONT, size=10)),
            xaxis=dict(title="", visible=False),
            yaxis=dict(title="", showgrid=False, tickfont=dict(family=CHART_FONT, size=11, color=C_TEXT)),
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            font=dict(family=CHART_FONT, size=11, color=C_TEXT),
        )

        cnt_sec = dff["Sector"].value_counts().sort_values().tail(5)
        fig_sec = _bar_fig(cnt_sec.values, cnt_sec.index, orientation="h", text=cnt_sec.values)

        cnt_y_type = dff.groupby(["year", "applicant_type"]).size().reset_index(name="Total")
        fig_y_type = px.bar(
            cnt_y_type,
            x="year",
            y="Total",
            color="applicant_type",
            barmode="group",
            color_discrete_map={"Individual": C_ORANGE_DARK, "Team": C_ORANGE_LIGHT},
            text="Total",
        )
        fig_y_type.update_traces(marker=dict(cornerradius=12), textposition="outside", cliponaxis=False)
        fig_y_type.update_layout(
            margin=dict(l=10, r=50, t=40, b=10),
            legend_title_text="Applicant Type",
            legend=dict(orientation="h", y=1.2, x=0.5, xanchor="center", font=dict(family=CHART_FONT, size=10)),
            xaxis=dict(title="", showgrid=False, tickfont=dict(family=CHART_FONT, size=11, color=C_TEXT), tickformat="d"),
            yaxis=dict(title="", visible=False),
            bargap=0.4,
            bargroupgap=0.25,
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            font=dict(family=CHART_FONT, size=11, color=C_TEXT),
        )

        sec_rate = (
            dff.groupby("Sector")["outcome_clean"]
            .apply(lambda values: (values == "Accepted").mean() * 100)
            .sort_values()
            .tail(6)
        )
        fig_sec_rate = _bar_fig(
            sec_rate.round(1).values,
            sec_rate.index,
            orientation="h",
            text=sec_rate.round(1).values.astype(str) + "%",
        )

        return _page_shell(
            "Sectors & Applicant Type",
            kpis,
            _row(
                _card("Applicant Type vs Outcome", fig_type_out, flex="2"),
                _card("Top Sectors", fig_sec),
            ),
            _row(
                _card("Applicant Type Over Years", fig_y_type),
                _card("Acceptance Rate by Sector", fig_sec_rate),
            ),
        )

    elif page == "page4":
        df_rate = (
            dff.groupby("cohort")["outcome_clean"]
            .value_counts(normalize=True)
            .unstack(fill_value=0)
            .reset_index()
        )
        df_rate["Acceptance Rate %"] = (
            (df_rate["Accepted"] * 100).round(1) if "Accepted" in df_rate.columns else 0
        )
        df_rate = df_rate.sort_values("Acceptance Rate %", ascending=False)
        fig_rate = _bar_fig(
            df_rate["cohort"],
            df_rate["Acceptance Rate %"],
            text=df_rate["Acceptance Rate %"].astype(str) + "%",
        )

        cnt_cohort = dff["cohort"].value_counts().sort_values()
        fig_cohort = _bar_fig(
            cnt_cohort.values, cnt_cohort.index, orientation="h", text=cnt_cohort.values
        )

        df_sec_cohort = (
            dff.groupby(["cohort", "Sector"])
            .size()
            .reset_index(name="Total")
            .sort_values("Total", ascending=False)
            .groupby("cohort")
            .head(3)
        )
        fig_sec_cohort = px.bar(
            df_sec_cohort,
            x="cohort",
            y="Total",
            color="Sector",
            barmode="group",
            text="Total",
            color_discrete_sequence=SECTOR_COLORS,
            category_orders={"cohort": ["Arabic", "English"]},
        )
        fig_sec_cohort.update_traces(marker=dict(cornerradius=10), textposition="outside", cliponaxis=False)
        fig_sec_cohort.update_layout(
            margin=dict(l=10, r=50, t=45, b=10),
            legend_title_text="Sector",
            bargap=0.4,
            bargroupgap=0.25,
            legend=dict(orientation="h", y=1.35, x=0.5, xanchor="center", font=dict(family=CHART_FONT, size=9)),
            xaxis=dict(title="", showgrid=False, tickfont=dict(family=CHART_FONT, size=11, color=C_TEXT)),
            yaxis=dict(title="", visible=False),
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            font=dict(family=CHART_FONT, size=11, color=C_TEXT),
        )

        df_type_cohort = dff.groupby(["cohort", "applicant_type"]).size().reset_index(name="Total")
        fig_type_cohort = px.bar(
            df_type_cohort,
            x="cohort",
            y="Total",
            color="applicant_type",
            barmode="group",
            text="Total",
            color_discrete_map={"Individual": C_ORANGE_DARK, "Team": C_ORANGE_LIGHT},
            category_orders={"cohort": ["Arabic", "English"]},
        )
        fig_type_cohort.update_traces(marker=dict(cornerradius=10), textposition="outside", cliponaxis=False)
        fig_type_cohort.update_layout(
            margin=dict(l=10, r=50, t=45, b=10),
            legend_title_text="Applicant Type",
            bargap=0.4,
            bargroupgap=0.25,
            legend=dict(orientation="h", y=1.35, x=0.5, xanchor="center", font=dict(family=CHART_FONT, size=10)),
            xaxis=dict(title="", showgrid=False, tickfont=dict(family=CHART_FONT, size=11, color=C_TEXT)),
            yaxis=dict(title="", visible=False),
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            font=dict(family=CHART_FONT, size=11, color=C_TEXT),
        )

        return _page_shell(
            "Cohort Comparison",
            kpis,
            _row(
                _card("Acceptance Rate by Cohort", fig_rate),
                _card("Cohort Size", fig_cohort),
            ),
            _row(
                _card("Top Sectors by Cohort", fig_sec_cohort),
                _card("Applicant Type by Cohort", fig_type_cohort),
            ),
        )

    else:  # page5 - Attendance
        if not any(col in dff.columns for col in ATTENDANCE_COLUMNS):
            return [
                html.Div(
                    "Attendance data is not included in the uploaded file",
                    style={
                        "flex": "1",
                        "background": "white",
                        "borderRadius": "20px",
                        "display": "flex",
                        "alignItems": "center",
                        "justifyContent": "center",
                        "fontWeight": "800",
                    },
                )
            ]

        if "team_attendance_rate" in dff.columns:
            att_series = _attendance_pct(dff["team_attendance_rate"])
            att_by_cohort = att_series.groupby(dff["cohort"]).mean().round(1).sort_values(ascending=False)
            fig_att_cohort = _bar_fig(
                att_by_cohort.index,
                att_by_cohort.values,
                text=att_by_cohort.values.astype(str) + "%",
            )
            att_by_year = att_series.groupby(dff["year"]).mean().round(1).sort_index()
            fig_att_year = _bar_fig(
                att_by_year.index,
                att_by_year.values,
                text=att_by_year.values.astype(str) + "%",
            )
            fig_att_year.update_layout(
                xaxis=dict(title="", showgrid=False, tickfont=dict(family=CHART_FONT, size=11, color=C_TEXT), tickformat="d")
            )
            att_by_sector = att_series.groupby(dff["Sector"]).mean().round(1).sort_values().tail(6)
            fig_att_sector = _bar_fig(
                att_by_sector.values,
                att_by_sector.index,
                orientation="h",
                text=att_by_sector.values.astype(str) + "%",
            )
        else:
            fig_att_cohort = _bar_fig([], [])
            fig_att_year = _bar_fig([], [])
            fig_att_sector = _bar_fig([], [])

        if {"sessions_scheduled", "team_days_present"}.issubset(dff.columns):
            sessions = (
                dff.groupby("year")[["sessions_scheduled", "team_days_present"]]
                .sum()
                .reset_index()
                .melt(id_vars="year", var_name="metric", value_name="Total")
            )
            sessions["metric"] = sessions["metric"].map(
                {
                    "sessions_scheduled": "Scheduled Sessions",
                    "team_days_present": "Days Present",
                }
            )
            fig_sessions = px.bar(
                sessions,
                x="year",
                y="Total",
                color="metric",
                barmode="group",
                color_discrete_map={
                    "Scheduled Sessions": C_ORANGE,
                    "Days Present": C_ORANGE_SOFT,
                },
                text="Total",
            )
            fig_sessions.update_traces(marker=dict(cornerradius=10), textposition="outside", cliponaxis=False)
            fig_sessions.update_layout(
                margin=dict(l=10, r=50, t=45, b=10),
                legend_title_text="Metric",
                bargap=0.4,
                bargroupgap=0.25,
                legend=dict(orientation="h", y=1.35, x=0.5, xanchor="center", font=dict(family=CHART_FONT, size=9)),
                xaxis=dict(title="", showgrid=False, tickfont=dict(family=CHART_FONT, size=11, color=C_TEXT), tickformat="d"),
                yaxis=dict(title="", visible=False),
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(0,0,0,0)",
                font=dict(family=CHART_FONT, size=11, color=C_TEXT),
            )
        else:
            fig_sessions = _bar_fig([], [])

        return _page_shell(
            "Attendance",
            kpis,
            _row(
                _card("Attendance Rate by Cohort", fig_att_cohort),
                _card("Attendance Rate by Year", fig_att_year),
            ),
            _row(
                _card("Sessions Scheduled vs Days Present", fig_sessions),
                _card("Attendance by Sector", fig_att_sector),
            ),
        )


# ---------------------------------------------------------------------------
# Entrypoint
# ---------------------------------------------------------------------------


def _load_env_file(path=".env"):
    """Minimal .env loader so the token does not have to live in code."""
    env = {}
    try:
        with open(path, "r", encoding="utf-8") as fh:
            for line in fh:
                line = line.strip()
                if not line or line.startswith("#") or "=" not in line:
                    continue
                key, _, value = line.partition("=")
                env[key.strip()] = value.strip().strip("\"'")
    except FileNotFoundError:
        pass
    return env


def start_ngrok_tunnel(port):
    """Create an ngrok tunnel for ``port``; return the public URL or None."""
    token = os.environ.get("NGROK_AUTHTOKEN") or _load_env_file().get("NGROK_AUTHTOKEN")
    if not token:
        print(
            "[warn] NGROK_AUTHTOKEN is not set (env or .env); running without a tunnel.",
            file=sys.stderr,
        )
        return None
    try:
        from pyngrok import ngrok

        ngrok.set_auth_token(token)
        # Clear any stale ngrok agents/tunnels left over from previous runs.
        ngrok.kill()
        time.sleep(0.5)
        try:
            for tunnel in ngrok.get_tunnels():
                ngrok.disconnect(tunnel.public_url)
        except Exception:
            pass
        tunnel = ngrok.connect(port, bind_tls=True)
        return tunnel.public_url
    except Exception as exc:  # never block the dashboard on tunnel issues
        print(f"[warn] could not start ngrok tunnel: {exc}", file=sys.stderr)
        return None


def main(argv=None):
    parser = argparse.ArgumentParser(description="Mashroo3i analytics dashboard")
    parser.add_argument("--host", default=os.environ.get("DASH_HOST", "0.0.0.0"))
    parser.add_argument("--port", type=int, default=int(os.environ.get("DASH_PORT", "8050")))
    parser.add_argument("--debug", action="store_true", default=bool(os.environ.get("DASH_DEBUG")))
    parser.add_argument("--no-ngrok", action="store_true", help="skip the ngrok tunnel")
    args = parser.parse_args(argv)

    public_url = None if args.no_ngrok else start_ngrok_tunnel(args.port)
    if public_url:
        print(f"Public dashboard: {public_url}")

    display_host = "localhost" if args.host in ("0.0.0.0", "") else args.host
    print(f"Local dashboard: http://{display_host}:{args.port}")
    app.run(host=args.host, port=args.port, debug=args.debug, use_reloader=False)


if __name__ == "__main__":
    main()
