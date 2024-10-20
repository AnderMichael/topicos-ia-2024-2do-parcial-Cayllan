import gradio as gr
from ai_assistant.prompts import agent_prompt_tpl
from ai_assistant.agent import TravelAgent

agent = TravelAgent(agent_prompt_tpl).get_agent()


def reset_chat():
    agent.reset()
    return "", "", ""


def agent_response(message, history):
    return agent.chat(
        f"{message},\nUtiliza las herramientas travel_guide si se requiere información\nUsar bus_tool, flight_tool, restaruant_tool, hotel_tool si se requiere hacer una reservación\nFinalmente usa trip_summary para obtener el informe y/o planificación de mi viaje"
    ).response


if __name__ == "__main__":
    # Initialize the chat interface with the agent response function
    demo = gr.ChatInterface(fn=agent_response, type="messages")
    demo.launch()
