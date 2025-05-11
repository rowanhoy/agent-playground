import json
from fastapi import FastAPI
import logfire
import openai
import asyncio

from fastapi.responses import StreamingResponse
from pydantic_ai import Agent
from pydantic_ai.models.openai import OpenAIModel
from pydantic_ai.providers.openai import OpenAIProvider
from pydantic_ai.models.gemini import GeminiModel
from pydantic_ai.providers.google_gla import GoogleGLAProvider
from pydantic_ai.mcp import MCPServerHTTP

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

client = openai.AsyncOpenAI(
    api_key=settings.GITHUB_MODELS_API_KEY,
    base_url=settings.GITHUB_MODELS_API_URL
)

openai_model = OpenAIModel(
    model_name="openai/gpt-4.1",
    provider=OpenAIProvider(openai_client=client),
)

gemini_provider = GoogleGLAProvider(api_key=settings.GEMINI_API_KEY)

gemini_model = GeminiModel('gemini-2.5-flash-preview-04-17', provider=gemini_provider)

agent = Agent(
    model=gemini_model,
    mcp_servers=[server],
    system_prompt="You are a generic agent that answers questions on any and all topics. You will have access to tools, but you do not need to use them, not should you limit your responses to the scope of the tools"
)

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

@app.post('/mock_chat')
async def post_mock_chat(
    chat_request: ChatRequest,
) -> StreamingResponse:
    """
    Mock chat with the model.
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

        #return a static message over 4 seconds
        async def static_message():
            for i in range(8):
                yield f"this is a static message part {i}\n"
                await asyncio.sleep(1)
        async for text in static_message():
            yield f"0:{json.dumps(text)}\n"
    
    return StreamingResponse(
        stream_message(),
        media_type="text/event-stream"
    )