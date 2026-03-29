"""
Gradio UI — Lecture Gap Finder
Beautiful, dark-mode interface for uploading lecture notes
and getting back a structured study guide.
"""
import os
import warnings
import tempfile
from dotenv import load_dotenv
import sys
print("=== LOADER STARTING ===", flush=True)
# Suppress upstream Pydantic V1 / Python 3.14 compatibility warnings from LangChain
warnings.filterwarnings("ignore", message=".*Pydantic V1.*", category=UserWarning)
warnings.filterwarnings("ignore", message=".*pydantic.v1.*", category=UserWarning)

load_dotenv()

import gradio as gr
from graph import app as gap_finder_graph
from nodes.parse_node import extract_text_from_file

# ─── Custom CSS ──────────────────────────────────────────────────────────────
CSS = """
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');

* { font-family: 'Inter', sans-serif; box-sizing: border-box; }

body, .gradio-container {
    background: #0f0f13 !important;
    color: #e2e8f0 !important;
}

.header-box {
    background: linear-gradient(135deg, #1a1a2e 0%, #16213e 50%, #0f3460 100%);
    border: 1px solid rgba(99, 102, 241, 0.3);
    border-radius: 16px;
    padding: 32px;
    margin-bottom: 24px;
    text-align: center;
}

.header-box h1 {
    font-size: 2.4rem;
    font-weight: 700;
    background: linear-gradient(135deg, #818cf8, #c084fc, #f472b6);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    margin: 0 0 8px 0;
}

.header-box p {
    color: #94a3b8;
    font-size: 1rem;
    margin: 0;
}

.step-badge {
    display: inline-block;
    background: rgba(99, 102, 241, 0.15);
    border: 1px solid rgba(99, 102, 241, 0.4);
    color: #818cf8;
    padding: 4px 12px;
    border-radius: 20px;
    font-size: 0.75rem;
    font-weight: 600;
    margin: 4px;
}

.gradio-button.primary {
    background: linear-gradient(135deg, #6366f1, #8b5cf6) !important;
    border: none !important;
    color: white !important;
    font-weight: 600 !important;
    padding: 12px 32px !important;
    border-radius: 10px !important;
    font-size: 1rem !important;
    transition: all 0.3s ease !important;
}

.gradio-button.primary:hover {
    transform: translateY(-2px) !important;
    box-shadow: 0 8px 25px rgba(99, 102, 241, 0.4) !important;
}

.status-box {
    background: rgba(15, 23, 42, 0.8);
    border: 1px solid rgba(99, 102, 241, 0.2);
    border-radius: 10px;
    padding: 12px 16px;
    font-family: 'Courier New', monospace;
    font-size: 0.85rem;
    color: #a5f3fc;
}

label { color: #94a3b8 !important; font-weight: 500 !important; }

.dark { --color-accent: #6366f1; }
"""

# ─── Processing Logic ─────────────────────────────────────────────────────────

def process_file(file, progress=gr.Progress()):
    """Main function: takes uploaded file, runs LangGraph pipeline."""
    if file is None:
        return "⚠️ Please upload a file first.", "", []

    progress(0.05, desc="📄 Reading file...")

    try:
        # Extract text from uploaded file
        file_name = os.path.basename(file.name)
        raw_text = extract_text_from_file(file.name)

        if not raw_text.strip():
            return "❌ Could not extract text from this file.", "", []

        progress(0.15, desc="🧠 Identifying concepts...")

        # Build initial state
        initial_state = {
            "file_name": file_name,
            "raw_text": raw_text,
            "all_concepts": [],
            "gaps": [],
            "prioritized_gaps": [],
            "filled_gaps": [],
            "concept_dependencies": {},
            "study_guide": "",
            "flashcards": [],
            "status": "Starting...",
            "messages": []
        }

        # Invoke the graph, collecting all node outputs for status log
        progress(0.20, desc="🧠 Running pipeline...")
        final = gap_finder_graph.invoke(initial_state)
        progress(1.0, desc="✅ Done!")

        study_guide = final.get("study_guide", "No study guide generated.")
        flashcards = final.get("flashcards", [])
        flashcards_md = _format_flashcards(flashcards)

        n_gaps = len(final.get("filled_gaps", []))
        status_text = f"✅ Analysis complete!\n🔍 Found and filled {n_gaps} knowledge gaps.\n📖 Study guide generated.\n🃏 {len(flashcards)} flashcards created."

        return status_text, study_guide, flashcards_md

    except Exception as e:
        import traceback
        return f"❌ Error: {str(e)}\n\n{traceback.format_exc()}", "", ""


def process_text(text_input, progress=gr.Progress()):
    """Process pasted text directly."""
    if not text_input.strip():
        return "⚠️ Please paste some lecture notes.", "", ""

    progress(0.05, desc="📝 Processing text...")

    try:
        initial_state = {
            "file_name": "pasted_notes.txt",
            "raw_text": text_input,
            "all_concepts": [],
            "gaps": [],
            "prioritized_gaps": [],
            "filled_gaps": [],
            "concept_dependencies": {},
            "study_guide": "",
            "flashcards": [],
            "status": "Starting...",
            "messages": []
        }

        progress(0.3, desc="🧠 Analyzing notes...")
        final = gap_finder_graph.invoke(initial_state)
        progress(1.0, desc="✅ Done!")

        study_guide = final.get("study_guide", "")
        flashcards = final.get("flashcards", [])
        flashcards_md = _format_flashcards(flashcards)

        status = f"✅ Found {len(final.get('filled_gaps', []))} gaps in your notes!"
        return status, study_guide, flashcards_md

    except Exception as e:
        import traceback
        return f"❌ Error: {str(e)}\n\n{traceback.format_exc()}", "", ""


def _format_flashcards(flashcards: list) -> str:
    if not flashcards:
        return "No flashcards generated."

    severity_emoji = {"high": "🔴", "medium": "🟡", "low": "🟢"}
    lines = [f"# 🃏 {len(flashcards)} Flashcards\n"]

    for i, card in enumerate(flashcards, 1):
        emoji = severity_emoji.get(card.get("severity", "medium"), "🟡")
        lines.append(f"### Card {i} {emoji} — {card['concept'].title()}")
        lines.append(f"**Q:** {card['question']}")
        lines.append(f"**A:** {card['answer']}")
        lines.append("")

    return "\n".join(lines)


# ─── SAMPLE TEXT for demo ─────────────────────────────────────────────────────
SAMPLE_TEXT = """
Introduction to Transformer Architecture

The transformer model relies heavily on the attention mechanism to process sequences.
Unlike RNNs, transformers can process tokens in parallel using self-attention layers.

Multi-head attention extends this by running attention in parallel across multiple heads,
allowing the model to attend to different representation subspaces simultaneously.

Positional encoding is added to input embeddings since transformers have no recurrence.
The model uses layer normalization after each sub-layer to stabilize training.

As you know from your linear algebra background, matrix multiplication is central to
attention computation. The attention scores are computed using softmax normalization.

BLEU score is commonly used to evaluate translation quality. The models are typically
trained using cross-entropy loss with teacher forcing.
"""

# ─── Gradio UI ────────────────────────────────────────────────────────────────
with gr.Blocks(title="Lecture Gap Finder") as demo:

    gr.HTML("""
    <div class="header-box">
        <h1>🎓 Lecture Gap Finder</h1>
        <p>Upload your lecture slides or paste notes — AI finds what's missing and fills the gaps</p>
        <br>
        <span class="step-badge">1. Parse</span>
        <span class="step-badge">2. Detect Gaps</span>
        <span class="step-badge">3. Prioritize</span>
        <span class="step-badge">4. Fill via MCP</span>
        <span class="step-badge">5. Map Dependencies</span>
        <span class="step-badge">6. Study Guide</span>
    </div>
    """)

    with gr.Tabs():
        # ── Tab 1: File Upload ──
        with gr.TabItem("📁 Upload File"):
            with gr.Row():
                with gr.Column(scale=1):
                    file_input = gr.File(
                        label="Upload Lecture Slides or Notes",
                        file_types=[".pdf", ".pptx", ".txt"],
                        type="filepath"
                    )
                    analyze_file_btn = gr.Button("🔍 Find My Gaps", variant="primary")

                    gr.HTML("<p style='color:#64748b; font-size:0.85rem; margin-top:12px;'>Supports: PDF, PPTX, TXT</p>")

                with gr.Column(scale=2):
                    file_status = gr.Textbox(
                        label="Status Log",
                        lines=6,
                        interactive=False,
                        elem_classes=["status-box"]
                    )

            file_study_guide = gr.Markdown(label="📖 Study Guide")
            file_flashcards = gr.Markdown(label="🃏 Flashcards")

            analyze_file_btn.click(
                fn=process_file,
                inputs=[file_input],
                outputs=[file_status, file_study_guide, file_flashcards]
            )

        # ── Tab 2: Paste Text ──
        with gr.TabItem("📝 Paste Notes"):
            with gr.Row():
                with gr.Column(scale=1):
                    text_input = gr.Textbox(
                        label="Paste Your Lecture Notes",
                        lines=15,
                        placeholder="Paste your lecture notes or slides text here...",
                        value=SAMPLE_TEXT
                    )
                    analyze_text_btn = gr.Button("🔍 Find My Gaps", variant="primary")

                with gr.Column(scale=2):
                    text_status = gr.Textbox(
                        label="Status",
                        lines=3,
                        interactive=False,
                        elem_classes=["status-box"]
                    )

            text_study_guide = gr.Markdown(label="📖 Study Guide")
            text_flashcards = gr.Markdown(label="🃏 Flashcards")

            analyze_text_btn.click(
                fn=process_text,
                inputs=[text_input],
                outputs=[text_status, text_study_guide, text_flashcards]
            )

    gr.HTML("""
    <div style="text-align:center; color:#475569; font-size:0.8rem; margin-top:24px; padding:16px;">
        Built with LangGraph · MCP · ChromaDB · Groq · Gradio
    </div>
    """)

if __name__ == "__main__":
    port = int(os.getenv("PORT", 7860))
    demo.launch(
        share=False,
        server_name="0.0.0.0",
        server_port=port,
        css=CSS,
        theme=gr.themes.Base()
    )
