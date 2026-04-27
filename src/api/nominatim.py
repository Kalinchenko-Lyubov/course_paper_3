import requests

def get_country_bbox(country_name):
    """
    Получает bounding box страны через API Nominatim.
    """
    try:
        response = requests.get(
            "https://nominatim.openstreetmap.org/search",
            params={
                "q": country_name,
                "format": "json",
                "limit": 1
            },
            headers={"User-Agent": "airplanes-app"}
        )

        response.raise_for_status()
        data = response.json()

        if not data:
            return None

        bbox = data[0]["boundingbox"]
        return tuple(map(float, bbox))

    except requests.RequestException:
        return None