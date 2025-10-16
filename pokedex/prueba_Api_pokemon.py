import requests

def get_pokemon(name):
    url = f"https://pokeapi.co/api/v2/pokemon/{name.lower()}"
    response = requests.get(url)

    if response.status_code == 200:
        data = response.json()

        nombre=(f"Nombre: {data['name'].capitalize()}")
        id=(f"ID: {data['id']}")
        altura=(f"Altura: {data['height']}")
        peso=(f"Peso: {data['weight']}")
        tipos=[t["type"]["name"] for t in data["types"]]



    else:
        print("Pokémon no encontrado.")

nombre=input("nombre pokemon:")
get_pokemon(nombre)


