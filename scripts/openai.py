import os
from dotenv import load_dotenv
import openai

# Load environment variables for API key
load_dotenv()
openai.api_key = os.getenv("OPENAI_API_KEY")


def describe_project(readme_path: str) -> str:
    """
    Summarizes the entire project based on the README.md file.
    """
    with open(readme_path, encoding="utf-8") as f:
        readme = f.read()
    system = (
        "You are an expert software documentation assistant. "
        "Given a project's README markdown, produce a concise overview "
        "in user-friendly language, covering: what the project does, "
        "its goals, and its main features (visualisations, forecasting model, map)."
    )
    user = f"Here is the project's README:\n\n```markdown\n{readme}\n```"
    resp = openai.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": system},
            {"role": "user",   "content": user}
        ],
        temperature=0.7,
        max_tokens=300
    )
    return resp.choices[0].message.content.strip()


def describe_chart(fig, title: str = "") -> str:
    """
    Given a Plotly figure object, returns a human-readable description.
    """
    fig_json = fig.to_dict()
    system = (
        "You are a data visualization assistant. "
        "Given the JSON spec of a Plotly chart, return a concise, "
        "user-friendly description of what the chart shows."
        "Explain what tendentious we can see in the chart."
    )
    user = f"Chart title: {title}\n\n```json\n{fig_json}\n```"
    resp = openai.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": system},
            {"role": "user",   "content": user}
        ],
        temperature=0.3,
        max_tokens=100
    )
    return resp.choices[0].message.content.strip()

