# Co-Stars Backend

A backend system for exploring connections between actors through movies they've appeared in together. This project uses the TMDB (The Movie Database) API to build a searchable network of actors and films.

## Overview

Co-Stars Backend enables you to:
- Fetch movie and actor data from TMDB API
- Store movie and actor information in a local SQLite database
- Query relationships between actors through their filmography
- Find the shortest path connecting any two actors (Six Degrees-style connections)

## Features

- **TMDB Integration**: Seamlessly fetch data from The Movie Database API
- **Movie Ingestion**: Add movies to the database by title or TMDB ID
- **Actor Network**: Build and query a network of actors and their collaborations
- **Path Finding**: Find shortest paths between any two actors using BFS algorithm
- **Duplicate Prevention**: Automatically skip movies that are already in the database

## Versus Game Usage

Start an interactive game between two actors:

```python
python versus_game.py
```

### How to Play

1. Choose your starting actor (1 or 2)
2. Select movies from that actor's filmography
3. Choose a costar from the selected movie
4. Continue until you reach the target actor
5. Use the back option to undo moves and explore alternative paths

**Features:**
- Loop detection automatically rewinds to prevent circular paths
- Backtracking support to explore different connections
- Path validation confirms all connections exist in the database
- Visual board display shows your current progression

## Project Structure

```
├── db.py                 # Database initialization and connection management
├── db_helper.py          # Database insertion and query helper functions
├── ingest.py             # Movie ingestion logic (by title or ID)
├── tmdb_api.py           # TMDB API wrapper functions
├── populate_db.py        # Main script to populate the database with initial movies
├── path_utils.py         # Actor path-finding algorithms
├── query_scratch.py      # Query utilities and testing
├── versus_game.py        # Interactive game mode to find connections between two actors with backtracking support
└── movies.db             # SQLite database (generated after initialization)
```

## Database Schema

### Movies Table
- `id` (INTEGER PRIMARY KEY): TMDB movie ID
- `title` (TEXT): Movie title
- `release_date` (TEXT): Release date

### Actors Table
- `id` (INTEGER PRIMARY KEY): TMDB actor ID
- `name` (TEXT): Actor name
- `popularity` (REAL): Popularity score from TMDB

### Movie_Actors Table (Junction)
- `movie_id` (INTEGER): Foreign key to movies
- `actor_id` (INTEGER): Foreign key to actors

## Setup

### Requirements
- Python 3.7+
- requests
- python-dotenv

### Installation

1. Clone the repository
2. Install dependencies:
   ```bash
   pip install requests python-dotenv
   ```

3. Set up environment variables:
   Create a `.env` file in the project root:
   ```
   TMDB_API_KEY=your_tmdb_api_key_here
   ```
   
   Get your API key from [The Movie Database (TMDB)](https://www.themoviedb.org/settings/api)

## Usage

### Populate the Database

Run the main population script to initialize and fill the database with sample movies:

```bash
python populate_db.py
```

This will:
1. Initialize a fresh SQLite database
2. Ingest a predefined list of movies
3. Fetch actors for each movie from TMDB
4. Store all data in the local database

### Ingest Individual Movies

```python
from ingest import ingest_movie_by_title, ingest_movie_by_id

# By movie title
ingest_movie_by_title("Ocean's Eleven")

# By TMDB ID
ingest_movie_by_id(1422)
```

### Find Actor Connections

```python
from path_utils import generate_path

# Find shortest path between two actors
path = generate_path(start_actor_id=123, end_actor_id=456)
# Returns: [actor, movie, actor, movie, ..., actor]
```

## Configuration

All database operations use `movies.db` as the default SQLite database file. This can be modified by changing the `DB_FILE` variable in `db.py` or `path_utils.py`.

