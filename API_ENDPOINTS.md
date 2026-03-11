# Co-Stars Backend API Endpoints

This backend exposes a REST API for actor and movie graph traversal. The API returns raw data and optional shortest-path hints so the frontend can decide how to display suggestions, popularity, and optimal routes.

## Base URL

```text
http://localhost:8000
```

## Copy/Paste URLs

```text
http://localhost:8000/docs
http://localhost:8000/api/levels
http://localhost:8000/api/actors
http://localhost:8000/api/movies
http://localhost:8000/api/actor/Matt%20Damon
http://localhost:8000/api/actor/1461/movies?target_type=actor&target_id=1892
http://localhost:8000/api/movie/161/costars?exclude=George%20Clooney&target_type=actor&target_id=1892
```

## 1. Get All Levels

- Endpoint: `GET /api/levels`
- Description: Returns predefined challenge levels.
- Copy/paste request:

```http
GET http://localhost:8000/api/levels
```

## 2. Get All Actors

- Endpoint: `GET /api/actors`
- Description: Returns every actor in the database with all actor attributes.
- Copy/paste request:

```http
GET http://localhost:8000/api/actors
```

- Response shape:

```json
[
  {
    "id": 1892,
    "name": "Matt Damon",
    "popularity": 51.25
  }
]
```

## 3. Get All Movies

- Endpoint: `GET /api/movies`
- Description: Returns every movie in the database with all movie attributes.
- Copy/paste request:

```http
GET http://localhost:8000/api/movies
```

- Response shape:

```json
[
  {
    "id": 161,
    "title": "Ocean's Eleven",
    "release_date": "2001-12-07"
  }
]
```

## 4. Get Actor By Name

- Endpoint: `GET /api/actor/<name>`
- Description: Resolves an actor name to a database actor record.
- Copy/paste request:

```http
GET http://localhost:8000/api/actor/Matt%20Damon
```

- Response shape:

```json
{
  "id": 1892,
  "name": "Matt Damon",
  "popularity": 51.25
}
```

## 5. Get Movies For Actor

- Endpoint: `GET /api/actor/<actor_id>/movies`
- Description: Returns all movies for the actor. If `target_type` and `target_id` are provided, each movie also includes a shortest-path hint from that movie to the target node.
- Query params:
  - `target_type=actor|movie`
  - `target_id=<id>`
- Copy/paste request:

```http
GET http://localhost:8000/api/actor/1461/movies?target_type=actor&target_id=1892
```

- Response shape:

```json
[
  {
    "id": 161,
    "title": "Ocean's Eleven",
    "release_date": "2001-12-07",
    "path_hint": {
      "reachable": true,
      "steps_to_target": 1,
      "path": [
        { "id": 161, "type": "movie", "label": "Ocean's Eleven" },
        { "id": 1892, "type": "actor", "label": "Matt Damon" }
      ]
    }
  }
]
```

## 6. Get Actors For Movie

- Endpoint: `GET /api/movie/<movie_id>/costars`
- Description: Returns all actors in the movie. If `target_type` and `target_id` are provided, each actor also includes a shortest-path hint from that actor to the target node.
- Query params:
  - `exclude=Name1&exclude=Name2`
  - `target_type=actor|movie`
  - `target_id=<id>`
- Copy/paste request:

```http
GET http://localhost:8000/api/movie/161/costars?exclude=George%20Clooney&target_type=actor&target_id=1892
```

- Response shape:

```json
[
  {
    "id": 1892,
    "name": "Matt Damon",
    "popularity": 51.25,
    "path_hint": {
      "reachable": true,
      "steps_to_target": 0,
      "path": [
        { "id": 1892, "type": "actor", "label": "Matt Damon" }
      ]
    }
  }
]
```

## 7. Validate Path

- Endpoint: `POST /api/path/validate`
- Description: Validates a path of alternating actor and movie names.
- Copy/paste request:

```http
POST http://localhost:8000/api/path/validate
Content-Type: application/json
```

- Postman raw JSON body:

```json
{
  "path": [
    "George Clooney",
    "Ocean's Eleven",
    "Matt Damon"
  ]
}
```

## 8. Generate Path

- Endpoint: `POST /api/path/generate`
- Description: Generates a shortest path between any two named nodes.
- Copy/paste request:

```http
POST http://localhost:8000/api/path/generate
Content-Type: application/json
```

- Postman raw JSON body:

```json
{
  "a": {
    "type": "actor",
    "value": "George Clooney"
  },
  "b": {
    "type": "actor",
    "value": "Matt Damon"
  }
}
```

- Response shape:

```json
{
  "path": "George Clooney -> Ocean's Eleven -> Matt Damon",
  "nodes": [
    { "id": 1461, "type": "actor", "label": "George Clooney" },
    { "id": 161, "type": "movie", "label": "Ocean's Eleven" },
    { "id": 1892, "type": "actor", "label": "Matt Damon" }
  ],
  "steps": 2,
  "reason": null
}
```

## Notes

- Popularity is returned as raw data only. The frontend decides how to use it.
- Suggestion endpoints return full raw lists. The frontend decides whether to show all options, a subset, random options, or ranked options.
- Optional `path_hint` metadata lets the backend expose the optimal path to the target for each returned option, including immediate matches where `steps_to_target` is `0`.
- The frontend can also ignore those hints and compute its own ranking from the returned raw options.
- The `/api/actors` and `/api/movies` endpoints are intended for custom modes such as quick play and speed round.# Co-Stars Backend API Endpoints

This backend exposes a REST API for actor and movie graph traversal. The API returns raw data and optional shortest-path hints so the frontend can decide how to display suggestions, popularity, and optimal routes.

## Base URL

```text
http://localhost:8000
```

## 1. Get All Levels

- Endpoint: `GET /api/levels`
- Description: Returns predefined challenge levels.
- Example:

```http
GET http://localhost:8000/api/levels
```

## 2. Get All Actors

- Endpoint: `GET /api/actors`
- Description: Returns every actor in the database with all actor attributes.
- Example:

```http
GET http://localhost:8000/api/actors
```

- Response shape:

```json
[
  {
    "id": 1892,
    "name": "Matt Damon",
    "popularity": 51.25
  }
]
```

## 3. Get All Movies

- Endpoint: `GET /api/movies`
- Description: Returns every movie in the database with all movie attributes.
- Example:

```http
GET http://localhost:8000/api/movies
```

- Response shape:

```json
[
  {
    "id": 161,
    "title": "Ocean's Eleven",
    "release_date": "2001-12-07"
  }
]
```

## 4. Get Actor By Name

- Endpoint: `GET /api/actor/<name>`
- Description: Resolves an actor name to a database actor record.
- Example:

```http
GET http://localhost:8000/api/actor/Matt%20Damon
```

- Response shape:

```json
{
  "id": 1892,
  "name": "Matt Damon",
  "popularity": 51.25
}
```

## 5. Get Movies For Actor

- Endpoint: `GET /api/actor/<actor_id>/movies`
- Description: Returns all movies for the actor. If `target_type` and `target_id` are provided, each movie also includes a shortest-path hint from that movie to the target node.
- Query params:
  - `target_type=actor|movie`
  - `target_id=<id>`
- Example:

```http
GET http://localhost:8000/api/actor/1461/movies?target_type=actor&target_id=1892
```

- Response shape:

```json
[
  {
    "id": 161,
    "title": "Ocean's Eleven",
    "release_date": "2001-12-07",
    "path_hint": {
      "reachable": true,
      "steps_to_target": 1,
      "path": [
        { "id": 161, "type": "movie", "label": "Ocean's Eleven" },
        { "id": 1892, "type": "actor", "label": "Matt Damon" }
      ]
    }
  }
]
```

## 6. Get Actors For Movie

- Endpoint: `GET /api/movie/<movie_id>/costars`
- Description: Returns all actors in the movie. If `target_type` and `target_id` are provided, each actor also includes a shortest-path hint from that actor to the target node.
- Query params:
  - `exclude=Name1&exclude=Name2` to remove actor names already used by the frontend
  - `target_type=actor|movie`
  - `target_id=<id>`
- Example:

```http
GET http://localhost:8000/api/movie/161/costars?exclude=George%20Clooney&target_type=actor&target_id=1892
```

- Response shape:

```json
[
  {
    "id": 1892,
    "name": "Matt Damon",
    "popularity": 51.25,
    "path_hint": {
      "reachable": true,
      "steps_to_target": 0,
      "path": [
        { "id": 1892, "type": "actor", "label": "Matt Damon" }
      ]
    }
  }
]
```

## 7. Validate Path

- Endpoint: `POST /api/path/validate`
- Description: Validates a path of alternating actor and movie names.
- Example:

```http
POST http://localhost:8000/api/path/validate
Content-Type: application/json
```

- Body:

```json
{
  "path": ["George Clooney", "Ocean's Eleven", "Matt Damon"]
}
```

## 8. Generate Path

- Endpoint: `POST /api/path/generate`
- Description: Generates a shortest path between any two named nodes.
- Example:

```http
POST http://localhost:8000/api/path/generate
Content-Type: application/json
```

- Body:

```json
{
  "a": { "type": "actor", "value": "George Clooney" },
  "b": { "type": "actor", "value": "Matt Damon" }
}
```

- Response shape:

```json
{
  "path": "George Clooney -> Ocean's Eleven -> Matt Damon",
  "nodes": [
    { "id": 1461, "type": "actor", "label": "George Clooney" },
    { "id": 161, "type": "movie", "label": "Ocean's Eleven" },
    { "id": 1892, "type": "actor", "label": "Matt Damon" }
  ],
  "steps": 2,
  "reason": null
}
```

## Notes

- Popularity is returned as raw data only. The frontend decides how to use it.
- Suggestion endpoints return full raw lists. The frontend decides whether to show all options, a subset, random options, or ranked options.
- Optional `path_hint` metadata lets the frontend surface optimal and near-optimal routes without forcing a backend display policy.
- The `/api/actors` and `/api/movies` endpoints are intended for custom modes such as quick play and speed round.# Co-Stars Backend API Endpoints

This backend exposes a RESTful API for actor/movie pathfinding and game logic. Use these endpoints from your frontend or tools like Postman.

---

## 1. Get All Levels
- **Endpoint:** `GET /api/levels`
- **Description:** Returns all predefined levels.
- **Test in Postman:**
    - Method: GET
    - URL: `http://localhost:8000/api/levels`

---

## 2. Get Actor by Name
- **Endpoint:** `GET /api/actor/<name>`
- **Description:** Returns actor info by name (case-insensitive), including TMDB popularity.
- **Test in Postman:**
    - Method: GET
    - URL: `http://localhost:8000/api/actor/Matt Damon`
- **Response shape:**
    ```json
    {
        "id": 1892,
        "name": "Matt Damon",
        "popularity": 51.25
    }
    ```

---

## 3. Get Movies for Actor
- **Endpoint:** `GET /api/actor/<actor_id>/movies`
- **Description:** Returns all movies for a given actor ID.
- **Test in Postman:**
    - Method: GET
    - URL: `http://localhost:8000/api/actor/123/movies`

---

## 4. Get Costars for Movie
- **Endpoint:** `GET /api/movie/<movie_id>/costars`
- **Description:** Returns costars for a given movie ID with popularity metadata. Optionally exclude names with `?exclude=Name1&exclude=Name2`.
- **Query params:**
        - `exclude`: Repeatable actor names to omit from the result.
        - `selection_mode=all|versus`: Use `all` to return the full cast sorted by popularity descending, or `versus` to mirror the versus-game logic by selecting a random pool and then ranking by popularity.
- **Test in Postman:**
    - Method: GET
    - URL: `http://localhost:8000/api/movie/456/costars?exclude=Matt Damon`
        - Versus mode URL: `http://localhost:8000/api/movie/456/costars?selection_mode=versus&exclude=Matt Damon`
- **Response shape:**
    ```json
    [
        {
            "id": 287,
            "name": "Brad Pitt",
            "popularity": 78.4,
            "popularity_rank": 1
        },
        {
            "id": 819,
            "name": "Edward Norton",
            "popularity": 42.7,
            "popularity_rank": 2
        }
    ]
    ```

---

## 5. Validate a Path
- **Endpoint:** `POST /api/path/validate`
- **Description:** Validates a path (list of alternating actor/movie names) for correctness.
- **Test in Postman:**
    - Method: POST
    - URL: `http://localhost:8000/api/path/validate`
    - Body: Raw JSON
      ```json
      { "path": ["Matt Damon", "The Martian", "Jessica Chastain"] }
      ```

---

## How to Run and Test

1. Install dependencies:
    ```sh
    pip install flask
    ```
2. Start the server:
    ```sh
    python app.py
    ```
3. Use Postman to call the endpoints above.

---

## Notes
- All responses are JSON.
- All endpoints return appropriate HTTP status codes.
- For actor/movie IDs, use the IDs returned by previous API calls.
- Actor and costar payloads now include `popularity`, and costars include `popularity_rank` so frontend logic can align with backend ranking rules.
