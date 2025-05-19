import os
from dotenv import load_dotenv
import openai

# Load environment variables for API key
load_dotenv()
openai.api_key = os.getenv("OPENAI_API_KEY")

"""
Summarizes the entire project based on README.md.
"""
def describe_project(readme_path: str = None) -> str:

    # 1. auto-locate README if no path given
    if readme_path is None:
        readme_path = os.path.abspath(
            os.path.join(os.path.dirname(__file__), '..', 'README.md')
        )

    # 2. read the file
    try:
        with open(readme_path, encoding="utf-8") as f:
            readme = f.read()
    except FileNotFoundError:
        return "[ERROR] README.md not found at " + readme_path

    system = (
        "Tu esi programinės įrangos dokumentacijos ekspertas. "
        "Remdamiesi projekto README Markdown, parengkite glaustą, "
        "vartotojui draugišką apžvalgą, kurioje būtų aptarta:, "
        "ką projektas daro, kokie jo tikslai ir kokios pagrindinės funkcijos "
        "(vizualizacijos, prognozavimo modelis, žemėlapis)."
    )
    user = f"Here is the project's README:\n\n```markdown\n{readme}\n```"

    try:
        resp = openai.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": system},
                {"role": "user",   "content": user}
            ],
            temperature=0.7
        )
        return resp.choices[0].message.content.strip()
    except Exception as ex:
        return f"[ERROR] {ex}"

"""
Given a Plotly figure object, returns a  description of a graph.
"""
def describe_chart(fig, title: str = "") -> str:

    fig_json = fig.to_dict()
    system = (
        "Tu esi duomenų vizualizacijų asistentas. "
        "Remdamasis Plotly diagramos JSON specifikacija, "
        "pateik glaustą ir vartotojui draugišką aprašymą, ką diagrama vaizduoja. "
        "Paaiškink, kokias tendencijas galima pastebėti diagramoje. "
        "Stenkis viską paaiškinti 2–3 sakiniais."
    )
    user = f"Chart title: {title}\n\n```json\n{fig_json}\n```"
    resp = openai.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": system},
            {"role": "user",   "content": user}
        ],
        temperature=0.3,
    )
    return resp.choices[0].message.content.strip()
