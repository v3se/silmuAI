from SPARQLWrapper import SPARQLWrapper, JSON
import pandas as pd


def fetch_houseplants_strict():
    sparql = SPARQLWrapper("https://query.wikidata.org/sparql")
    query = """
SELECT DISTINCT ?plant ?plantLabel WHERE {
  ?plant wdt:P31 wd:Q152740 .  # instance of houseplant
  SERVICE wikibase:label { bd:serviceParam wikibase:language "fi,en". }
}
LIMIT 100
    """

    sparql.setQuery(query)
    sparql.setReturnFormat(JSON)
    results = sparql.query().convert()

    plants = []
    bindings = results.get("results", {}).get("bindings", [])
    for result in bindings:
        plant_uri = result.get("plant", {}).get("value", "")
        plant_label = result.get("plantLabel", {}).get("value", "")
        plants.append(
            {
                "URI": plant_uri,
                "Name": plant_label,
            }
        )

    df = pd.DataFrame(plants)
    return df


def fetch_houseplants_broad():
    sparql = SPARQLWrapper("https://query.wikidata.org/sparql")
    query = """
SELECT DISTINCT ?plant ?plantLabel WHERE {
  ?plant wdt:P31/wdt:P279* wd:Q16521 .  # instance of (subclass of) plant
  ?plant wdt:P366 wd:Q152740 .          # use (P366) houseplant (Q152740)
  SERVICE wikibase:label { bd:serviceParam wikibase:language "fi,en". }
}
LIMIT 100
    """

    sparql.setQuery(query)
    sparql.setReturnFormat(JSON)
    results = sparql.query().convert()

    plants = []
    bindings = results.get("results", {}).get("bindings", [])
    for result in bindings:
        plant_uri = result.get("plant", {}).get("value", "")
        plant_label = result.get("plantLabel", {}).get("value", "")
        plants.append(
            {
                "URI": plant_uri,
                "Name": plant_label,
            }
        )

    df = pd.DataFrame(plants)
    return df


def fetch_houseplants_regex():
    sparql = SPARQLWrapper("https://query.wikidata.org/sparql")
    query = """
SELECT DISTINCT ?plant ?plantLabel WHERE {
  ?plant wdt:P31/wdt:P279* wd:Q16521 .
  ?plant wdt:P366 ?use .
  FILTER(CONTAINS(LCASE(STR(?use)), "152740"))  # Q152740 is houseplant
  SERVICE wikibase:label { bd:serviceParam wikibase:language "fi,en". }
}
LIMIT 50
    """

    sparql.setQuery(query)
    sparql.setReturnFormat(JSON)
    results = sparql.query().convert()

    plants = []
    bindings = results.get("results", {}).get("bindings", [])
    for result in bindings:
        plant_uri = result.get("plant", {}).get("value", "")
        plant_label = result.get("plantLabel", {}).get("value", "")
        plants.append(
            {
                "URI": plant_uri,
                "Name": plant_label,
            }
        )

    df = pd.DataFrame(plants)
    return df


if __name__ == "__main__":
    df = fetch_houseplants_regex()
    df.to_csv("houseplants_regex.csv", index=False)
    print(f"Dataset created with {len(df)} entries.")
