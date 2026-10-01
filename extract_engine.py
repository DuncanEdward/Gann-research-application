import ast,json,pathlib,shutil,hashlib
root=pathlib.Path(__file__).resolve().parents[1]; p=root/'source/Bucholtz_Meridian_McWhirter_V10_2_3_ULTRA_LAZY.ipynb'; n=json.loads(p.read_text())

parts=['# Extracted from V10.2.3. Keep patch order; see source/ and CONVERSION.md.\nfrom __future__ import annotations\nfrom datetime import date\n']
manifest=[]
for idx in [10,13,19,21,23,26,27,29,31,38,41,43,44,47,49,53,55,59,60,63]:
 src=''.join(n['cells'][idx]['source']); lines=src.splitlines(keepends=True)
 for node in ast.parse(src).body:
  keep=True
  if idx==23:keep=isinstance(node,ast.FunctionDef) and node.name in ['show_detail','_validated_market_mode']
  if idx==27:
   keep=(isinstance(node,(ast.Import,ast.ImportFrom)) and not (isinstance(node,ast.ImportFrom) and node.module=='IPython.display')) or (isinstance(node,ast.FunctionDef) and node.name not in ['_download','on_pdf','on_csv','on_html'])
  if isinstance(node,ast.ImportFrom) and node.module=='__future__':keep=False
  if isinstance(node,ast.Expr):keep=False
  if idx==41 and isinstance(node,ast.If):keep=False
  if not keep:continue
  segment=''.join(lines[node.lineno-1:node.end_lineno])
  # Replace only the notebook-specific report output directory.
  segment=segment.replace("Path('/content' if Path('/content').exists() else '/mnt/data')","Path(REPORT_DIR)").replace('Path("/content" if Path("/content").exists() else "/mnt/data")','Path(REPORT_DIR)')
  parts.append(f'\n# Notebook cell {idx}, line {node.lineno}\n'+segment)
  if isinstance(node,ast.FunctionDef):manifest.append({'cell':idx,'function':node.name,'source_sha256':hashlib.sha256(ast.dump(node,include_attributes=False).encode()).hexdigest(),'report_path_adapted':segment!=''.join(lines[node.lineno-1:node.end_lineno])})
(root/'engine'/'notebook_core.py').write_text('\n'.join(parts))
(root/'source'/'extraction_manifest.json').write_text(json.dumps(manifest,indent=2))
