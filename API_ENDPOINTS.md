# Co-Stars Backend API Endpoints

This backend exposes a RESTful API for actor/movie pathfinding and game logic. Use these endpoints from your frontend or tools like Postman.

---

## 1. Get All Levels
- **Endpoint:** `GET /api/levels`
- **Description:** Returns all predefined levels.
- **Test in Postman:**
    - Method: GET
    - URL: `http://localhost:5000/api/levels`

---

## 2. Get Actor by Name
- **Endpoint:** `GET /api/actor/<name>`
- **Description:** Returns actor info by name (case-insensitive).
- **Test in Postman:**
    - Method: GET
    - URL: `http://localhost:5000/api/actor/Matt Damon`

---

## 3. Get Movies for Actor
- **Endpoint:** `GET /api/actor/<actor_id>/movies`
- **Description:** Returns all movies for a given actor ID.
- **Test in Postman:**
    - Method: GET
    - URL: `http://localhost:5000/api/actor/123/movies`

---

## 4. Get Costars for Movie
- **Endpoint:** `GET /api/movie/<movie_id>/costars`
- **Description:** Returns all costars for a given movie ID. Optionally exclude names with `?exclude=Name1&exclude=Name2`.
- **Test in Postman:**
    - Method: GET
    - URL: `http://localhost:5000/api/movie/456/costars?exclude=Matt Damon`

---

## 5. Validate a Path
- **Endpoint:** `POST /api/path/validate`
- **Description:** Validates a path (list of alternating actor/movie names) for correctness.
- **Test in Postman:**
    - Method: POST
    - URL: `http://localhost:5000/api/path/validate`
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
- Extend endpoints as needed for your frontend.
