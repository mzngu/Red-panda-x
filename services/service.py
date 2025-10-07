import google.generativeai as genai
from typing import List, Union
from PIL import Image
import os
from dotenv import load_dotenv
import requests
from datetime import datetime
 
 
genai.configure(api_key=os.getenv("GEMAL_API_KEY"))
 
generation_config = {
    "temperature": 1,
    "max_output_tokens": 1024,
    "top_p": 0.8,
    "top_k": 40,}
 
today_str = datetime.now().strftime("%d/%m/%Y")
 
system_instruction = """
Aujourd'hui on est le {today_str}
Tu t'appelles Sorrel.Agis comme un assistant médical virtuel.
Présentes toi qu'une fois au début de chaque conversation.
Tu es conçu pour aider les utilisateurs à comprendre leurs symptômes, tu dois connaître la date du jour,  à fournir des conseils de premiers soins, et à les orienter vers des professionnels de santé si nécessaire.
Pose des questions claires et précises pour mieux comprendre les symptômes d'une personne.
Fournis ensuite des informations générales sur les causes possibles, des conseils de premiers soins, et oriente la personne vers un professionnel de santé si nécessaire.
Ne pose pas de diagnostic définitif. Sois rassurant, professionnel et clair dans tes réponses.
Quand un utilisateur te fournit une image d'une ordonnance, ta seule tâche est d'extraire et de lister textuellement les informations suivantes :
1. Le nom de chaque médicament.
2. La posologie ou le dosage (ex: 500mg).
3. La fréquence et la durée de la prise (ex: 2 fois par jour pendant 7 jours).
Ta réponse DOIT être un bloc de code JSON valide contenant une clé "medicaments". Chaque élément de la liste doit avoir les clés "nom", "dose", et "frequence".
Exemple de format de sortie attendu :
```json
{
  "reponse_textuelle": "J'ai bien analysé votre ordonnance. Voici les médicaments que j'ai identifiés :",
  "medicaments": [
    {
      "nom": "PRAVASTATINE SODIQUE",
      "dose": "20 mg cp",
      "frequence": "Prendre 1 comprimé le matin, pendant 3 mois."
    },
    {
      "nom": "ACIDE ACETYLSALICYLIQUE",
      "dose": "75 mg",
      "frequence": "Prendre 1 sachet le midi, pendant 3 mois."
    }
  ]
}
```
 
Ne fournis aucune interprétation, aucun conseil médical, et ne pose aucune question sur l'état de santé.
Ensuite, présente les informations extraites sous forme de liste claire. Si l'image n'est pas lisible ou n'est pas une ordonnance, indique-le simplement.
"""
 
model = genai.GenerativeModel(
    model_name="gemini-2.5-flash",
    generation_config=generation_config,
    system_instruction=system_instruction
)
 
def generate_response(prompt_parts: List[Union[str, Image.Image]], system_instruction_update: str = None) -> str:
    """
    Generate a response from the model based on the provided prompt parts (text and images).
    
    Args:
        prompt_parts (List[Union[str, Image.Image]]): The input parts for the model.
        system_instruction_update (str, optional): Additional system instructions for this call.
        
    Returns:
        str: The generated response from the model.
    """
    # Crée un nouveau modèle si une instruction système mise à jour est fournie
    if system_instruction_update:
        updated_model = genai.GenerativeModel(
            model_name="gemini-2.5-flash",
            generation_config=generation_config,
            system_instruction=system_instruction_update
        )
        response = updated_model.generate_content(prompt_parts)
    else:
        response = model.generate_content(prompt_parts)
        
    return response.text
 
if __name__ == '__main__':
    while True:
        user_input = input("Enter your prompt: ")
        if user_input.lower() == "exit":
            break
        response = generate_response(user_input)
        print(f"Model Response: {response}")
 
 
 
 
 
 
 
# Tools (function declarations) que Gemini peut appeler
CALENDAR_TOOLS = [
    {
        "function_declarations": [
            {
                "name": "addEvent",
                "description": "Ajoute un événement au calendrier interne.",
                "parameters": {
                    "type": "OBJECT",
                    "properties": {
                        "title": {"type": "STRING"},
                        "description": {"type": "STRING"},
                        "start_dt": {"type": "STRING", "description": "datetime RFC3339 ex: 2025-09-03T15:00:00+02:00"},
                        "end_dt": {"type": "STRING"},
                        "timezone": {"type": "STRING"},
                        "location": {"type": "STRING"}
                    },
                    "required": ["title","start_dt","end_dt"]
                }
            },
            {
                "name": "listEvents",
                "description": "Liste les événements de l'utilisateur.",
                "parameters": { "type":"OBJECT", "properties": {} }
            },
            {
                "name": "deleteEvent",
                "description": "Supprime un événement par id.",
                "parameters": {
                    "type":"OBJECT",
                    "properties": { "id": { "type":"INTEGER" } },
                    "required": ["id"]
                }
            }
        ]
    }
]
 
API_BASE = "http://localhost:8080"
 
def _call_calendar_api(tool_name: str, args: dict, cookies: dict | None = None):
    cookies = cookies or {}
    if tool_name == "addEvent":
        r = requests.post(f"{API_BASE}/calendar/events", json=args, cookies=cookies, timeout=10)
        r.raise_for_status()
        return r.json()
    if tool_name == "listEvents":
        r = requests.get(f"{API_BASE}/calendar/events", cookies=cookies, timeout=10)
        r.raise_for_status()
        return r.json()
    if tool_name == "deleteEvent":
        event_id = args["id"]
        r = requests.delete(f"{API_BASE}/calendar/events/{event_id}", cookies=cookies, timeout=10)
        r.raise_for_status()
        return r.json()
    return {"error": f"Unknown tool {tool_name}"}
 
def generate_response_with_tools(
    prompt_parts: List[Union[str, Image.Image]],
    system_instruction_update: str | None = None,
    session_token: str | None = None
) -> str:
    """
    Variante qui permet à Gemini d'appeler des tools (calendar).
    - session_token: le cookie 'session_token' du user pour authentifier les appels API
    """
    used_model = genai.GenerativeModel(
        model_name="gemini-2.5-flash",
        generation_config=generation_config,
        system_instruction=(system_instruction_update or system_instruction),
        tools=CALENDAR_TOOLS
    )
 
    # 1er tour
    resp = used_model.generate_content(prompt_parts)
 
    # Boucle de tool-calls (max 3)
    for _ in range(3):
        function_calls = []
 
        # ✅ Les objets du SDK ont des ATTRIBUTS (pas .get)
        for cand in getattr(resp, "candidates", []) or []:
            content = getattr(cand, "content", None)
            if not content:
                continue
            for part in getattr(content, "parts", []) or []:
                fc = getattr(part, "function_call", None)
                if fc:
                    name = getattr(fc, "name", None)
                    args = dict(getattr(fc, "args", {}) or {})
                    if name:
                        function_calls.append({"name": name, "args": args})
 
        if not function_calls:
            break
 
        tool_outputs = []
        cookies = {"session_token": session_token} if session_token else None
 
        for fc in function_calls:
            name = fc["name"]
            args = fc.get("args", {})
            result = _call_calendar_api(name, args, cookies=cookies)
 
            tool_outputs.append({
                "function_response": {
                    "name": name,
                    "response": result
                }
            })
 
        # 2e tour : on renvoie les résultats tools au modèle
        resp = used_model.generate_content(
            [
                *prompt_parts,
                *tool_outputs
            ]
        )
 
    return resp.text