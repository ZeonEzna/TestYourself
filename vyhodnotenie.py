import openai
import os

# You need to have the OpenAI API key set as an environment variable
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

def read_results(file_path):
    with open(file_path, 'r', encoding='utf-8') as f:
        return f.read()

def analyze_results(results_text):
    """
    Uses OpenAI's API to analyze the test results and generate a detailed personality and performance report.
    """
    prompt = f"""
Vstupné údaje z testov:
{results_text}

Na základe vyššie uvedených čiastočných výsledkov testov vykonaj nasledovné:
- Vytvor komplexné, rozsiahle vyhodnotenie osobnosti človeka, ktorý absolvoval tieto testy.
- Identifikuj silné a slabé stránky, typické chyby, vedomostnú a inteligenčnú úroveň v porovnaní s priemernou populáciou.
- Uveď objektívnu analýzu doteraz získaných výsledkov.
- Ak je údajov málo, upozorni na potrebu ďalších testov pre detailnejší profil.
- Výstup by mal byť veľmi detailný, profesionálny, objektívny a analytický, vhodný ako podklad pre osobnostné hodnotenie kandidáta.

Komplexné vyhodnotenie:
"""
    response = openai.Completion.create(
        engine="gpt-4",  # alebo iný dostupný engine
        prompt=prompt,
        max_tokens=1200,
        temperature=0.7,
        api_key=OPENAI_API_KEY
    )
    return response.choices[0].text.strip()

def main():
    vstup = "result.txt"
    if not os.path.exists(vstup):
        print("Súbor result.txt nie je prítomný.")
        return
    vysledky = read_results(vstup)
    hodnotenie = analyze_results(vysledky)
    with open("vyhodnotenie.txt", "w", encoding="utf-8") as f:
        f.write(hodnotenie)
    print("Komplexné vyhodnotenie bolo uložené do vyhodnotenie.txt")

if __name__ == "__main__":
    main()
