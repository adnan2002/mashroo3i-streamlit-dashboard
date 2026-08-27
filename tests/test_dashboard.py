"""Smoke tests for the Mashroo3i dashboard (no browser required).

Run directly with ``python tests/test_dashboard.py`` or via pytest.
"""

import base64
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import app as dashboard

DUMMY_CSV = ROOT / "dummy_mashroo3i_2023_2026.csv"


def _upload_contents(path: Path) -> str:
    return "data:text/csv;base64," + base64.b64encode(path.read_bytes()).decode()


def test_index_page_serves():
    client = dashboard.server.test_client()
    response = client.get("/")
    assert response.status_code == 200
    assert b"Mashroo3i" in response.data


def test_upload_builds_filter_options():
    (
        status,
        year_opts,
        cohort_opts,
        outcome_opts,
        sector_opts,
        type_opts,
    ) = dashboard.handle_upload(_upload_contents(DUMMY_CSV), DUMMY_CSV.name)
    assert status is not None
    assert dashboard.DF_GLOBAL is not None and len(dashboard.DF_GLOBAL) > 0
    assert year_opts and all(isinstance(opt["value"], int) for opt in year_opts)
    assert cohort_opts and all("Arabic" in str(opt["label"]) or "English" in str(opt["label"]) for opt in cohort_opts)
    assert outcome_opts and sector_opts and type_opts
    assert "team_attendance_rate" in dashboard.DF_GLOBAL.columns


def test_all_pages_render_after_upload():
    status, *_ = dashboard.handle_upload(_upload_contents(DUMMY_CSV), DUMMY_CSV.name)
    for page in ("page1", "page2", "page3", "page4", "page5"):
        rendered = dashboard.update_page(page, status, None, None, None, None, None)
        assert rendered is not None and len(rendered) > 0, f"{page} produced no content"


def test_filters_produce_content():
    status, *_ = dashboard.handle_upload(_upload_contents(DUMMY_CSV), DUMMY_CSV.name)
    rendered = dashboard.update_page(
        "page1",
        status,
        years=[2024],
        cohorts=["Arabic"],
        outcomes=["Accepted"],
        sectors=None,
        types=["Individual"],
    )
    assert rendered is not None and len(rendered) > 0


def test_empty_data_uploads_render_a_prompt():
    dashboard.DF_GLOBAL = None
    rendered = dashboard.update_page("page1", None, None, None, None, None, None)
    assert rendered is not None and len(rendered) == 1


def test_switch_page():
    # `switch_page` reads dash.ctx, which only exists inside a live callback.
    # Simulate that callback context explicitly.
    import dash._callback_context as callback_context
    from dash._utils import AttributeDict

    token = callback_context.context_value.set(
        AttributeDict(
            triggered_inputs=[{"prop_id": "btn-p5.n_clicks", "value": 1}],
        )
    )
    try:
        page, s1, s2, s3, s4, s5 = dashboard.switch_page(0, 0, 0, 0, 1)
    finally:
        callback_context.context_value.reset(token)

    assert page == "page5"
    assert s5["background"] == dashboard.C_ORANGE
    assert s1["background"] == "white"


def test_no_page_word_in_buttons():
    buttons = dashboard.app.layout.children[0].children[4:9]
    assert len(buttons) == 5
    assert all("Page" not in child.children for child in buttons)


def main():
    tests = [
        test_index_page_serves,
        test_upload_builds_filter_options,
        test_all_pages_render_after_upload,
        test_filters_produce_content,
        test_empty_data_uploads_render_a_prompt,
        test_switch_page,
    ]
    for test in tests:
        test()
        print(f"PASS {test.__name__}")
    print(f"\nAll {len(tests)} tests passed.")


if __name__ == "__main__":
    main()
