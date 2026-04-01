import os
import sqlite3
import tempfile
import unittest
from unittest.mock import patch

import db
import db_helper
import populate_db
from frontend_snapshot import (
    build_frontend_manifest,
    build_frontend_manifest_v2,
    build_frontend_snapshot,
    build_frontend_snapshot_v2,
)


def initialize_legacy_db(db_path):
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
        self.db_helper_patch = patch.object(db_helper, "DB_FILE", self.db_path)
        self.db_patch = patch.object(db, "DB_FILE", self.db_path)
        self.db_helper_patch.start()
        self.db_patch.start()

        db.ensure_schema()

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
        self.db_helper_patch.stop()
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

    def test_insert_movie_upserts_enriched_metadata(self):
        db_helper.insert_movie(
            161,
            "Ocean's Eleven",
            "2001-12-07",
            genres_json='["Crime", "Thriller"]',
            overview="Danny Ocean assembles a crew.",
            poster_path="/poster.jpg",
            original_language="en",
            content_rating="PG-13",
        )

        conn = sqlite3.connect(self.db_path)
        row = conn.execute(
            """
            SELECT genres_json, overview, poster_path, original_language, content_rating
            FROM movies
            WHERE id = 161
            """
        ).fetchone()
        conn.close()

        self.assertEqual(
            row,
            ('["Crime", "Thriller"]', "Danny Ocean assembles a crew.", "/poster.jpg", "en", "PG-13"),
        )

    def test_insert_actor_upserts_enriched_metadata(self):
        db_helper.insert_actor(
            1892,
            "Matt Damon",
            51.25,
            birthday="1970-10-08",
            deathday=None,
            place_of_birth="Cambridge, Massachusetts, USA",
            biography="Fixture biography",
            profile_path="/matt.jpg",
            known_for_department="Acting",
        )

        conn = sqlite3.connect(self.db_path)
        row = conn.execute(
            """
            SELECT birthday, deathday, place_of_birth, biography, profile_path, known_for_department
            FROM actors
            WHERE id = 1892
            """
        ).fetchone()
        conn.close()

        self.assertEqual(
            row,
            (
                "1970-10-08",
                None,
                "Cambridge, Massachusetts, USA",
                "Fixture biography",
                "/matt.jpg",
                "Acting",
            ),
        )


class TestSchemaMigration(unittest.TestCase):
    def setUp(self):
        temp_db = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
        temp_db.close()
        self.db_path = temp_db.name
        self.db_patch = patch.object(db, "DB_FILE", self.db_path)
        self.db_patch.start()
        initialize_legacy_db(self.db_path)

    def tearDown(self):
        self.db_patch.stop()
        if os.path.exists(self.db_path):
            os.remove(self.db_path)

    def test_ensure_schema_adds_missing_enrichment_columns(self):
        db.ensure_schema()

        conn = sqlite3.connect(self.db_path)
        movie_columns = {
            row[1] for row in conn.execute("PRAGMA table_info(movies)").fetchall()
        }
        actor_columns = {
            row[1] for row in conn.execute("PRAGMA table_info(actors)").fetchall()
        }
        conn.close()

        self.assertTrue(
            {"genres_json", "overview", "poster_path", "original_language", "content_rating"}.issubset(movie_columns)
        )
        self.assertTrue(
            {"birthday", "deathday", "place_of_birth", "biography", "profile_path", "known_for_department"}.issubset(actor_columns)
        )


class TestPopulateDbHelpers(unittest.TestCase):
    def test_load_seed_movie_ids_reads_tmdb_ids(self):
        with tempfile.NamedTemporaryFile("w", suffix=".csv", delete=False, newline="") as handle:
            handle.write("tmdb_movie_id,title\n161,Ocean's Eleven\n1422,The Departed\n")
            csv_path = handle.name

        try:
            self.assertEqual(populate_db.load_seed_movie_ids(csv_path), [161, 1422])
        finally:
            os.remove(csv_path)

    @patch("populate_db.ingest_movie_by_id")
    @patch("populate_db.movie_exists")
    def test_sync_movies_skips_existing_ids_in_additive_mode(
        self,
        mock_movie_exists,
        mock_ingest_movie_by_id,
    ):
        mock_movie_exists.side_effect = [False, True, False]
        mock_ingest_movie_by_id.side_effect = ["inserted", "inserted"]

        summary = populate_db.sync_movies([161, 1422, 508])

        self.assertEqual(summary, {"inserted": 2, "refreshed": 0, "skipped": 1})
        self.assertEqual(mock_ingest_movie_by_id.call_count, 2)
        mock_ingest_movie_by_id.assert_any_call(161, refresh_existing=False)
        mock_ingest_movie_by_id.assert_any_call(508, refresh_existing=False)

    @patch("populate_db.ingest_movie_by_id")
    @patch("populate_db.movie_exists")
    def test_sync_movies_refreshes_existing_ids_when_requested(
        self,
        mock_movie_exists,
        mock_ingest_movie_by_id,
    ):
        mock_movie_exists.side_effect = [True, True]
        mock_ingest_movie_by_id.side_effect = ["refreshed", "refreshed"]

        summary = populate_db.sync_movies([161, 1422], refresh_existing=True)

        self.assertEqual(summary, {"inserted": 0, "refreshed": 2, "skipped": 0})
        mock_ingest_movie_by_id.assert_any_call(161, refresh_existing=True)
        mock_ingest_movie_by_id.assert_any_call(1422, refresh_existing=True)


class TestFrontendSnapshotBuilders(unittest.TestCase):
    @patch("frontend_snapshot.get_project_version", return_value="2.1.0")
    @patch("frontend_snapshot.get_all_movie_actor_links")
    @patch("frontend_snapshot.get_all_movies_with_metadata")
    @patch("frontend_snapshot.get_all_actors_with_metadata")
    def test_build_frontend_snapshot_assembles_graph_payload(
        self,
        mock_get_all_actors,
        mock_get_all_movies,
        mock_get_all_links,
        mock_get_project_version,
    ):
        mock_get_all_actors.return_value = [
            (1461, "George Clooney", 33.1, "1961-05-06", None, "Lexington, Kentucky, USA", "Actor.", "/george.jpg", "Acting"),
            (1892, "Matt Damon", 51.25, "1970-10-08", None, "Cambridge, Massachusetts, USA", "Actor.", "/matt.jpg", "Acting"),
        ]
        mock_get_all_movies.return_value = [
            (161, "Ocean's Eleven", "2001-12-07", '["Crime", "Thriller"]', "Danny Ocean assembles a crew.", "/oceans.jpg", "en", "PG-13"),
        ]
        mock_get_all_links.return_value = [
            (161, 1461),
            (161, 1892),
        ]

        snapshot = build_frontend_snapshot(
            [{"actor_a": "George Clooney", "actor_b": "Matt Damon", "stars": 3}]
        )

        self.assertEqual(snapshot["meta"]["version"], "2.1.0")
        self.assertEqual(snapshot["meta"]["actor_count"], 2)
        self.assertEqual(snapshot["actors"][0]["profile_url"], "https://image.tmdb.org/t/p/w500/george.jpg")
        self.assertEqual(snapshot["movies"][0]["poster_url"], "https://image.tmdb.org/t/p/w500/oceans.jpg")
        self.assertEqual(snapshot["adjacency"]["actor_to_movies"]["1461"], [161])
        self.assertEqual(snapshot["adjacency"]["movie_to_actors"]["161"], [1461, 1892])
        self.assertEqual(snapshot["levels"][0]["actor_b"], "Matt Damon")
        mock_get_project_version.assert_called_once()

    @patch("frontend_snapshot.get_all_movie_actor_links")
    @patch("frontend_snapshot.get_all_movies_with_metadata")
    @patch("frontend_snapshot.get_all_actors_with_metadata")
    def test_build_frontend_snapshot_rejects_levels_missing_from_graph(
        self,
        mock_get_all_actors,
        mock_get_all_movies,
        mock_get_all_links,
    ):
        mock_get_all_actors.return_value = [
            (1461, "George Clooney", 33.1, None, None, None, None, None, None),
        ]
        mock_get_all_movies.return_value = [
            (161, "Ocean's Eleven", "2001-12-07", None, None, None, None, None),
        ]
        mock_get_all_links.return_value = [
            (161, 1461),
        ]

        with self.assertRaisesRegex(ValueError, "Matt Damon"):
            build_frontend_snapshot(
                [{"actor_a": "George Clooney", "actor_b": "Matt Damon", "stars": 3}]
            )

    @patch("frontend_snapshot._get_source_updated_at", return_value="2026-03-11T00:00:00+00:00")
    @patch("frontend_snapshot.get_project_version", return_value="2.1.0")
    @patch("frontend_snapshot.get_all_movie_actor_links")
    @patch("frontend_snapshot.get_all_movies_with_metadata")
    @patch("frontend_snapshot.get_all_actors_with_metadata")
    def test_build_frontend_manifest_reports_refresh_metadata(
        self,
        mock_get_all_actors,
        mock_get_all_movies,
        mock_get_all_links,
        mock_get_project_version,
        mock_get_source_updated_at,
    ):
        mock_get_all_actors.return_value = [
            (1461, "George Clooney", 33.1, None, None, None, None, None, None),
            (1892, "Matt Damon", 51.25, None, None, None, None, None, None),
        ]
        mock_get_all_movies.return_value = [(161, "Ocean's Eleven", "2001-12-07", None, None, None, None, None)]
        mock_get_all_links.return_value = [(161, 1461)]

        manifest = build_frontend_manifest(
            [{"actor_a": "George Clooney", "actor_b": "Matt Damon", "stars": 3}]
        )

        self.assertEqual(manifest["version"], "2.1.0")
        self.assertEqual(manifest["source_updated_at"], "2026-03-11T00:00:00+00:00")
        self.assertEqual(manifest["recommended_refresh_interval_hours"], 168)
        self.assertEqual(manifest["snapshot_endpoint"], "/api/export/frontend-snapshot")
        self.assertEqual(manifest["relationship_count"], 1)
        mock_get_source_updated_at.assert_called_once()
        mock_get_project_version.assert_called_once()

    @patch("frontend_snapshot._get_source_updated_at", return_value="2026-03-11T00:00:00+00:00")
    @patch("frontend_snapshot.get_project_version", return_value="2.1.0")
    @patch("frontend_snapshot.get_all_movie_actor_links")
    @patch("frontend_snapshot.get_all_movies_with_metadata")
    @patch("frontend_snapshot.get_all_actors_with_metadata")
    def test_build_frontend_manifest_accepts_static_snapshot_endpoint(
        self,
        mock_get_all_actors,
        mock_get_all_movies,
        mock_get_all_links,
        mock_get_project_version,
        mock_get_source_updated_at,
    ):
        mock_get_all_actors.return_value = [
            (1461, "George Clooney", 33.1, None, None, None, None, None, None),
            (1892, "Matt Damon", 51.25, None, None, None, None, None, None),
        ]
        mock_get_all_movies.return_value = [(161, "Ocean's Eleven", "2001-12-07", None, None, None, None, None)]
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
    @patch("frontend_snapshot.get_project_version", return_value="2.1.0")
    @patch("frontend_snapshot.get_all_movie_actor_links")
    @patch("frontend_snapshot.get_all_movies_with_metadata")
    @patch("frontend_snapshot.get_all_actors_with_metadata")
    def test_build_frontend_manifest_rejects_levels_missing_from_graph(
        self,
        mock_get_all_actors,
        mock_get_all_movies,
        mock_get_all_links,
        mock_get_project_version,
        mock_get_source_updated_at,
    ):
        mock_get_all_actors.return_value = [(1461, "George Clooney", 33.1, None, None, None, None, None, None)]
        mock_get_all_movies.return_value = [(161, "Ocean's Eleven", "2001-12-07", None, None, None, None, None)]
        mock_get_all_links.return_value = [(161, 1461)]

        with self.assertRaisesRegex(ValueError, "Matt Damon"):
            build_frontend_manifest(
                [{"actor_a": "George Clooney", "actor_b": "Matt Damon", "stars": 3}]
            )

    @patch("frontend_snapshot.get_project_version", return_value="2.2.0")
    @patch("frontend_snapshot.get_all_movie_actor_links")
    @patch("frontend_snapshot.get_all_movies_with_metadata")
    @patch("frontend_snapshot.get_all_actors_with_metadata")
    def test_build_frontend_snapshot_v2_assembles_grouped_graph_payload(
        self,
        mock_get_all_actors,
        mock_get_all_movies,
        mock_get_all_links,
        mock_get_project_version,
    ):
        mock_get_all_actors.return_value = [
            (1461, "George Clooney", 33.1, "1961-05-06", None, "Lexington, Kentucky, USA", "Actor.", "/george.jpg", "Acting"),
            (1892, "Matt Damon", 51.25, "1970-10-08", None, "Cambridge, Massachusetts, USA", "Actor.", "/matt.jpg", "Acting"),
        ]
        mock_get_all_movies.return_value = [
            (161, "Ocean's Eleven", "2001-12-07", '["Crime", "Thriller"]', "Danny Ocean assembles a crew.", "/oceans.jpg", "en", "PG-13"),
        ]
        mock_get_all_links.return_value = [
            (161, 1461),
            (161, 1892),
        ]

        snapshot = build_frontend_snapshot_v2(
            {
                "schema-version": 2,
                "levels": [
                    {
                        "level-id": "1",
                        "level-name": "Level 1 - Starter Pack",
                        "game-data": [
                            {
                                "game-id": "1",
                                "game-type": "normal-non-boss",
                                "startNode": {"id": 1892, "type": "actor", "label": "Matt Damon"},
                                "targetNode": {"id": 1461, "type": "actor", "label": "George Clooney"},
                                "notes": {"text": "Fixture"},
                                "settings": {},
                            }
                        ],
                    }
                ],
            }
        )

        self.assertEqual(snapshot["meta"]["version"], "2.2.0")
        self.assertEqual(snapshot["meta"]["level_schema_version"], 2)
        self.assertEqual(snapshot["meta"]["level_group_count"], 1)
        self.assertEqual(snapshot["meta"]["normal_game_count"], 1)
        self.assertEqual(snapshot["levels"][0]["game-data"][0]["targetNode"]["id"], 1461)
        mock_get_project_version.assert_called_once()

    @patch("frontend_snapshot._get_source_updated_at", return_value="2026-03-11T00:00:00+00:00")
    @patch("frontend_snapshot.get_project_version", return_value="2.2.0")
    @patch("frontend_snapshot.get_all_movie_actor_links")
    @patch("frontend_snapshot.get_all_movies_with_metadata")
    @patch("frontend_snapshot.get_all_actors_with_metadata")
    def test_build_frontend_manifest_v2_reports_grouped_refresh_metadata(
        self,
        mock_get_all_actors,
        mock_get_all_movies,
        mock_get_all_links,
        mock_get_project_version,
        mock_get_source_updated_at,
    ):
        mock_get_all_actors.return_value = [
            (1461, "George Clooney", 33.1, None, None, None, None, None, None),
            (1892, "Matt Damon", 51.25, None, None, None, None, None, None),
        ]
        mock_get_all_movies.return_value = [(161, "Ocean's Eleven", "2001-12-07", None, None, None, None, None)]
        mock_get_all_links.return_value = [(161, 1461)]

        manifest = build_frontend_manifest_v2(
            {
                "schema-version": 2,
                "levels": [
                    {
                        "level-id": "1",
                        "level-name": "Level 1 - Starter Pack",
                        "game-data": [
                            {
                                "game-id": "1",
                                "game-type": "normal-non-boss",
                                "startNode": {"id": 1892, "type": "actor", "label": "Matt Damon"},
                                "targetNode": {"id": 1461, "type": "actor", "label": "George Clooney"},
                                "notes": {"text": "Fixture"},
                                "settings": {},
                            }
                        ],
                    }
                ],
            },
            snapshot_endpoint="/api/v2/export/frontend-snapshot",
        )

        self.assertEqual(manifest["version"], "2.2.0")
        self.assertEqual(manifest["source_updated_at"], "2026-03-11T00:00:00+00:00")
        self.assertEqual(manifest["level_group_count"], 1)
        self.assertEqual(manifest["normal_game_count"], 1)
        self.assertEqual(manifest["boss_game_count"], 0)
        self.assertEqual(manifest["snapshot_endpoint"], "/api/v2/export/frontend-snapshot")
        mock_get_source_updated_at.assert_called_once()
        mock_get_project_version.assert_called_once()


if __name__ == "__main__":
    suite = unittest.defaultTestLoader.loadTestsFromModule(__import__(__name__))
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    passed = result.testsRun - len(result.failures) - len(result.errors)
    failed = len(result.failures) + len(result.errors)
    print(f"\nSummary: {passed} passed, {failed} failed, {result.testsRun} total")