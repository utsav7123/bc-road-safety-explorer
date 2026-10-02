from __future__ import annotations

from pathlib import Path
import requests

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "raw"

SOURCES = {
    "fatalities_road_user": "https://catalogue.data.gov.bc.ca/dataset/546debd7-1f13-40fb-9153-07b25b3cc01b/resource/834a8f81-9ac4-4ab9-9b1b-0c76452afe70/download/motor-vehicle-fatalities-by-road-user-type.csv",
    "fatalities_region": "https://catalogue.data.gov.bc.ca/dataset/f23f5ce0-44d4-4f7e-ab93-a9f5442d26c4/resource/1f1681c1-5e6e-4bae-ac34-d5df174ca1a5/download/motor-vehicle-fatalities-by-region.csv",
    "serious_injuries_region": "https://catalogue.data.gov.bc.ca/dataset/c336d3ee-c8b3-46b5-a3f7-a934bbc2c3ce/resource/1778419d-88e4-4d15-9b6f-b1895e397b89/download/motor-vehicle-serious-injuries-by-icbc-region.csv",
    "fatalities_speeding": "https://catalogue.data.gov.bc.ca/dataset/23937c1c-f1e0-497c-a34f-c2c6ce15e775/resource/de1b175c-2725-403a-ba33-6b57f868f38e/download/motor-vehicle-fatalities-with-speeding-involvement.csv",
}


def download(name: str, url: str) -> Path:
    response = requests.get(url, timeout=60)
    response.raise_for_status()
    path = RAW / f"{name}.csv"
    path.write_bytes(response.content)
    print(f"{name}: {len(response.content):,} bytes")
    return path


def main() -> None:
    RAW.mkdir(parents=True, exist_ok=True)
    for name, url in SOURCES.items():
        download(name, url)


if __name__ == "__main__":
    main()
