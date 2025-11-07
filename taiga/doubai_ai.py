from openai import OpenAI


API_KEY = "01418fc1-36f3-4962-8fca-c5b20d1ebbb5"

client = OpenAI(
    base_url="https://ark.cn-beijing.volces.com/api/v3/bots",
    api_key=API_KEY,
)

def ask_once(question: str, prompt: str) -> str:
    """
    入参: question, prompt
    出参: return_message (纯文本)
    """
    resp = client.chat.completions.create(
        model="bot-20251029054843-d8tv6",
        messages=[
            {"role": "system", "content": prompt},
            {"role": "user", "content": question},
        ],
    )
    return_message = resp.choices[0].message.content or ""
    return return_message
