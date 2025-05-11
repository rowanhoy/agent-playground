import json
from fastapi import FastAPI
import logfire
import openai
import asyncio

from fastapi.responses import StreamingResponse
from pydantic_ai import Agent
from pydantic_ai.models.openai import OpenAIModel
from pydantic_ai.providers.openai import OpenAIProvider

from app.settings import Settings
from app.models import (
    ChatRequest
)

settings = Settings()

logfire.configure(send_to_logfire='if-token-present')

app = FastAPI()
logfire.instrument_fastapi(app)

client = openai.AsyncOpenAI(
    api_key=settings.GITHUB_MODELS_API_KEY,
    base_url=settings.GITHUB_MODELS_API_URL
)

model = OpenAIModel(
    model_name="openai/gpt-4o-mini",
    provider=OpenAIProvider(openai_client=client),
)

agent = Agent(
    model=model
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