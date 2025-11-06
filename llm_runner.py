from pydantic import BaseModel
from typing import (
    List,
    AsyncIterator,
    TypedDict,
    Literal,
)
import os
from openai import OpenAI
from dotenv import load_dotenv  # type: ignore

from openai.types.chat import ChatCompletionMessageParam
from thesys_genui_sdk.context import get_assistant_message, write_content
from services import message_service, thread_service

load_dotenv()

# define the client
client = OpenAI(
    api_key=os.getenv("THESYS_API_KEY"),
    base_url="https://api.thesys.dev/v1/embed",
)

# define the prompt type in request
class Prompt(TypedDict):
    role: Literal["user"]
    content: str
    id: str

# define the request type
class ChatRequest(BaseModel):
    prompt: Prompt
    threadId: str
    responseId: str

    class Config:
        extra = "allow"  # Allow extra fields

async def generate_stream(chat_request: ChatRequest):
    # Get messages from database
    db_messages = message_service.get_thread_messages(chat_request.threadId)

    # Convert database messages to OpenAI format
    conversation_history: List[ChatCompletionMessageParam] = [
        {"role": msg["role"], "content": msg["content"]}
        for msg in db_messages
    ]

    # Add the new user message to history
    conversation_history.append(chat_request.prompt)

    # Save user message to database
    message_service.create_message(
        thread_id=chat_request.threadId,
        role=chat_request.prompt['role'],
        content=chat_request.prompt['content'],
        external_id=chat_request.prompt['id']
    )

    assistant_message_for_history: dict | None = None

    stream = client.chat.completions.create(
        messages=conversation_history,
        model="c1/anthropic/claude-sonnet-4/v-20250815",
        stream=True,
    )

    for chunk in stream:
        delta = chunk.choices[0].delta
        finish_reason = chunk.choices[0].finish_reason

        if delta and delta.content:
            await write_content(delta.content)

        if finish_reason:
            assistant_message_for_history = get_assistant_message()

    if assistant_message_for_history:
        conversation_history.append(assistant_message_for_history)

        # Save assistant message to database
        message_service.create_message(
            thread_id=chat_request.threadId,
            role=assistant_message_for_history['role'],
            content=assistant_message_for_history['content'],
            external_id=chat_request.responseId
        )
