from typing import Any, List, Tuple
from io import StringIO
import functools
import sys

import gradio as gr
from ai_assistant.prompts import agent_prompt_tpl
from ai_assistant.agent import TravelAgent

agent = TravelAgent(agent_prompt_tpl).get_agent()

class Capturing(list):
    """To capture the stdout from ReActAgent.chat with verbose=True. Taken from
    https://stackoverflow.com/questions/16571150/\
        how-to-capture-stdout-output-from-a-python-function-call.
    """

    def __enter__(self) -> Any:
        self._stdout = sys.stdout
        sys.stdout = self._stringio = StringIO()
        return self

    def __exit__(self, *args) -> None:
        self.extend(self._stringio.getvalue().splitlines())
        del self._stringio  # free up some memory
        sys.stdout = self._stdout

class GradioTravelAgentPack():
    """Gradio chatbot to chat with a ReActAgent pack."""

    def __init__(
        self,
        agent : TravelAgent,
        **kwargs: Any,
    ) -> None:
        """Init params."""
        try:
            from ansi2html import Ansi2HTMLConverter
        except ImportError:
            raise ImportError("Please install ansi2html via `pip install ansi2html`")
        
        self.agent = agent
        
        self.thoughts = ""
        self.conv = Ansi2HTMLConverter()


    def _handle_user_message(self, user_message, history):
        """Handle the user submitted message. Clear message box, and append
        to the history.
        """
        return "", [*history, (user_message, "")]

    def _generate_response(
        self, chat_history: List[Tuple[str, str]]
    ) -> Tuple[str, List[Tuple[str, str]]]: # type: ignore
        """Generate the response from agent, and capture the stdout of the
        ReActAgent's thoughts.
        """
        with Capturing() as output:
            response = self.agent.chat(chat_history[-1][0])
        ansi = "\n========\n".join(output)
        html_output = self.conv.convert(ansi)
        for token in response.response_gen:
            chat_history[-1][1] += token
            yield chat_history, str(html_output)

    def _reset_chat(self) -> Tuple[str, str]:
        """Reset the agent's chat history. And clear all dialogue boxes."""
        # clear agent history
        self.agent.reset()
        return "", "", ""  # clear textboxes

    def run(self, *args: Any, **kwargs: Any) -> Any:
        """Run the pipeline."""
        import gradio as gr

        demo = gr.Blocks(
            theme="gstaff/xkcd",
            css="#box { height: 420px; overflow-y: scroll !important}",
        )
        with demo:
            gr.Markdown(
                "# Gradio ReActAgent Powered by LlamaIndex and LlamaHub 🦙\n"
                "This Gradio app is powered by LlamaIndex's `ReActAgent` with\n"
                "OpenAI's GPT-4-Turbo as the LLM. The tools are listed below.\n"
                "## Tools\n"
                "- [ArxivToolSpec](https://llamahub.ai/l/tools-arxiv)\n"
                "- [WikipediaToolSpec](https://llamahub.ai/l/tools-wikipedia)"
            )
            with gr.Row():
                chat_window = gr.Chatbot(
                    label="Message History",
                    scale=3,
                )
                console = gr.HTML(elem_id="box")
            with gr.Row():
                message = gr.Textbox(label="Write A Message", scale=4)
                clear = gr.ClearButton()

            message.submit(
                self._handle_user_message,
                [message, chat_window],
                [message, chat_window],
                queue=False,
            ).then(
                self._generate_response,
                chat_window,
                [chat_window, console],
            )
            clear.click(self._reset_chat, None, [message, chat_window, console])

        demo.launch()


if __name__ == "__main__":
    GradioTravelAgentPack(agent=agent).run()
