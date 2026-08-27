"""Pandas dtype map and loader for 'cleaned_mashroo3i (3).csv'."""

import pandas as pd

PATH = "cleaned_mashroo3i (3).csv"

# Columns read via parse_dates (empty cells become NaT).
DATE_COLS = ["submitted_at", "date_of_birth", "first_session", "last_session"]

# Yes/No strings that must be mapped to real booleans after reading.
YES_NO_COLS = {
    "has_commercial_registration",
    "previous_mashroo3i_participant",
    "outcome",
}

# Source values are float-formatted ("1.0"); cast to nullable Int64 after reading.
FLOAT_AS_INT_COLS = {
    "team_member_count",
    "previous_mashroo3i_year",
    "team_size_from_attendance",
}

DTYPE_MAP = {
    # Identity & demographics
    "year": "int64",
    "submitted_at": "datetime64[ns]",
    "cohort": "category",
    "nationality": "category",
    "date_of_birth": "datetime64[ns]",
    "gender": "category",
    "employment_status": "category",
    "individual_or_team": "category",
    "applicant_type": "category",
    "team_member_count": "Int64",
    "education": "category",
    "major": "category",
    "Age Group": "category",
    # Venture & classification
    "project_name": "string",
    "stage": "category",
    "Business Stage": "category",
    "sector": "category",
    "subsector": "category",
    "Sector": "category",
    "sector_all": "string",
    "subsector_all": "string",
    "has_commercial_registration": "boolean",
    "application_id": "string",
    "outcome": "boolean",
    "outcome_clean": "category",
    "is_duplicate": "boolean",
    # Long-form essay fields (and English translations)
    "problem": "string",
    "problem_en": "string",
    "solution": "string",
    "solution_en": "string",
    "differentiation": "string",
    "differentiation_en": "string",
    "sales_approach": "string",
    "sales_approach_en": "string",
    "target_customers": "string",
    "impact": "string",
    "impact_en": "string",
    "inspiration": "string",
    "inspiration_en": "string",
    "why_join": "string",
    "why_join_en": "string",
    "program_expectations": "string",
    "program_expectations_en": "string",
    "team_fit": "string",
    "team_fit_en": "string",
    # Program metadata
    "how_heard": "category",
    "how_heard_all": "category",
    "prior_program_experience": "category",
    "prior_program_experience_all": "string",
    "previous_mashroo3i_participant": "boolean",
    "previous_mashroo3i_year": "Int64",
    "target_customers_normalized": "category",
    "target_customers_all": "string",
    "keywords": "string",
    # Attendance & engagement
    "attendance_project_name_raw": "string",
    "attendance_member_rows": "int64",
    "sessions_scheduled": "int64",
    "team_days_present": "int64",
    "team_days_virtual": "int64",
    "team_days_absent": "int64",
    "team_attendance_rate": "float64",
    "member_days_present": "int64",
    "member_days_virtual": "int64",
    "member_days_absent": "int64",
    "member_days_unknown": "int64",
    "member_attendance_rate": "float64",
    "first_session": "datetime64[ns]",
    "last_session": "datetime64[ns]",
    "max_consecutive_absences": "int64",
    "form_filled_count": "int64",
    "participant_info_form_filled": "int64",
    "tc_completed_count": "int64",
    "tc_total": "int64",
    "whatsapp_group_joined": "boolean",
    "refined_problem_filled": "int64",
    # Matching & quality checks
    "team_type_raw": "category",
    "team_size_raw": "string",
    "team_size_from_attendance": "Int64",
    "matched_project_name": "string",
    "match_method": "category",
    "match_score": "float64",
    "matched_application_id": "string",
    "attendance_matched": "boolean",
    "team_size_check": "category",
}


def load_csv(path: str = PATH) -> pd.DataFrame:
    """Read the CSV with its intended pandas dtypes applied."""
    read_dtype = {
        col: (
            "category"
            if col in YES_NO_COLS
            else "float64"
            if col in FLOAT_AS_INT_COLS
            else dtype
        )
        for col, dtype in DTYPE_MAP.items()
        if dtype != "datetime64[ns]"
    }
    df = pd.read_csv(
        path,
        dtype=read_dtype,
        parse_dates=DATE_COLS,
        encoding="utf-8-sig",
    )
    df[DATE_COLS] = df[DATE_COLS].astype("datetime64[ns]")
    for col in YES_NO_COLS:
        df[col] = df[col].map({"Yes": True, "No": False}).astype("boolean")
    for col in FLOAT_AS_INT_COLS:
        df[col] = df[col].astype("Int64")
    return df
