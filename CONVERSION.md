# Conversion record

Master source: `source/Bucholtz_Meridian_McWhirter_V10_2_3_ULTRA_LAZY.ipynb`.

The generated `engine/notebook_core.py` retains engine definitions and patch bindings in notebook order from cells 10, 13, 19, 21, 23 (detail and session validator only), 26, 27 (report definitions/imports only), 29, 31, 38, 41, 43, 44, 47, 49, 53, 55, 59, 60 and 63.

Removed: runtime pip installation, Colab upload/download prompts, ipywidgets controls/callbacks, notebook display calls at startup, ready messages and scratch diagnostic cells. Added: Streamlit controls, session module loader, strict CSV validation, manual/Finviz selection through the existing stock-universe argument path, private temporary report folders and optional password gate.

Each retained top-level engine function has the same AST as its source counterpart, except that legacy report output directories are replaced by `REPORT_DIR`. `source/extraction_manifest.json` records original function hashes. The automated source comparison checks every retained function and its override order. No scoring weights, source-rule tables, technical gates, timing algorithms, inherited commodity wrapper behaviour or trade-plan formula have been edited.

The web adapter is deliberately conservative: it loads the whole extracted engine in a fresh namespace, rather than splitting the interdependent patches into individual book modules. A new engine is created for every submitted scan. Browser sessions do not share LAST_SCAN_RESULTS, first-trade databases or timing caches. A process lock protects calls because Swiss Ephemeris and redirected console output have process-wide state.

Tests cover CSV parsing, invalid uploads, lazy startup, independent session globals/output folders, historical mode enforcement, synthetic-OHLC scoring through all three engines, selected timing, PDF/CSV/HTML generation and failed-scan cleanup. Synthetic prices test the software pipeline only; they are not trading evidence. Live Yahoo requests and a real Render deployment are separate checks and require the hosting/data environment.

## Validation performed

All **7 tests passed** locally using the pinned dependency set (Python 3.12 test runtime; Render and CI are configured for Python 3.11). Source comparison checked **197 function definitions**, including repeated overrides. The Streamlit test driver exercised the initial interface, password gate, one synthetic-price NVDA scan with embedded database, and all three report downloads. The separate engine test used a replacement first-trade CSV and verified failed-scan cleanup. No live Yahoo data or Render deployment was tested.
