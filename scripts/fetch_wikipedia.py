import requests
import boto3
import os
import json
import time
import botocore.exceptions

# Bedrock client
bedrock = boto3.client(
    "bedrock-runtime", region_name=os.environ.get("BEDROCK_REGION", "us-east-1")
)
ACCOUNT_ID = boto3.client("sts").get_caller_identity()["Account"]
MODEL_ID = f"arn:aws:bedrock:us-east-1:{ACCOUNT_ID}:inference-profile/us.anthropic.claude-3-5-sonnet-20241022-v2:0"


def fetch_wikipedia_extract(title: str, lang="fi") -> str:
    url = f"https://{lang}.wikipedia.org/api/rest_v1/page/summary/{title}"
    resp = requests.get(url)
    if resp.status_code == 200:
        data = resp.json()
        return data.get("extract", "")
    return ""


def query_bedrock_for_care_instructions_with_retry(
    plant_name: str, scientific_name: str, raw_text: str, max_retries=5, base_delay=1
):
    prompt = f"""
Anna hoito-ohjeet seuraavalle huonekasville JSON-muodossa seuraavien kenttien kanssa:

kasvin_nimi, tieteellinen_nimi, hoitoohjeet, valo, kastelu, multa, lämpötila, kosteus, lisävinkit (lista), lähteet (lista).

Käytä selkeää ja ytimekästä suomea.

Kasvin nimi: {plant_name}
Tieteellinen nimi: {scientific_name}
Wikipedia-artikkelin tiivistelmä:
{raw_text}

Vastaa vain JSON-muodossa, älä muuta rakennetta.
"""
    for attempt in range(1, max_retries + 1):
        try:
            response = bedrock.converse(
                modelId=MODEL_ID,
                messages=[{"role": "user", "content": [{"text": prompt}]}],
                inferenceConfig={"maxTokens": 1024, "temperature": 0.5, "topP": 0.9},
            )
            result = response["output"]["message"]
            if "content" in result and result["content"]:
                text = result["content"][0]["text"]
                try:
                    return json.loads(text)
                except json.JSONDecodeError:
                    print("Virhe JSON:in purussa. Vastauksena saatu:")
                    print(text)
                    return {}
            else:
                return {}
        except botocore.exceptions.ClientError as e:
            if e.response["Error"]["Code"] == "ThrottlingException":
                delay = base_delay * (2 ** (attempt - 1))  # eksponentiaalinen backoff
                print(
                    f"ThrottlingException: Yritetään uudelleen {attempt}/{max_retries} yritys {delay} sekunnin kuluttua..."
                )
                time.sleep(delay)
            else:
                # Jos virhe on joku muu, heitä se uudelleen
                raise
    print("Maksimiyritykset saavutettu, pyyntö epäonnistui.")
    return {}


def main():
    kasvilista = [
        {"nimi": "Käärmekaktus", "tieteellinen": "Disocactus flagelliformis"},
        {"nimi": "Viherkasvi", "tieteellinen": ""},
        {"nimi": "Rönsylilja", "tieteellinen": "Chlorophytum comosum"},
        {"nimi": "Jadeplant", "tieteellinen": "Crassula ovata"},
        {"nimi": "Palmuvehka", "tieteellinen": "Zamioculcas zamiifolia"},
        {"nimi": "Ficus benjamina", "tieteellinen": "Ficus benjamina"},
        {"nimi": "Monstera", "tieteellinen": "Monstera deliciosa"},
        {"nimi": "Anopinkieli", "tieteellinen": "Sansevieria trifasciata"},
        {"nimi": "Kultaköynnös", "tieteellinen": "Epipremnum aureum"},
        {"nimi": "Muratti", "tieteellinen": "Hedera helix"},
    ]

    tulokset = []

    for kasvi in kasvilista:
        print(f"Hakee Wikipedia-artikkelin: {kasvi['nimi']}")
        teksti = fetch_wikipedia_extract(kasvi["nimi"])
        if not teksti:
            print(f"Ei löytynyt tietoa kasville {kasvi['nimi']}.")
            continue

        ohjeet = query_bedrock_for_care_instructions_with_retry(
            kasvi["nimi"], kasvi["tieteellinen"], teksti
        )
        if ohjeet:
            tulokset.append(ohjeet)

    print(json.dumps(tulokset, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
