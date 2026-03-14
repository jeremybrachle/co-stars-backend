import unittest
from unittest.mock import patch

from fastapi.testclient import TestClient

from fastapi_app.main import app


class TestApiEndpoints(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(app)

    def test_health_check_returns_status_and_version(self):
        response = self.client.get("/api/health")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["status"], "ok")
        self.assertIn("version", response.json())

    @patch("fastapi_app.main.build_frontend_manifest")
    def test_export_frontend_manifest_returns_refresh_metadata(self, mock_build_frontend_manifest):
        mock_build_frontend_manifest.return_value = {
            "version": "2.1.0",
            "source_updated_at": "2026-03-11T00:00:00+00:00",
            "actor_count": 2,
            "movie_count": 1,
            "relationship_count": 2,
            "level_count": 1,
            "recommended_refresh_interval_hours": 168,
            "snapshot_endpoint": "/api/export/frontend-snapshot",
        }

        response = self.client.get("/api/export/frontend-manifest")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["recommended_refresh_interval_hours"], 168)
        self.assertEqual(response.json()["snapshot_endpoint"], "/api/export/frontend-snapshot")
        mock_build_frontend_manifest.assert_called_once()

    @patch("fastapi_app.main.build_frontend_snapshot")
    def test_export_frontend_snapshot_returns_full_graph_payload(self, mock_build_frontend_snapshot):
        mock_build_frontend_snapshot.return_value = {
            "meta": {
                "version": "2.1.0",
                "exported_at": "2026-03-11T00:00:00+00:00",
                "actor_count": 2,
                "movie_count": 1,
                "relationship_count": 2,
                "level_count": 1,
            },
            "actors": [
                {
                    "id": 1,
                    "name": "George Clooney",
                    "popularity": 33.1,
                    "birthday": "1961-05-06",
                    "deathday": None,
                    "place_of_birth": "Lexington, Kentucky, USA",
                    "biography": "Actor, director, and producer.",
                    "profile_path": "/george.jpg",
                    "profile_url": "https://image.tmdb.org/t/p/w500/george.jpg",
                    "known_for_department": "Acting",
                },
                {
                    "id": 2,
                    "name": "Matt Damon",
                    "popularity": 51.25,
                    "birthday": "1970-10-08",
                    "deathday": None,
                    "place_of_birth": "Cambridge, Massachusetts, USA",
                    "biography": "Actor and screenwriter.",
                    "profile_path": "/matt.jpg",
                    "profile_url": "https://image.tmdb.org/t/p/w500/matt.jpg",
                    "known_for_department": "Acting",
                },
            ],
            "movies": [
                {
                    "id": 11,
                    "title": "Ocean's Eleven",
                    "release_date": "2001-12-07",
                    "genres": ["Crime", "Thriller"],
                    "overview": "Danny Ocean assembles a crew.",
                    "poster_path": "/oceans.jpg",
                    "poster_url": "https://image.tmdb.org/t/p/w500/oceans.jpg",
                    "original_language": "en",
                    "content_rating": "PG-13",
                },
            ],
            "movie_actors": [
                {"movie_id": 11, "actor_id": 1},
                {"movie_id": 11, "actor_id": 2},
            ],
            "adjacency": {
                "actor_to_movies": {"1": [11], "2": [11]},
                "movie_to_actors": {"11": [1, 2]},
            },
            "levels": [
                {"actor_a": "George Clooney", "actor_b": "Matt Damon", "stars": 3},
            ],
        }

        response = self.client.get("/api/export/frontend-snapshot")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["meta"]["relationship_count"], 2)
        self.assertEqual(response.json()["adjacency"]["movie_to_actors"]["11"], [1, 2])
        mock_build_frontend_snapshot.assert_called_once()

    @patch("fastapi_app.main.get_all_actors_with_metadata")
    def test_get_all_actors_returns_enriched_actor_records(self, mock_get_all_actors):
        mock_get_all_actors.return_value = [
            (
                1,
                "George Clooney",
                33.1,
                "1961-05-06",
                None,
                "Lexington, Kentucky, USA",
                "Actor, director, and producer.",
                "/george.jpg",
                "Acting",
            ),
            (
                2,
                "Matt Damon",
                51.25,
                "1970-10-08",
                None,
                "Cambridge, Massachusetts, USA",
                "Actor and screenwriter.",
                "/matt.jpg",
                "Acting",
            ),
        ]

        response = self.client.get("/api/actors")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.json(),
            [
                {
                    "id": 1,
                    "name": "George Clooney",
                    "popularity": 33.1,
                    "birthday": "1961-05-06",
                    "deathday": None,
                    "place_of_birth": "Lexington, Kentucky, USA",
                    "biography": "Actor, director, and producer.",
                    "profile_path": "/george.jpg",
                    "profile_url": "https://image.tmdb.org/t/p/w500/george.jpg",
                    "known_for_department": "Acting",
                },
                {
                    "id": 2,
                    "name": "Matt Damon",
                    "popularity": 51.25,
                    "birthday": "1970-10-08",
                    "deathday": None,
                    "place_of_birth": "Cambridge, Massachusetts, USA",
                    "biography": "Actor and screenwriter.",
                    "profile_path": "/matt.jpg",
                    "profile_url": "https://image.tmdb.org/t/p/w500/matt.jpg",
                    "known_for_department": "Acting",
                },
            ],
        )

    @patch("fastapi_app.main.get_all_movies_with_metadata")
    def test_get_all_movies_returns_enriched_movie_records(self, mock_get_all_movies):
        mock_get_all_movies.return_value = [
            (
                11,
                "Ocean's Eleven",
                "2001-12-07",
                '["Crime", "Thriller"]',
                "Danny Ocean assembles a crew.",
                "/oceans.jpg",
                "en",
                "PG-13",
            ),
            (
                22,
                "The Departed",
                "2006-10-04",
                '["Crime", "Drama"]',
                "An undercover cop and a mole try to identify each other.",
                "/departed.jpg",
                "en",
                "R",
            ),
        ]

        response = self.client.get("/api/movies")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.json(),
            [
                {
                    "id": 11,
                    "title": "Ocean's Eleven",
                    "release_date": "2001-12-07",
                    "genres": ["Crime", "Thriller"],
                    "overview": "Danny Ocean assembles a crew.",
                    "poster_path": "/oceans.jpg",
                    "poster_url": "https://image.tmdb.org/t/p/w500/oceans.jpg",
                    "original_language": "en",
                    "content_rating": "PG-13",
                },
                {
                    "id": 22,
                    "title": "The Departed",
                    "release_date": "2006-10-04",
                    "genres": ["Crime", "Drama"],
                    "overview": "An undercover cop and a mole try to identify each other.",
                    "poster_path": "/departed.jpg",
                    "poster_url": "https://image.tmdb.org/t/p/w500/departed.jpg",
                    "original_language": "en",
                    "content_rating": "R",
                },
            ],
        )

    @patch("fastapi_app.main.vg_get_actor_details_by_name")
    def test_get_actor_by_name_includes_popularity(self, mock_get_actor_details):
        mock_get_actor_details.return_value = (101, "Matt Damon", 51.25)

        response = self.client.get("/api/actor/Matt Damon")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.json(),
            {"id": 101, "name": "Matt Damon", "popularity": 51.25},
        )

    @patch("fastapi_app.main.actor_exists")
    @patch("fastapi_app.main.db_get_movies_for_actor")
    @patch("fastapi_app.main.build_path_hint")
    def test_get_movies_for_actor_includes_optional_path_hints(
        self,
        mock_build_path_hint,
        mock_get_movies_for_actor,
        mock_actor_exists,
    ):
        mock_actor_exists.return_value = True
        mock_get_movies_for_actor.return_value = [
            (11, "Ocean's Eleven", "2001-12-07"),
            (12, "The Perfect Storm", "2000-06-30"),
        ]
        mock_build_path_hint.side_effect = [
            {
                "reachable": True,
                "steps_to_target": 1,
                "path": [
                    {"id": 11, "type": "movie", "label": "Ocean's Eleven"},
                    {"id": 44, "type": "actor", "label": "Matt Damon"},
                ],
            },
            {
                "reachable": True,
                "steps_to_target": 3,
                "path": [
                    {"id": 12, "type": "movie", "label": "The Perfect Storm"},
                    {"id": 55, "type": "actor", "label": "Mark Wahlberg"},
                    {"id": 21, "type": "movie", "label": "The Departed"},
                    {"id": 44, "type": "actor", "label": "Matt Damon"},
                ],
            },
        ]

        response = self.client.get("/api/actor/9/movies?target_type=actor&target_id=44")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()[0]["path_hint"]["steps_to_target"], 1)
        self.assertEqual(response.json()[1]["path_hint"]["steps_to_target"], 3)
        mock_build_path_hint.assert_any_call(11, "movie", 44, "actor")
        mock_build_path_hint.assert_any_call(12, "movie", 44, "actor")

    @patch("fastapi_app.main.actor_exists")
    @patch("fastapi_app.main.movie_exists")
    @patch("fastapi_app.main.db_get_movies_for_actor")
    @patch("fastapi_app.main.build_path_hint")
    def test_get_movies_for_actor_can_return_target_as_immediate_optimal_match(
        self,
        mock_build_path_hint,
        mock_get_movies_for_actor,
        mock_movie_exists,
        mock_actor_exists,
    ):
        mock_actor_exists.return_value = True
        mock_movie_exists.return_value = True
        mock_get_movies_for_actor.return_value = [
            (161, "Ocean's Eleven", "2001-12-07"),
        ]
        mock_build_path_hint.return_value = {
            "reachable": True,
            "steps_to_target": 0,
            "path": [{"id": 161, "type": "movie", "label": "Ocean's Eleven"}],
        }

        response = self.client.get("/api/actor/1461/movies?target_type=movie&target_id=161")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()[0]["path_hint"]["steps_to_target"], 0)
        self.assertEqual(response.json()[0]["path_hint"]["path"][0]["label"], "Ocean's Eleven")

    @patch("fastapi_app.main.actor_exists")
    @patch("fastapi_app.main.movie_exists")
    @patch("fastapi_app.main.get_actors_in_movie")
    @patch("fastapi_app.main.build_path_hint")
    def test_get_costars_returns_raw_popularity_plus_path_hints(
        self,
        mock_build_path_hint,
        mock_get_actors_in_movie,
        mock_movie_exists,
        mock_actor_exists,
    ):
        mock_movie_exists.return_value = True
        mock_actor_exists.return_value = True
        mock_get_actors_in_movie.return_value = [
            (44, "Matt Damon", 51.25),
            (55, "Mark Wahlberg", 28.0),
        ]
        mock_build_path_hint.side_effect = [
            {
                "reachable": True,
                "steps_to_target": 0,
                "path": [{"id": 44, "type": "actor", "label": "Matt Damon"}],
            },
            {
                "reachable": True,
                "steps_to_target": 2,
                "path": [
                    {"id": 55, "type": "actor", "label": "Mark Wahlberg"},
                    {"id": 21, "type": "movie", "label": "The Departed"},
                    {"id": 44, "type": "actor", "label": "Matt Damon"},
                ],
            },
        ]

        response = self.client.get("/api/movie/11/costars?exclude=George Clooney&target_type=actor&target_id=44")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.json(),
            [
                {
                    "id": 44,
                    "name": "Matt Damon",
                    "popularity": 51.25,
                    "path_hint": {
                        "reachable": True,
                        "steps_to_target": 0,
                        "path": [{"id": 44, "type": "actor", "label": "Matt Damon"}],
                    },
                },
                {
                    "id": 55,
                    "name": "Mark Wahlberg",
                    "popularity": 28.0,
                    "path_hint": {
                        "reachable": True,
                        "steps_to_target": 2,
                        "path": [
                            {"id": 55, "type": "actor", "label": "Mark Wahlberg"},
                            {"id": 21, "type": "movie", "label": "The Departed"},
                            {"id": 44, "type": "actor", "label": "Matt Damon"},
                        ],
                    },
                },
            ],
        )
        mock_get_actors_in_movie.assert_called_once_with(11, ["George Clooney"])

    @patch("fastapi_app.main.actor_exists")
    @patch("fastapi_app.main.movie_exists")
    @patch("fastapi_app.main.get_actors_in_movie")
    @patch("fastapi_app.main.build_path_hint")
    def test_get_costars_can_return_target_as_immediate_optimal_match(
        self,
        mock_build_path_hint,
        mock_get_actors_in_movie,
        mock_movie_exists,
        mock_actor_exists,
    ):
        mock_movie_exists.return_value = True
        mock_actor_exists.return_value = True
        mock_get_actors_in_movie.return_value = [
            (1892, "Matt Damon", 51.25),
        ]
        mock_build_path_hint.return_value = {
            "reachable": True,
            "steps_to_target": 0,
            "path": [{"id": 1892, "type": "actor", "label": "Matt Damon"}],
        }

        response = self.client.get("/api/movie/161/costars?target_type=actor&target_id=1892")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()[0]["path_hint"]["steps_to_target"], 0)
        self.assertEqual(response.json()[0]["path_hint"]["path"][0]["label"], "Matt Damon")

    @patch("fastapi_app.main.actor_exists")
    def test_get_movies_for_actor_rejects_partial_target_query(self, mock_actor_exists):
        mock_actor_exists.return_value = True

        response = self.client.get("/api/actor/9/movies?target_type=actor")

        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json(), {"detail": "target_type and target_id must be provided together"})

    @patch("fastapi_app.main.validate_named_path")
    def test_validate_path_supports_movie_start(self, mock_validate_named_path):
        mock_validate_named_path.return_value = True

        response = self.client.post(
            "/api/path/validate",
            json={
                "start_type": "movie",
                "path": ["Ocean's Eleven", "Matt Damon", "The Departed"],
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"valid": True})
        mock_validate_named_path.assert_called_once_with(
            ["Ocean's Eleven", "Matt Damon", "The Departed"],
            start_type="movie",
        )

    @patch("fastapi_app.main.normalize_path")
    def test_normalize_path_rewinds_to_previous_repeat(self, mock_normalize_path):
        mock_normalize_path.return_value = {
            "original_path": ["George Clooney", "Ocean's Eleven", "Brad Pitt", "The Mexican", "George Clooney"],
            "normalized_path": ["George Clooney"],
            "loop_detected": True,
            "rewind_to_index": 0,
            "repeated_node": {"type": "actor", "label": "George Clooney"},
            "removed_segment": [
                {"type": "movie", "label": "Ocean's Eleven"},
                {"type": "actor", "label": "Brad Pitt"},
                {"type": "movie", "label": "The Mexican"},
            ],
        }

        response = self.client.post(
            "/api/path/normalize",
            json={
                "start_type": "actor",
                "path": ["George Clooney", "Ocean's Eleven", "Brad Pitt", "The Mexican", "George Clooney"],
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["loop_detected"], True)
        self.assertEqual(response.json()["normalized_path"], ["George Clooney"])
        self.assertEqual(response.json()["rewind_to_index"], 0)
        mock_normalize_path.assert_called_once_with(
            ["George Clooney", "Ocean's Eleven", "Brad Pitt", "The Mexican", "George Clooney"],
            start_type="actor",
        )

    @patch("fastapi_app.main.vg_get_actor_by_name")
    @patch("fastapi_app.main.vg_get_movie_by_title")
    @patch("fastapi_app.main.generate_typed_path")
    @patch("fastapi_app.main.serialize_typed_path")
    @patch("fastapi_app.main.pretty_print_path")
    def test_generate_path_returns_structured_nodes(
        self,
        mock_pretty_print_path,
        mock_serialize_typed_path,
        mock_generate_typed_path,
        mock_get_movie_by_title,
        mock_get_actor_by_name,
    ):
        mock_get_actor_by_name.return_value = (1, "George Clooney")
        mock_get_movie_by_title.return_value = (11, "Ocean's Eleven")
        mock_generate_typed_path.return_value = [(1, "actor"), (11, "movie")]
        mock_serialize_typed_path.return_value = [
            {"id": 1, "type": "actor", "label": "George Clooney"},
            {"id": 11, "type": "movie", "label": "Ocean's Eleven"},
        ]
        mock_pretty_print_path.return_value = "George Clooney -> Ocean's Eleven"

        response = self.client.post(
            "/api/path/generate",
            json={
                "a": {"type": "actor", "value": "George Clooney"},
                "b": {"type": "movie", "value": "Ocean's Eleven"},
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.json(),
            {
                "path": "George Clooney -> Ocean's Eleven",
                "nodes": [
                    {"id": 1, "type": "actor", "label": "George Clooney"},
                    {"id": 11, "type": "movie", "label": "Ocean's Eleven"},
                ],
                "steps": 1,
                "reason": None,
            },
        )


if __name__ == "__main__":
    suite = unittest.defaultTestLoader.loadTestsFromTestCase(TestApiEndpoints)
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    passed = result.testsRun - len(result.failures) - len(result.errors)
    failed = len(result.failures) + len(result.errors)
    print(f"\nSummary: {passed} passed, {failed} failed, {result.testsRun} total")