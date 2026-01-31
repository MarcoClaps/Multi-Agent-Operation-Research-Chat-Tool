import os
import dotenv
import httpx
from openai import AsyncAzureOpenAI
from agents import (
    OpenAIChatCompletionsModel,
    set_default_openai_client,
    set_tracing_disabled,
)

dotenv.load_dotenv()

# Configure custom timeout (default is 60 seconds, increasing to 120)
timeout = httpx.Timeout(
    timeout=240.0,  # Total timeout
    connect=60.0,   # Connection timeout (was causing the issue)
)

# Configure OpenAI Azure client with increased timeout
azure = AsyncAzureOpenAI(
    api_key=os.environ["AZURE_OPENAI_API_KEY"],
    api_version=os.environ.get("AZURE_OPENAI_API_VERSION", "2024-12-01-preview"),
    azure_endpoint=os.environ[
        "AZURE_OPENAI_ENDPOINT"
    ],
    timeout=timeout,
)
set_tracing_disabled(True)
set_default_openai_client(azure)

model = OpenAIChatCompletionsModel(
    model=os.environ["AZURE_OPENAI_DEPLOYMENT"], openai_client=azure
)
