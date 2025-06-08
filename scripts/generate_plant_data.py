import os
import boto3
import json
import time

# AWS Bedrock -asetukset
BEDROCK_REGION = os.environ.get("BEDROCK_REGION", "us-east-1")

ACCOUNT_ID = boto3.client("sts").get_caller_identity()["Account"]
MODEL_ID = f"arn:aws:bedrock:{BEDROCK_REGION}:{ACCOUNT_ID}:inference-profile/us.anthropic.claude-3-5-sonnet-20241022-v2:0"

bedrock = boto3.client("bedrock-runtime", region_name=BEDROCK_REGION)

plants = [
    "Viirivehka",
    "Kultaköynnös",
    "Rönsylilja",
    "Palmuvehka",
    "Anopinkieli",
    "Käärmekaktus",
]


def generate_plant_care_bedrock_with_sources(plant_name):
    prompt = f"""
Kirjoita suomeksi hoito-ohjeet seuraavalle kasville:

Kasvi: {plant_name}

Muodosta vastaus JSON-muodossa, kentät:
kasvin_nimi, tieteellinen_nimi, hoitoohjeet, valo, kastelu, multa, lämpötila, kosteus, lisävinkit, lahteet.

'lahteet' on lista tai teksti, joka kertoo mistä tiedot on haettu (esim. kirjallisuus, nettisivut, tutkimukset).

Vastaa vain JSON-objektina.
"""
    conversation = [{"role": "user", "content": [{"text": prompt}]}]

    try:
        response = bedrock.converse(
            modelId=MODEL_ID,
            messages=conversation,
            inferenceConfig={
                "maxTokens": 1024,
                "temperature": 0.5,
                "topP": 0.9,
            },
        )

        message = response["output"]["message"]
        text = message["content"][0]["text"]

        plant_data = json.loads(text)
        return plant_data

    except json.JSONDecodeError:
        print(f"JSON-parsing epäonnistui kasville {plant_name}. Vastaus:")
        print(text)
        return None
    except Exception as e:
        print(f"Virhe Bedrock-kyselyssä kasville {plant_name}: {str(e)}")
        return None


def main():
    dataset = []
    for plant in plants:
        print(f"Generoin hoito-ohjeet kasville: {plant}...")
        data = generate_plant_care_bedrock_with_sources(plant)
        if data:
            dataset.append(data)
        time.sleep(2)  # Tauko API-kutsujen välillä

    with open("huonekasvit_hoito_lahteet.json", "w", encoding="utf-8") as f:
        json.dump(dataset, f, ensure_ascii=False, indent=2)

    print("Datasetti tallennettu tiedostoon huonekasvit_hoito_lahteet.json")


if __name__ == "__main__":
    main()
