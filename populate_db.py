from db import init_db
from ingest import ingest_movie_by_title, ingest_movie_by_id

def main():
    # 1️⃣ Initialize the database (fresh start)
    init_db()

    # 2️⃣ Movies to ingest (can be titles or IDs)
    movies_to_ingest = [
        "Ocean's Eleven",   # title
        1422,               # TMDB ID for The Departed
        "The Great Gatsby", # title
        2133,               # Perfect Storm
        270487,             # Hail Caesar
        348350,             # Solo
        334541,             # Manchester by the Sea
        580489,             # Venom 2
        652,                # Troy
        550,                # Fight Club
        2501,               # Bourne Identity
        615777,             # Babylon
        508,                # Love Actually
        27205,              # Inception
        414906,             # The Batman
        546554,             # Knives Out
        16869,              # Inglorious Basterds
        286217,             # The Martian
        206647,             # Spectre
    ]

    # 3️⃣ Ingest each movie
    for item in movies_to_ingest:
        if isinstance(item, int):
            print(f"\nIngesting movie by ID: {item}")
            ingest_movie_by_id(item)
        else:
            print(f"\nIngesting movie by title: {item}")
            ingest_movie_by_title(item)

    print("\nDatabase population complete!")

if __name__ == "__main__":
    main()
