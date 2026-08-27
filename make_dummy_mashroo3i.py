"""Generate synthetic Mashroo3i data matching mashroo3i_dtypes.DTYPE_MAP.

Usage:
    python make_dummy_mashroo3i.py [--rows 800] [--seed 42] [--out dummy_mashroo3i_2023_2026.csv]
"""

import argparse
import random
from datetime import datetime, timedelta

import numpy as np
import pandas as pd

from mashroo3i_dtypes import DTYPE_MAP


# ---------------------------------------------------------------------------
# Realistic value pools (same vocabulary as the original cleaned dataset).
# ---------------------------------------------------------------------------

NATIONALITIES = [
    "Bahrain", "Pakistan", "Egypt", "India", "Nigeria", "Yemen",
    "Saudi Arabia", "Sudan", "Jordan", "Argentina", "United Kingdom",
    "United States", "Philippines", "Sri Lanka", "Not Specified",
]

GENDERS = ["Female", "Male"]

EMPLOYMENT = [
    "Employed", "Unemployed", "Student", "Self-Employed",
    "Founder", "Graduate", "Freelancer", "Retired",
]

EDUCATION = [
    "University / Higher Education", "Bachelor's", "Employment / Professional",
    "University Student", "High School", "Master's", "Diploma / Associate's",
    "Doctorate", "High School Student", "Not Specified",
]

MAJORS = [
    "Computer Science & IT", "Finance, Banking & Accounting",
    "Media & Communication", "Medicine & Health", "Science & Humanities",
    "Engineering & Architecture", "Cybersecurity & Networking",
    "Hospitality & Tourism", "Business & Management", "Aviation & Logistics",
    "Law", "Not Specified",
]

AGE_GROUPS = ["18-24", "25-34", "35-44", "45+", "Not Specified"]

STAGES = ["Idea", "MVP", "Operating", "Revenue Generating"]

SECTORS = [
    "Food & Beverage", "Retail & Consumer Goods", "Health & Medicine",
    "Environment & Sustainability", "Technology & IT", "Manufacturing",
    "Fashion, Textiles & Beauty", "Entertainment & Events",
    "Media, Design & Creative", "Services & Consulting",
    "Transportation & Automotive", "Real Estate & Construction",
]

SUBSECTORS = [
    "Food & Beverage", "Retail & Consumer Goods", "Environment & Sustainability",
    "Fashion, Textiles & Beauty", "Health & Medicine", "Sports & Fitness",
    "Technology & IT", "Media, Design & Creative", "FinTech & Finance",
    "Entertainment & Events", "Tourism & Hospitality",
    "Transportation & Automotive",
]

HOW_HEARD = [
    "Email", "Other Online / Social Media", "Programs & Organizations",
    "Instagram", "Tamkeen (Direct)", "LinkedIn", "University / Education",
    "Other / Unspecified", "Word of Mouth / Referral", "Friends & Family",
    "Government / Ministries", "TikTok",
]

PRIOR_EXPERIENCE = ["No", "Yes", "Unspecified"]

TARGET_CUSTOMERS = [
    "Businesses & Companies", "Government & Public Sector", "Athletes & Fitness",
    "Women", "Travelers & Expats", "General Public", "Youth & Teens",
    "Parents & Families", "Health & Medical", "Investors & Funders",
    "Professionals & Employees", "Other / Unspecified",
]

PROBLEMS = [
    "Local businesses struggle to manage orders across multiple channels.",
    "Students lack a simple way to track and share their study progress.",
    "Homeowners have no easy tool to compare maintenance service quotes.",
    "Small retailers cannot afford expensive inventory analytics software.",
    "Freelancers waste time chasing late payments from clients.",
]

SOLUTIONS = [
    "A unified dashboard that consolidates orders and automates follow-ups.",
    "A lightweight study tracker with shared milestones and reminders.",
    "A quote-comparison marketplace for verified local service providers.",
    "An affordable analytics tool built specifically for small shops.",
    "Automated invoicing with gentle payment reminders and reports.",
]

DIFFERENTIATION = [
    "One low monthly price instead of per-seat licensing.",
    "Arabic-first interface with SMS reminders, not just email.",
    "Direct integration with local banks and payment gateways.",
    "A 15-minute onboarding flow requiring no technical setup.",
]

SALES_APPROACH = [
    "Direct sales to businesses with a free pilot period.",
    "Social media campaigns plus a referral program for early users.",
    "Partnerships with universities and co-working spaces.",
    "Subscription tiers with a freemium starter plan.",
]

IMPACT = [
    "Saves users time and reduces operational errors.",
    "Helps underserved businesses adopt digital tools.",
    "Creates local jobs and keeps spending in the community.",
    "Improves access to services for residents.",
]

INSPIRATION = [
    "Frustration from personal experience with the same problem.",
    "Feedback from a family member who runs a small business.",
    "A gap noticed while working in the industry.",
]

WHY_JOIN = [
    "To validate the idea and learn from experienced mentors.",
    "To meet co-founders and build a stronger team.",
    "To get structured feedback and access to funding networks.",
]

EXPECTATIONS = [
    "Clear milestones and honest feedback from mentors.",
    "Connections to investors and pilot customers.",
    "Practical workshops on sales and financial planning.",
]

TEAM_FIT = [
    "Complementary skills across product, sales and finance.",
    "Deep domain knowledge plus a technical co-founder.",
    "A track record of shipping projects in a small team.",
]

KEYWORDS_POOL = [
    "marketplace", "fintech", "health", "education", "logistics",
    "sustainability", "retail", "b2b", "consumer", "saas", "food",
    "tourism", "automation",
]


def _rand_time_between(start: datetime, end: datetime, rng: random.Random) -> datetime:
    span = int((end - start).total_seconds())
    return start + timedelta(seconds=rng.randint(0, span))


def _age_from_group(age_group: str, rng: random.Random) -> int:
    if age_group == "18-24":
        return rng.randint(18, 24)
    if age_group == "25-34":
        return rng.randint(25, 34)
    if age_group == "35-44":
        return rng.randint(35, 44)
    if age_group == "45+":
        return rng.randint(45, 65)
    return rng.randint(20, 50)


def generate_dummy(rows: int = 800, seed: int = 42) -> pd.DataFrame:
    """Build a synthetic DataFrame with every column from DTYPE_MAP."""
    rng = random.Random(seed)
    np_rng = np.random.default_rng(seed)

    # Year weights so every year from 2023 to 2026 is well represented.
    year_weights = {2023: 0.22, 2024: 0.26, 2025: 0.28, 2026: 0.24}
    years = [2023, 2024, 2025, 2026]
    year_choices = rng.choices(years, weights=[year_weights[y] for y in years], k=rows)

    records = []
    seq_by_year = {y: 1 for y in years}

    for i, year in enumerate(year_choices):
        r = {}

        # ---- Submitted timestamp -------------------------------------------------
        start = datetime(year, 1, 1)
        end = datetime(year, 12, 31, 23, 59, 59)
        submitted = _rand_time_between(start, end, rng)
        r["submitted_at"] = submitted
        r["year"] = year

        # ---- Cohorts: 2023 was English-only, later years mix --------------------
        r["cohort"] = "English" if year == 2023 else rng.choice(["English", "Arabic"])

        # ---- Identity -----------------------------------------------------------
        r["nationality"] = rng.choice(NATIONALITIES)
        r["gender"] = rng.choice(GENDERS)
        age_group = rng.choice(AGE_GROUPS)
        r["Age Group"] = age_group
        age = _age_from_group(age_group, rng)
        dob_year = year - age
        dob = datetime(dob_year, rng.randint(1, 12), rng.randint(1, 28))
        r["date_of_birth"] = dob
        r["employment_status"] = rng.choice(EMPLOYMENT)
        r["education"] = rng.choice(EDUCATION)
        r["major"] = rng.choice(MAJORS)

        # ---- Team vs individual -------------------------------------------------
        is_team = rng.random() < 0.30
        team_member_count = float(rng.randint(2, 5) if is_team else 1)
        r["team_member_count"] = team_member_count
        r["individual_or_team"] = "Team" if is_team else "Individual"
        r["applicant_type"] = "Team" if is_team else "Individual"
        r["team_type_raw"] = "Team" if is_team else "Solo"
        r["team_size_raw"] = f"{int(team_member_count)}"

        # ---- Venture -------------------------------------------------------------
        project = f"Dummy Project {seq_by_year[year]:04d}"
        r["project_name"] = project
        stage = rng.choice(STAGES)
        r["stage"] = stage
        r["Business Stage"] = stage if rng.random() < 0.9 else "Not Specified"
        sector = rng.choice(SECTORS)
        subsector = rng.choice(SUBSECTORS)
        r["sector"] = sector
        r["subsector"] = subsector
        # The dashboard uses 'Sector', whose original values include this casing.
        r["Sector"] = sector if rng.random() < 0.95 else "Not Specified"
        r["sector_all"] = sector
        r["subsector_all"] = subsector

        registered = rng.random() < 0.35
        r["has_commercial_registration"] = "Yes" if registered else "No"

        # ---- Essays --------------------------------------------------------------
        r["problem"] = rng.choice(PROBLEMS)
        r["solution"] = rng.choice(SOLUTIONS)
        r["differentiation"] = rng.choice(DIFFERENTIATION)
        r["sales_approach"] = rng.choice(SALES_APPROACH)
        r["target_customers"] = rng.choice(TARGET_CUSTOMERS)
        r["impact"] = rng.choice(IMPACT)
        r["inspiration"] = rng.choice(INSPIRATION)
        r["why_join"] = rng.choice(WHY_JOIN)
        r["program_expectations"] = rng.choice(EXPECTATIONS)
        r["team_fit"] = rng.choice(TEAM_FIT)
        for suffix in ["_en"]:
            r[f"problem{suffix}"] = r["problem"]
            r[f"solution{suffix}"] = r["solution"]
            r[f"differentiation{suffix}"] = r["differentiation"]
            r[f"sales_approach{suffix}"] = r["sales_approach"]
            r[f"impact{suffix}"] = r["impact"]
            r[f"inspiration{suffix}"] = r["inspiration"]
            r[f"why_join{suffix}"] = r["why_join"]
            r[f"program_expectations{suffix}"] = r["program_expectations"]
            r[f"team_fit{suffix}"] = r["team_fit"]

        # ---- Program metadata ------------------------------------------------------
        how_heard = rng.choice(HOW_HEARD)
        r["how_heard"] = how_heard
        r["how_heard_all"] = how_heard if rng.random() < 0.8 else f"{how_heard}; {rng.choice(HOW_HEARD)}"
        prior = rng.choice(PRIOR_EXPERIENCE)
        r["prior_program_experience"] = prior
        r["prior_program_experience_all"] = prior if prior != "Unspecified" else "Not Specified"
        previous_participant = rng.random() < 0.08
        r["previous_mashroo3i_participant"] = "Yes" if previous_participant else "No"
        if previous_participant:
            r["previous_mashroo3i_year"] = float(rng.randint(2014, year))
        else:
            r["previous_mashroo3i_year"] = np.nan

        # ---- Outcome ----------------------------------------------------------------
        accepted = rng.random() < 0.35
        r["outcome"] = "Yes" if accepted else "No"
        r["outcome_clean"] = "Accepted" if accepted else "Rejected"
        r["is_duplicate"] = rng.random() < 0.02

        # ---- IDs ----------------------------------------------------------------------
        app_id = f"APP-{year}-{seq_by_year[year]:05d}"
        seq_by_year[year] += 1
        r["application_id"] = app_id

        # ---- Attendance (only a subset of rows attended) ------------------------------
        has_attendance = rng.random() < 0.15
        if has_attendance:
            sessions = rng.randint(2, 9)
            present = rng.randint(1, sessions)
            absent = sessions - present
            r["sessions_scheduled"] = sessions
            r["team_days_present"] = present
            r["team_days_virtual"] = 0
            r["team_days_absent"] = absent
            r["team_attendance_rate"] = present / sessions
            size = int(team_member_count)
            r["member_days_present"] = present * size
            r["member_days_virtual"] = 0
            r["member_days_absent"] = absent * size
            r["member_days_unknown"] = 0
            r["member_attendance_rate"] = present / sessions
            r["attendance_member_rows"] = size
            first = submitted + timedelta(days=rng.randint(1, 45))
            last = first + timedelta(weeks=rng.randint(1, 8))
            year_end = datetime(year, 12, 31, 23, 59, 59)
            first = min(first, year_end)
            last = min(max(last, first), year_end)
            r["first_session"] = first
            r["last_session"] = last
            r["max_consecutive_absences"] = rng.randint(0, 3)
            r["team_size_from_attendance"] = float(size)
            r["team_size_check"] = rng.choices(
                ["match", "mismatch", "missing_attendance_count"],
                weights=[0.7, 0.15, 0.15],
                k=1,
            )[0]
        else:
            for col in (
                "sessions_scheduled", "team_days_present", "team_days_virtual",
                "team_days_absent", "member_days_present", "member_days_virtual",
                "member_days_absent", "member_days_unknown", "max_consecutive_absences",
                "attendance_member_rows",
            ):
                r[col] = 0
            r["team_attendance_rate"] = np.nan
            r["member_attendance_rate"] = np.nan
            r["first_session"] = pd.NaT
            r["last_session"] = pd.NaT
            r["team_size_from_attendance"] = np.nan
            r["team_size_check"] = rng.choices(
                ["not_comparable", "missing_attendance_count"],
                weights=[0.6, 0.4],
                k=1,
            )[0]

        # ---- Engagement forms -------------------------------------------------------------
        form_filled = rng.randint(0, 4)
        r["form_filled_count"] = form_filled
        r["participant_info_form_filled"] = min(form_filled, rng.randint(0, 4))
        r["tc_total"] = rng.randint(0, 4)
        r["tc_completed_count"] = rng.randint(0, r["tc_total"] + 1)
        r["whatsapp_group_joined"] = rng.random() < 0.4
        r["refined_problem_filled"] = rng.randint(0, 3)

        # ---- Matching ---------------------------------------------------------------------
        matched = has_attendance and rng.random() < 0.85
        r["attendance_matched"] = matched
        r["match_method"] = "exact" if matched else "unmatched"
        r["match_score"] = 1.0 if matched else np.nan
        r["matched_project_name"] = project if matched else np.nan
        r["matched_application_id"] = app_id if matched else np.nan
        r["attendance_project_name_raw"] = project

        # ---- Customer targeting ------------------------------------------------------------
        target = rng.choice(TARGET_CUSTOMERS)
        r["target_customers_normalized"] = target
        r["target_customers_all"] = target

        r["keywords"] = ", ".join(rng.sample(KEYWORDS_POOL, k=rng.randint(3, 6)))

        records.append(r)

    df = pd.DataFrame(records, columns=list(DTYPE_MAP))

    # Keep everything within the requested 2023-2026 window.
    df["submitted_at"] = pd.to_datetime(df["submitted_at"])
    df["date_of_birth"] = pd.to_datetime(df["date_of_birth"])
    df["first_session"] = pd.to_datetime(df["first_session"])
    df["last_session"] = pd.to_datetime(df["last_session"])

    return df


def write_dummy(df: pd.DataFrame, path: str) -> None:
    """Write the CSV so mashroo3i_dtypes.load_csv() reads it cleanly."""
    out = df.copy()

    # Yes/No columns must be plain strings.
    for col in ("has_commercial_registration", "previous_mashroo3i_participant", "outcome"):
        out[col] = out[col].astype("string")

    # Nullable ints are float-formatted in the source CSV.
    for col in ("team_member_count", "previous_mashroo3i_year", "team_size_from_attendance"):
        out[col] = pd.to_numeric(out[col], errors="coerce")

    # Plain booleans -> "True"/"False".
    for col in ("whatsapp_group_joined", "is_duplicate", "attendance_matched"):
        out[col] = out[col].astype(bool).map({True: "True", False: "False"})

    out.to_csv(path, index=False, encoding="utf-8-sig")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--rows", type=int, default=800)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--out", default="dummy_mashroo3i_2023_2026.csv")
    args = parser.parse_args()

    df = generate_dummy(rows=args.rows, seed=args.seed)
    write_dummy(df, args.out)
    print(f"Wrote {len(df)} rows x {len(df.columns)} columns -> {args.out}")
    print("Year distribution:", df["year"].value_counts().sort_index().to_dict())


if __name__ == "__main__":
    main()
