from pydantic_ai import Agent
from pydantic_ai.mcp import MCPServerHTTP

import json
from fastapi import FastAPI
import logfire

from fastapi.responses import StreamingResponse
from pydantic_ai import Agent
from pydantic_ai.mcp import MCPServerHTTP
from pydantic_ai.models.gemini import GeminiModel
from pydantic_ai.providers.google_gla import GoogleGLAProvider

from app.settings import Settings
from app.models import (
    ChatRequest
)

import os

settings = Settings()

os.environ['OTEL_EXPORTER_OTLP_TRACES_ENDPOINT'] = settings.OTEL_EXPORTER_OTLP_TRACES_ENDPOINT

logfire.configure(
        send_to_logfire=False,
        service_name='pydantic'
    )

logfire.instrument_pydantic_ai()
Agent.instrument_all()

app = FastAPI()
logfire.instrument_fastapi(app)

server = MCPServerHTTP(url='http://localhost:5008/sse')
model = GeminiModel(settings.GEMINI_MODEL, provider=GoogleGLAProvider(api_key=settings.GEMINI_API_KEY))

system_prompt = """
You are a generic agent that answers questions on any and all topics. 
You will have access to tools, but you do not need to use them, nor should you limit your responses to the scope of the tools.
If you use tools, you should wait for them to complete before responding to the user.
When using azure tools, before asking the user for a subscription, you should first fetch the available subscriptions and present them to the user.
If there is only one subscription, you should use that one without asking the user.
"""

agent = Agent(
    model=model,
    mcp_servers=[server],
    system_prompt=system_prompt)

@app.post('/chat')
async def post_chat(
    chat_request: ChatRequest,
) -> StreamingResponse:
    """
    Chat with the model.
    - message: The message to send to the model.
    - history: The history of the conversation in the form of a list of ModelMessage objects. Passing None will start a new conversation.
    """
    async def stream_message():
        """
        Streams line delimited messages to the client as they are generated, all lines are prefixed with with of the following codes:
        - 0: message part [string]
        - e: error [json]
        - h: history [json]
        - s: system [json]
        - c: chain of thought part [string]

        for example:
        0:"this is a "
        0:"message part"
        s:{"model":"gpt-3.5-turbo","temperature":0.7,"top_p":1,"frequency_penalty":0,"presence_penalty":0,"stop":["\n"]}
        """
        async with agent.run_mcp_servers():
            async with agent.run_stream(
                user_prompt=chat_request.message,
                message_history=chat_request.history
            ) as result:
                async for text in result.stream_text(debounce_by=0.1, delta=True):
                    yield f"0:{json.dumps(text)}\n"
                yield f"h:{result.all_messages_json().decode()}\n"
    
    return StreamingResponse(
        stream_message(),
        media_type="text/event-stream"
    )
