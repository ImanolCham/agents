# Libraries
import gradio as gr
from deep_research import ui

# Priorize .env vs the environment variables
load_dotenv(override=True)

if __name__ == "__main__":
    ui.launch()