from agents import (
    Agent,
    Runner,
    SQLiteSession,
    InputGuardrailTripwireTriggered,
    OutputGuardrailTripwireTriggered,
)
from openai.types.responses import ResponseTextDeltaEvent
import os
import traceback

# Import the Azure OpenAI model configuration
from azure import model

# Import the specialized agents
from Agents.AG_instance_gen import instance_generator_agent
from Agents.AG_vrptw_solver import vrptw_solver_agent
from Agents.AG_code_editor import code_editor_agent
from Agents.AG_visualization import visualization_agent
from Agents.shared_context import get_context

# Import guardrails
from Agents.guardrails import topic_guardrail, safety_guardrail, professional_output_guardrail

import chainlit as cl


# Create the main orchestrator agent that coordinates the specialized agents
orchestrator_agent = Agent(
    name="OR Orchestrator Agent",
    instructions="""You are the main orchestrator for Operations Research problem solving.

You coordinate four specialized agents:
1. **Instance Generator Agent**: Creates and manages VRP problem instances
2. **VRPTW Solver Agent**: Solves Vehicle Routing Problems with Time Windows
3. **Code Editor Agent**: Analyzes and modifies optimization code
4. **Visualization Agent**: Creates visual representations of problems and solutions

When a user asks about:
- Creating/generating VRP instances → Hand off to Instance Generator Agent
- Solving routing problems → Hand off to VRPTW Solver Agent  
- Analyzing/modifying code or generating templates → Hand off to Code Editor Agent
- Visualizing instances or solutions → Hand off to Visualization Agent

For complex tasks that require multiple steps:
1. First generate an instance (if needed)
2. Then solve it
3. Then visualize the results
4. Explain the findings

The agents share context, so data flows automatically between them.

Always provide clear explanations and guide users through the OR workflow.
Be helpful in explaining optimization concepts like time windows, capacity constraints, and routing.""",
    handoffs=[instance_generator_agent, vrptw_solver_agent, code_editor_agent, visualization_agent],
    model=model,
    input_guardrails=[safety_guardrail, topic_guardrail],
    output_guardrails=[professional_output_guardrail]
)



@cl.on_chat_start
async def on_chat_start():
    """
    Creates a new SQLite session for the user and saves it in the user session.
    Also initializes the shared OR context.
    """
    session = SQLiteSession("conversation_history")
    cl.user_session.set("agent_session", session)
    
    # Initialize shared context with workspace path
    ctx = get_context()
    workspace_path = os.path.join(os.path.dirname(__file__), ".files")
    ctx.set_workspace(workspace_path)
    ctx.clear()  # Clear previous session data

@cl.on_chat_end
async def on_chat_end():
    """
    Gets the session back from the user session and closes it. Saves it to the DB.
    """
    session = cl.user_session.get("agent_session")
    if session is not None:
        # close() might not be async, handle both cases
        close_result = session.close()
        if close_result is not None:
            await close_result

@cl.password_auth_callback
def auth_callback(username: str, password: str):
    """
    Simple authentication callback that checks username and password against
    environment variables. Returns a User object if authentication is successful,
    otherwise returns None.

    Args:
        username (str): The username provided by the user.
        password (str): The password provided by the user.
    Returns:
        Optional[cl.User]: A User object if authentication is successful, otherwise None.

    """
    if (username, password) == (
        os.getenv("CHAINLIT_USERNAME"),
        os.getenv("CHAINLIT_PASSWORD"),
    ):
        return cl.User(
            identifier="Student",
            metadata={"role": "student", "provider": "credentials"},
        )
    else:
        return None

@cl.on_message
async def on_message(message: cl.Message):
    """
    Handles incoming messages from the user, runs the orchestrator agent,
    and streams the response back to the user.
    
    Args:
        message (cl.Message): The incoming message from the user.
    
    """
    session = cl.user_session.get("agent_session")

    try:
        result = Runner.run_streamed(
            orchestrator_agent,
            input=message.content,
            session=session
        )

        msg = cl.Message(content="")
        async for event in result.stream_events():
            # Stream final message text to screen
            if event.type == "raw_response_event" and isinstance(
                event.data, ResponseTextDeltaEvent
            ):
                await msg.stream_token(token=event.data.delta)

            elif (
                event.type == "raw_response_event"
                and hasattr(event.data, "item")
                and hasattr(event.data.item, "type")
                and event.data.item.type == "function_call"
                and len(event.data.item.arguments) > 0
            ):
                with cl.Step(name=f"{event.data.item.name}", type="tool") as step:
                    step.input = event.data.item.arguments

        await msg.update()
    
    except InputGuardrailTripwireTriggered as e:
        # Handle input guardrail violations
        guardrail_name = e.guardrail_result.guardrail.name
        output_info = e.guardrail_result.output.output_info
        
        if guardrail_name == "topic_guardrail":
            response = (
                "🚫 **Off-topic request detected**\n\n"
                "I'm specialized in Operations Research problems like:\n"
                "- Vehicle Routing Problems (VRP, VRPTW)\n"
                "- Traveling Salesman Problem (TSP)\n"
                "- Optimization and scheduling\n"
                "- Mathematical programming (LP, MIP)\n\n"
                f"*Reason: {output_info.reasoning}*\n\n"
                "Please ask me about OR-related topics!"
            )
        elif guardrail_name == "safety_guardrail":
            response = (
                "⚠️ **Request blocked for safety reasons**\n\n"
                "I detected content that I cannot process. "
                "Please rephrase your request appropriately.\n\n"
                f"*Reason: {output_info.reasoning}*"
            )
        else:
            response = (
                "⚠️ **Request blocked**\n\n"
                "Your request could not be processed. Please try again."
            )
        
        await cl.Message(content=response).send()
        
    except OutputGuardrailTripwireTriggered as e:
        # Handle output guardrail violations (rare)
        await cl.Message(
            content="⚠️ I generated a response that didn't meet quality standards. "
                    "Please try asking your question differently."
        ).send()
        
    except Exception as e:
        error_msg = f"❌ An error occurred: {str(e)}\n\n```\n{traceback.format_exc()}\n```"
        await cl.Message(content=error_msg).send()

