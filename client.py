import os

from dotenv import load_dotenv
from mistralai.client import Mistral
from mistralai.client.utils import BackoffStrategy, RetryConfig

RELANCE = RetryConfig("backoff", BackoffStrategy(1000, 60000, 1.5, 300000), False)

load_dotenv()
client = Mistral(api_key=os.getenv("MISTRAL_API_KEY"), retry_config=RELANCE)
