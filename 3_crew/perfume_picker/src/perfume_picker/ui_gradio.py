import gradio as gr
from datetime import datetime
from perfume_picker.crew import PerfumePicker


def run_perfume_picker(user, likes, dislikes, budget, notes):
    inputs = {
        "user": user,
        "query": query,
        "budget": budget,
        "current_date": datetime.now().astimezone().isoformat()
    }

    picker = PerfumePicker()
    crew = picker.crew()
    result = crew.kickoff(inputs=inputs)

    raw = getattr(result, "raw", str(result))
    pyd = getattr(result, "pydantic", None)

    return raw, (pyd.model_dump() if pyd else {})


def build_ui():
    with gr.Blocks() as demo:
        gr.Markdown("# Perfume Picker (CrewAI)")

        with gr.Row():
            user = gr.Textbox(label="Usuario", value="John Pork")
            budget = gr.Number(label="Presupuesto (€)", value=100)

        likes = gr.Textbox(label="Qué te gusta")
        dislikes = gr.Textbox(label="Qué no te gusta")
        notes = gr.Textbox(label="Referencia o notas extra")

        btn = gr.Button("Recomendar")
        out_text = gr.Textbox(label="Resultado", lines=18)
        out_json = gr.JSON(label="Resultado estructurado")

        btn.click(
            fn=run_perfume_picker,
            inputs=[user, likes, dislikes, budget, notes],
            outputs=[out_text, out_json]
        )

    return demo


if __name__ == "__main__":
    demo = build_ui()
    demo.launch()
