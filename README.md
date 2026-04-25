# 📊 AuditPal

An AI-powered document assistant for accountants, built as a [Streamlit](https://streamlit.io/) UI on top of [NotebookLM](https://notebooklm.google.com/) via the [`notebooklm-py`](https://pypi.org/project/notebooklm-py/) library.

Upload tax forms, financial statements, and client documents into a notebook, then ask questions about them in natural language. Answers come back with inline citations linking to the source passages.

## Features

- 📤 Upload PDFs, spreadsheets, and other documents, or add URL sources
- 💬 Chat with your sources — follow-up questions retain conversation context
- 📎 Inline citation badges (`[1]`, `[2]`) with hover tooltips showing the source title and cited passage
- 📋 Pre-built prompt templates for common accounting tasks (summaries, discrepancy checks, tax summaries, etc.)
- 📥 Export chat transcripts to Markdown or PDF
- 📓 Multi-notebook workspace via the sidebar

## Requirements

- Python >= 3.10
- A Google account with access to NotebookLM
- (Optional) Docker, for containerised deployment

## One-time setup: NotebookLM authentication

The app talks to NotebookLM using a stored browser session. Run this **on your host machine** once:

```bash
pip install "notebooklm-py[browser]"
playwright install chromium
notebooklm login
```

A browser window opens — sign in with the Google account that has NotebookLM access. The session is saved to `~/.notebooklm/storage_state.json`.

## Running locally (recommended for development)

Install dependencies and start Streamlit:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e .
streamlit run app.py
```

Then open <http://localhost:8501>.

## Running with Docker

The repo ships with a `Dockerfile` and `docker-compose.yml`.

```bash
# Make your NotebookLM credentials available to the image build
mkdir -p credentials
cp ~/.notebooklm/storage_state.json credentials/

docker-compose up -d --build
```

Open <http://localhost:8501>. Stop with `docker-compose down`.

> ⚠️ The Docker image bakes credentials in at build time. Do not push the resulting image to a public registry.

## Project layout

```
auditpal/
├── app.py                  # Streamlit entry point and main layout
├── config.py               # Settings + prompt templates
├── components/
│   ├── chat.py             # Chat UI with citation tooltips
│   ├── sidebar.py          # Notebook picker / creator
│   ├── sources.py          # File / URL source management
│   └── templates.py        # Prompt template UI
├── services/
│   └── notebook.py         # NotebookLM client wrapper
├── utils/
│   └── export.py           # Markdown / PDF export
├── Dockerfile
└── docker-compose.yml
```

## Configuration

Settings are loaded from environment variables (or a `.env` file in the project root) via `config.py`. See `.env.example` for available options. Key settings:

| Variable | Default | Description |
| --- | --- | --- |
| `MAX_FILE_SIZE_MB` | `50` | Maximum allowed upload size |
| `SUPPORTED_EXTENSIONS` | `.pdf .txt .md .docx .xlsx .csv` | File types accepted by the uploader |

## Citations

Answers from NotebookLM include reference markers in the text (`[1]`, `[2]`, or grouped like `[1, 2]`). AuditPal renders each as a styled hover badge — hover to see the source title and the cited passage extracted by NotebookLM.

Some citations may show `(no excerpt extracted)` — this happens when the upstream NotebookLM API does not return a text passage for that citation; the source title is still displayed.

## Limitations

- The `notebooklm-py` library reverse-engineers Google's internal API and may break on Google-side changes.
- Citation excerpts are only as detailed as what NotebookLM exposes; for table-heavy PDFs they can be a single cell value.
- Conversation context resets when you switch notebooks or clear the chat.

## License

MIT — see `pyproject.toml` for details.
