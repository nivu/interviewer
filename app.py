import os

import gradio as gr

from llm import end_interview, get_problem, read_last_message, send_request, speech_to_text, test_connection, text_to_speech
from options import fixed_messages, topics_list

default_audio_params = {
    "label": "Record answer",
    "sources": ["microphone"],
    "type": "numpy",
    "waveform_options": {"show_controls": False},
    "editable": False,
    "container": False,
    "show_share_button": False,
}


def hide_settings():
    init_acc = gr.Accordion("Settings", open=False)
    start_btn = gr.Button("Generate a problem", interactive=False)
    solution_acc = gr.Accordion("Solution", open=True)
    end_btn = gr.Button("Finish the interview", interactive=True)
    audio_input = gr.Audio(interactive=True, **default_audio_params)
    return init_acc, start_btn, solution_acc, end_btn, audio_input


def add_interviewer_message(message):
    def f(chat):
        chat.append((None, message))
        return chat

    return f


def hide_solution():
    solution_acc = gr.Accordion("Solution", open=False)
    end_btn = gr.Button("Finish the interview", interactive=False)
    problem_acc = gr.Accordion("Problem statement", open=False)
    audio_input = gr.Audio(interactive=False, **default_audio_params)
    return solution_acc, end_btn, problem_acc, audio_input


with gr.Blocks() as demo:
    with gr.Tab("Instruction") as instruction_tab:
        with gr.Row():
            with gr.Column(scale=10):
                gr.Markdown("# Welcome to the AI Tech Interviewer Training!")
                gr.Markdown(
                    """
                This project leverages the latest AI models to simulate a realistic tech interview experience, 
                allowing you to practice your coding interview skills in an environment that closely mimics the real thing. 
                While it's not designed to replace a human interviewer or the essential steps of interview preparation, such as studying algorithms and practicing coding, 
                it serves as a valuable addition to your preparation arsenal.
                """
                )

                if os.getenv("IS_DEMO"):
                    gr.Markdown(
                        """
                    ### Demo Version Notice
                    **This is a demo version running on limited resources, which may respond slower than usual.**
                    It's primarily for demonstration purposes. 
                    For optimal performance, we recommend running this application on your local machine using your own OpenAI API_KEY or local models. 
                    See the instructions below on how to set up and run this application locally for the best experience.
                    I also recommend to read this introduction page first.
                    If you proceed to the interview interface right now, just click on the 'Coding' tab.
                    """
                    )

                gr.Markdown("### Introduction")
                gr.Markdown("### Setting Up Locally")
                gr.Markdown("### Interview Interface Overview")
                gr.Markdown("### Models Configuration")

            with gr.Column(scale=1):
                try:
                    audio_test = text_to_speech("Handshake")
                    gr.Markdown("TTS status: 🟢")
                except:
                    gr.Markdown("TTS status: 🔴")
                try:
                    text_test = speech_to_text(audio_test, False)
                    gr.Markdown("STT status: 🟢")
                except:
                    gr.Markdown("STT status: 🔴")

                try:
                    test_connection()
                    gr.Markdown("LLM status: 🟢")
                except:
                    gr.Markdown("LLM status: 🔴")

        pass
    with gr.Tab("Coding") as coding_tab:
        chat_history = gr.State([])
        previous_code = gr.State("")
        client = gr.State(None)
        client_started = gr.State(False)
        with gr.Accordion("Settings") as init_acc:
            with gr.Row():
                with gr.Column():
                    gr.Markdown("##### Problem settings")
                    with gr.Row():
                        gr.Markdown("Difficulty")
                        difficulty_select = gr.Dropdown(
                            label="Select difficulty",
                            choices=["Easy", "Medium", "Hard"],
                            value="Medium",
                            container=False,
                            allow_custom_value=True,
                        )
                    with gr.Row():
                        gr.Markdown("Topic (can type custom value)")
                        topic_select = gr.Dropdown(
                            label="Select topic", choices=topics_list, value="Arrays", container=False, allow_custom_value=True
                        )
                with gr.Column(scale=2):
                    requirements = gr.Textbox(label="Requirements", placeholder="Specify additional requirements", lines=5)
                    start_btn = gr.Button("Generate a problem")

        with gr.Accordion("Problem statement", open=True) as problem_acc:
            description = gr.Markdown()
        with gr.Accordion("Solution", open=False) as solution_acc:
            with gr.Row() as content:
                with gr.Column(scale=2):
                    code = gr.Code(
                        label="Please write your code here. Only Python syntax highlighting is available for now.",
                        language="python",
                        lines=35,
                    )
                with gr.Column(scale=1):
                    end_btn = gr.Button("Finish the interview", interactive=False)
                    chat = gr.Chatbot(label="Chat", show_label=False, show_share_button=False)
                    audio_input = gr.Audio(interactive=False, **default_audio_params)
                    audio_output = gr.Audio(label="Play audio", autoplay=True, visible=False)
                    message = gr.Textbox(label="Message", lines=3, visible=False)

        with gr.Accordion("Feedback", open=True) as feedback_acc:
            feedback = gr.Markdown()

    coding_tab.select(fn=add_interviewer_message(fixed_messages["intro"]), inputs=[chat], outputs=[chat])

    start_btn.click(fn=add_interviewer_message(fixed_messages["start"]), inputs=[chat], outputs=[chat]).then(
        fn=get_problem,
        inputs=[requirements, difficulty_select, topic_select],
        outputs=[description, chat_history],
        scroll_to_output=True,
    ).then(fn=hide_settings, inputs=None, outputs=[init_acc, start_btn, solution_acc, end_btn, audio_input])

    message.submit(
        fn=send_request,
        inputs=[code, previous_code, message, chat_history, chat],
        outputs=[chat_history, chat, message, previous_code],
    )

    end_btn.click(
        fn=add_interviewer_message(fixed_messages["end"]),
        inputs=[chat],
        outputs=[chat],
    ).then(
        fn=end_interview, inputs=[description, chat_history], outputs=feedback
    ).then(fn=hide_solution, inputs=None, outputs=[solution_acc, end_btn, problem_acc, audio_input])

    audio_input.stop_recording(fn=speech_to_text, inputs=[audio_input], outputs=[message]).then(
        fn=lambda: None, inputs=None, outputs=[audio_input]
    ).then(
        fn=send_request,
        inputs=[code, previous_code, message, chat_history, chat],
        outputs=[chat_history, chat, message, previous_code],
    )

    chat.change(fn=read_last_message, inputs=[chat], outputs=[audio_output])

    audio_output.stop(fn=lambda: None, inputs=None, outputs=[audio_output])

demo.launch(show_api=False)
