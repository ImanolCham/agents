import gradio as gr
from dotenv import load_dotenv
from research_manager import ResearchManager
from perfume_db import get_perfume_info   # 👈 nuevo

load_dotenv(override=True)

async def run(query: str):
    async for chunk in ResearchManager().run(query):
        yield chunk

with gr.Blocks(theme=gr.themes.Default(primary_hue="sky")) as ui:
    gr.Markdown("# Deep Research")

    query_textbox = gr.Textbox(
        label="What perfum is the one you are using right now or the one you would like to buy?"
    )
    run_button = gr.Button("Run", variant="primary")
    report = gr.Markdown(label="Report")
    
    run_button.click(fn=run, inputs=query_textbox, outputs=report)
    query_textbox.submit(fn=run, inputs=query_textbox, outputs=report)

    # 🔽🔽 TODO ESTO ES LO NUEVO: lookup directo al CSV
    gr.Markdown("## Look up a perfume from the Kaggle dataset")

    with gr.Row():
        perfume_name_input = gr.Textbox(label="Perfume name (approximate is ok)")
        show_button = gr.Button("Show perfume info")

    with gr.Row():
        perfume_image = gr.Image(label="Bottle", interactive=False)
        perfume_info_html = gr.HTML(label="Description & Notes")

    def show_info(name: str):
        info = get_perfume_info(name)
        if info is None:
            return None, "<p>No he encontrado ese perfume en la base de datos.</p>"
        return info["image_url"], info["html"]

    show_button.click(
        fn=show_info,
        inputs=perfume_name_input,
        outputs=[perfume_image, perfume_info_html],
    )
