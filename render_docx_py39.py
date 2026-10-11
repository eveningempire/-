from pathlib import Path
src = Path(r'C:/Users/HP/.codex/plugins/cache/openai-primary-runtime/documents/26.1007.11041/skills/documents/render_docx.py')
dst = Path('render_docx_py39_impl.py')
text = src.read_text(encoding='utf-8').replace('tempfile.TemporaryDirectory[str] | None', 'object')
dst.write_text(text, encoding='utf-8')
print(dst)
