import requests


def get_planes(bbox):
    """
    Получает список самолётов в заданной области.
    """
    try:
        response = requests.get(
            "https://opensky-network.org/api/states/all",
            params={
                "lamin": bbox[0],
                "lomin": bbox[2],
                "lamax": bbox[1],
                "lomax": bbox[3],
            }
        )

        response.raise_for_status()
        data = response.json()

        return data.get("states", [])

    except requests.RequestException:
        return []