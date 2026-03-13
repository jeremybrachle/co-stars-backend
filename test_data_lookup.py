import os
import sqlite3
import tempfile
import unittest
from unittest.mock import patch

import db_helper
from frontend_snapshot import build_frontend_manifest, build_frontend_snapshot


def initialize_temp_db(db_path):
    connection = sqlite3.connect(db_path)
    cursor = connection.cursor()
    cursor.execute(
        """
        CREATE TABLE actors (
            id INTEGER PRIMARY KEY,
            name TEXT,
            popularity REAL
        )
        """
    )
    cursor.execute(
        """
        CREATE TABLE movies (
            id INTEGER PRIMARY KEY,
            title TEXT,
            release_date TEXT
        )
        """
    )
    cursor.execute(
        """
        CREATE TABLE movie_actors (
            movie_id INTEGER,
            actor_id INTEGER,
            PRIMARY KEY (movie_id, actor_id)
        )
        """
    )
    connection.commit()
    connection.close()


class TestDbHelperLookups(unittest.TestCase):
    def setUp(self):
        temp_db = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
        temp_db.close()
        self.db_path = temp_db.name
        self.db_patch = patch.object(db_helper, "DB_FILE", self.db_path)
        self.db_patch.start()

        initialize_temp_db(self.db_path)

        db_helper.insert_actor(1461, "George Clooney", 33.1)
        db_helper.insert_actor(1892, "Matt Damon", 51.25)
        db_helper.insert_actor(287, "Brad Pitt", 37.0)
        db_helper.insert_movie(161, "Ocean's Eleven", "2001-12-07")
        db_helper.insert_movie(910001, "Fixture Bridge Line", "2010-01-01")
        db_helper.insert_relationship(161, 1461)
        db_helper.insert_relationship(161, 1892)
        db_helper.insert_relationship(161, 287)
        db_helper.insert_relationship(910001, 1892)

    def tearDown(self):
        self.db_patch.stop()
        if os.path.exists(self.db_path):
            os.remove(self.db_path)

    def test_get_movies_for_actor_returns_sorted_titles(self):
        movies = db_helper.get_movies_for_actor(1892)

        self.assertEqual(
            movies,
            [
                (910001, "Fixture Bridge Line", "2010-01-01"),
                (161, "Ocean's Eleven", "2001-12-07"),
            ],
        )

    def test_get_actors_in_movie_excludes_names_and_returns_sorted(self):
        actors = db_helper.get_actors_in_movie(161, exclude_names=["George Clooney"])

        self.assertEqual(
            actors,
            [
                (287, "Brad Pitt", 37.0),
                (1892, "Matt Damon", 51.25),
            ],
        )

    def test_get_all_movie_actor_links_returns_ordered_edges(self):
        links = db_helper.get_all_movie_actor_links()

        self.assertEqual(
            links,
            [
                (161, 287),
                (161, 1461),
                (161, 1892),
                (910001, 1892),
            ],
        )

    def test_existence_and_id_lookups_return_expected_records(self):
        self.assertTrue(db_helper.actor_exists(1461))
        self.assertFalse(db_helper.actor_exists(999999))
        self.assertTrue(db_helper.movie_exists(161))
        self.assertFalse(db_helper.movie_exists(999999))
        self.assertTrue(db_helper.movie_exists_by_title("ocean's eleven"))
        self.assertEqual(db_helper.get_actor_by_id(1892), (1892, "Matt Damon", 51.25))
        self.assertEqual(db_helper.get_movie_by_id(161), (161, "Ocean's Eleven", "2001-12-07"))


class TestFrontendSnapshotBuilders(unittest.TestCase):
    @patch("frontend_snapshot.get_project_version", return_value="2.0.0")
    @patch("frontend_snapshot.get_all_movie_actor_links")
    @patch("frontend_snapshot.get_all_movies")
    @patch("frontend_snapshot.get_all_actors")
    def test_build_frontend_snapshot_assembles_graph_payload(
        self,
        mock_get_all_actors,
        mock_get_all_movies,
        mock_get_all_links,
        mock_get_project_version,
    ):
        mock_get_all_actors.return_value = [
            (1461, "George Clooney", 33.1),
            (1892, "Matt Damon", 51.25),
        ]
        mock_get_all_movies.return_value = [
            (161, "Ocean's Eleven", "2001-12-07"),
        ]
        mock_get_all_links.return_value = [
            (161, 1461),
            (161, 1892),
        ]

        snapshot = build_frontend_snapshot(
            [{"actor_a": "George Clooney", "actor_b": "Matt Damon", "stars": 3}]
        )

        self.assertEqual(snapshot["meta"]["version"], "2.0.0")
        self.assertEqual(snapshot["meta"]["actor_count"], 2)
        self.assertEqual(snapshot["adjacency"]["actor_to_movies"]["1461"], [161])
        self.assertEqual(snapshot["adjacency"]["movie_to_actors"]["161"], [1461, 1892])
        self.assertEqual(snapshot["levels"][0]["actor_b"], "Matt Damon")
        mock_get_project_version.assert_called_once()

    @patch("frontend_snapshot.get_all_movie_actor_links")
    @patch("frontend_snapshot.get_all_movies")
    @patch("frontend_snapshot.get_all_actors")
    def test_build_frontend_snapshot_rejects_levels_missing_from_graph(
        self,
        mock_get_all_actors,
        mock_get_all_movies,
        mock_get_all_links,
    ):
        mock_get_all_actors.return_value = [
            (1461, "George Clooney", 33.1),
        ]
        mock_get_all_movies.return_value = [
            (161, "Ocean's Eleven", "2001-12-07"),
        ]
        mock_get_all_links.return_value = [
            (161, 1461),
        ]

        with self.assertRaisesRegex(ValueError, "Matt Damon"):
            build_frontend_snapshot(
                [{"actor_a": "George Clooney", "actor_b": "Matt Damon", "stars": 3}]
            )

    @patch("frontend_snapshot._get_source_updated_at", return_value="2026-03-11T00:00:00+00:00")
    @patch("frontend_snapshot.get_project_version", return_value="2.0.0")
    @patch("frontend_snapshot.get_all_movie_actor_links")
    @patch("frontend_snapshot.get_all_movies")
    @patch("frontend_snapshot.get_all_actors")
    def test_build_frontend_manifest_reports_refresh_metadata(
        self,
        mock_get_all_actors,
        mock_get_all_movies,
        mock_get_all_links,
        mock_get_project_version,
        mock_get_source_updated_at,
    ):
        mock_get_all_actors.return_value = [
            (1461, "George Clooney", 33.1),
            (1892, "Matt Damon", 51.25),
        ]
        mock_get_all_movies.return_value = [(161, "Ocean's Eleven", "2001-12-07")]
        mock_get_all_links.return_value = [(161, 1461)]

        manifest = build_frontend_manifest(
            [{"actor_a": "George Clooney", "actor_b": "Matt Damon", "stars": 3}]
        )

        self.assertEqual(manifest["version"], "2.0.0")
        self.assertEqual(manifest["source_updated_at"], "2026-03-11T00:00:00+00:00")
        self.assertEqual(manifest["recommended_refresh_interval_hours"], 168)
        self.assertEqual(manifest["snapshot_endpoint"], "/api/export/frontend-snapshot")
        self.assertEqual(manifest["relationship_count"], 1)
        mock_get_source_updated_at.assert_called_once()
        mock_get_project_version.assert_called_once()

    @patch("frontend_snapshot._get_source_updated_at", return_value="2026-03-11T00:00:00+00:00")
    @patch("frontend_snapshot.get_project_version", return_value="2.0.0")
    @patch("frontend_snapshot.get_all_movie_actor_links")
    @patch("frontend_snapshot.get_all_movies")
    @patch("frontend_snapshot.get_all_actors")
    def test_build_frontend_manifest_accepts_static_snapshot_endpoint(
        self,
        mock_get_all_actors,
        mock_get_all_movies,
        mock_get_all_links,
        mock_get_project_version,
        mock_get_source_updated_at,
    ):
        mock_get_all_actors.return_value = [
            (1461, "George Clooney", 33.1),
            (1892, "Matt Damon", 51.25),
        ]
        mock_get_all_movies.return_value = [(161, "Ocean's Eleven", "2001-12-07")]
        mock_get_all_links.return_value = [(161, 1461)]

        manifest = build_frontend_manifest(
            [{"actor_a": "George Clooney", "actor_b": "Matt Damon", "stars": 3}],
            snapshot_endpoint="https://cdn.example.com/co-stars/frontend-snapshot.json",
        )

        self.assertEqual(
            manifest["snapshot_endpoint"],
            "https://cdn.example.com/co-stars/frontend-snapshot.json",
        )
        mock_get_source_updated_at.assert_called_once()
        mock_get_project_version.assert_called_once()

    @patch("frontend_snapshot._get_source_updated_at", return_value="2026-03-11T00:00:00+00:00")
    @patch("frontend_snapshot.get_project_version", return_value="2.0.0")
    @patch("frontend_snapshot.get_all_movie_actor_links")
    @patch("frontend_snapshot.get_all_movies")
    @patch("frontend_snapshot.get_all_actors")
    def test_build_frontend_manifest_rejects_levels_missing_from_graph(
        self,
        mock_get_all_actors,
        mock_get_all_movies,
        mock_get_all_links,
        mock_get_project_version,
        mock_get_source_updated_at,
    ):
        mock_get_all_actors.return_value = [(1461, "George Clooney", 33.1)]
        mock_get_all_movies.return_value = [(161, "Ocean's Eleven", "2001-12-07")]
        mock_get_all_links.return_value = [(161, 1461)]

        with self.assertRaisesRegex(ValueError, "Matt Damon"):
            build_frontend_manifest(
                [{"actor_a": "George Clooney", "actor_b": "Matt Damon", "stars": 3}]
            )


if __name__ == "__main__":
    suite = unittest.defaultTestLoader.loadTestsFromModule(__import__(__name__))
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    passed = result.testsRun - len(result.failures) - len(result.errors)
    failed = len(result.failures) + len(result.errors)
    print(f"\nSummary: {passed} passed, {failed} failed, {result.testsRun} total")