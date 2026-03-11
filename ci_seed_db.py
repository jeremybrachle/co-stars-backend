from db import init_db
from db_helper import insert_actor, insert_movie, insert_relationship


ACTORS = [
    (1461, "George Clooney", 33.1),
    (1892, "Matt Damon", 51.25),
    (8784, "Daniel Craig", 42.0),
    (13240, "Mark Wahlberg", 28.0),
    (287, "Brad Pitt", 37.0),
]

MOVIES = [
    (161, "Ocean's Eleven", "2001-12-07"),
    (1422, "The Departed", "2006-10-04"),
    (910001, "Bridge Line", "2010-01-01"),
]

RELATIONSHIPS = [
    (161, 1461),
    (161, 1892),
    (161, 287),
    (1422, 1892),
    (1422, 13240),
    (910001, 13240),
    (910001, 8784),
]


def main():
    init_db()

    for actor_id, name, popularity in ACTORS:
        insert_actor(actor_id, name, popularity)

    for movie_id, title, release_date in MOVIES:
        insert_movie(movie_id, title, release_date)

    for movie_id, actor_id in RELATIONSHIPS:
        insert_relationship(movie_id, actor_id)

    print("Seeded deterministic CI database fixture.")


if __name__ == "__main__":
    main()