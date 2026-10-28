import os
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()
client = OpenAI(base_url=os.environ["MODEL_BASE_URL"], api_key=os.environ["MODEL_API_KEY"])
for m in client.models.list():
    print(m.id)