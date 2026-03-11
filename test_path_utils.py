import unittest
from path_utils import generate_path, pretty_print_path, get_connection

def get_actor_id_by_name(name):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id FROM actors WHERE name = ? COLLATE NOCASE", (name,))
    row = cursor.fetchone()
    conn.close()
    return row[0] if row else None

def get_movie_id_by_title(title):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id FROM movies WHERE title = ? COLLATE NOCASE", (title,))
    row = cursor.fetchone()
    conn.close()
    return row[0] if row else None

class TestGeneratePath(unittest.TestCase):
    def test_actor_actor(self):
        src_name = "Matt Damon"
        dst_name = "Daniel Craig"
        a = get_actor_id_by_name(src_name)
        b = get_actor_id_by_name(dst_name)
        path = generate_path(a, "actor", b, "actor")
        self.assertIsInstance(path, list)
        self.assertGreaterEqual(len(path), 3)
        print("\n=== Test: Actor to Actor ===")
        print(f"From: {src_name} (id={a})  To: {dst_name} (id={b})")
        print(f"Raw path (IDs): {path}")
        print(f"Pretty path:   {pretty_print_path(path, start_type='actor')}")
        print("============================\n")

    def test_actor_movie(self):
        src_name = "Matt Damon"
        dst_title = "Ocean's Eleven"
        a = get_actor_id_by_name(src_name)
        b = get_movie_id_by_title(dst_title)
        path = generate_path(a, "actor", b, "movie")
        self.assertIsInstance(path, list)
        self.assertGreaterEqual(len(path), 2)
        print("\n=== Test: Actor to Movie ===")
        print(f"From: {src_name} (id={a})  To: {dst_title} (id={b})")
        print(f"Raw path (IDs): {path}")
        print(f"Pretty path:   {pretty_print_path(path, start_type='actor')}")
        print("============================\n")

    def test_movie_movie(self):
        src_title = "Ocean's Eleven"
        dst_title = "The Departed"
        a = get_movie_id_by_title(src_title)
        b = get_movie_id_by_title(dst_title)
        path = generate_path(a, "movie", b, "movie")
        self.assertIsInstance(path, list)
        self.assertGreaterEqual(len(path), 3)
        print("\n=== Test: Movie to Movie ===")
        print(f"From: {src_title} (id={a})  To: {dst_title} (id={b})")
        print(f"Raw path (IDs): {path}")
        print(f"Pretty path:   {pretty_print_path(path, start_type='movie')}")
        print("============================\n")

    def test_no_path(self):
        src_name = "Matt Damon"
        dst_name = "DefinitelyNotARealActorName12345"
        a = get_actor_id_by_name(src_name)
        b = get_actor_id_by_name(dst_name)
        if b is None:
            b = -999999
        path = generate_path(a, "actor", b, "actor")
        print("\n=== Test: No Path Exists ===")
        print(f"From: {src_name} (id={a})  To: {dst_name} (id={b})")
        print(f"Raw path (IDs): {path}")
        print("Expected: -1 (no path found)")
        print("============================\n")
        self.assertEqual(path, -1)

if __name__ == "__main__":
    suite = unittest.defaultTestLoader.loadTestsFromTestCase(TestGeneratePath)
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    passed = result.testsRun - len(result.failures) - len(result.errors)
    failed = len(result.failures) + len(result.errors)
    print(f"\nSummary: {passed} passed, {failed} failed, {result.testsRun} total")
