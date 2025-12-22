import requests

API_URL = "https://pokeapi.co/api/v2/"

def get_pokemon_list_data(name=None, type=None, generation=None):
    try:
        if name:
            response = requests.get(f"{API_URL}pokemon/{name.lower()}")
            if response.status_code == 200:
                data = response.json()
                return [{'name': data['name'], 'url': f"{API_URL}pokemon/{data['id']}"}], 200
            return [], 200

        elif type:
            response = requests.get(f"{API_URL}type/{type.lower()}")
            if response.status_code != 200:
                return [], 200
            data = response.json()
            return [{'name': p['pokemon']['name'], 'url': p['pokemon']['url']} for p in data['pokemon']], 200

        elif generation:
            response = requests.get(f"{API_URL}generation/{generation}")
            if response.status_code != 200:
                return [], 200
            data = response.json()
            return [{'name': p['name'], 'url': p['url']} for p in data['pokemon_species']], 200

        else:
            params = {'limit': 151}
            response = requests.get(f"{API_URL}pokemon", params=params)
            response.raise_for_status()
            data = response.json()
            return data['results'], 200

    except Exception as e:
        return {"error": str(e)}, 500


def get_pokemon_details_data(name):
    try:
        url = f"{API_URL}pokemon/{name.lower()}"
        response = requests.get(url)

        if response.status_code == 200:
            data = response.json()

            stats = []
            for s in data['stats']:
                stats.append({
                    "name": s['stat']['name'],
                    "base_stat": s['base_stat']
                })

            details = {
                "id": data['id'],
                "name": data['name'],
                "height": data['height'],
                "weight": data['weight'],
                "sprite": data['sprites']['other']['official-artwork']['front_default'] or data['sprites'][
                    'front_default'],
                "types": [t["type"]["name"] for t in data["types"]],
                "abilities": [a["ability"]["name"] for a in data["abilities"]],
                "stats": stats
            }
            return details, 200
        else:
            return {"error": "Not Found"}, 404

    except Exception as e:
        return {"error": str(e)}, 500