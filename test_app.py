from pathlib import Path
from streamlit.testing.v1 import AppTest

APP = Path(__file__).resolve().parents[1] / 'app.py'


def test_app_initial_screen(monkeypatch):
    monkeypatch.delenv('APP_PASSWORD', raising=False)
    app = AppTest.from_file(str(APP)).run(timeout=30)
    assert not app.exception
    assert app.title[0].value == 'Bucholtz · Meridian · McWhirter'
    assert app.button[0].label == 'Run analysis'


def test_password_gate(monkeypatch):
    monkeypatch.setenv('APP_PASSWORD', 'test-only-password')
    app = AppTest.from_file(str(APP)).run(timeout=30)
    assert not app.exception
    assert app.text_input[0].label == 'Password'
    app.text_input[0].set_value('wrong')
    app.button[0].click().run()
    assert app.error
    assert not app.exception
    app.text_input[0].set_value('test-only-password')
    app.button[0].click().run()
    assert not app.exception
    assert app.title[0].value == 'Bucholtz · Meridian · McWhirter'


def test_app_scan_and_report_workflow(monkeypatch):
    import engine.adapter as adapter
    import pandas as pd
    import numpy as np
    original = adapter.ResearchEngine
    class FixtureEngine(original):
        def __init__(self):
            super().__init__()
            index = pd.bdate_range('2023-01-02', '2026-09-30')
            x = np.arange(len(index))
            close = 40 + x*.08 + np.sin(x/8)*2
            prices = pd.DataFrame({'Open':close-.3, 'High':close+1, 'Low':close-1,
                                   'Close':close, 'Volume':3000000}, index=index)
            self.core.fetch_history = lambda *a, **k: prices.copy()
    monkeypatch.setattr(adapter, 'ResearchEngine', FixtureEngine)
    monkeypatch.delenv('APP_PASSWORD', raising=False)
    app = AppTest.from_file(str(APP)).run(timeout=30)
    app.text_area[0].set_value('NVDA')
    app.button[0].click().run(timeout=30)
    assert not app.exception
    assert not app.error
    assert app.dataframe
    report_button = next(b for b in app.button if b.label == 'Prepare PDF, CSV and HTML reports')
    report_button.click().run(timeout=30)
    assert not app.exception
    assert not app.error
    assert len(app.session_state['engine'].exports) == 3
    app.session_state['engine'].close()
