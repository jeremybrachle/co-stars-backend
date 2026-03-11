# Frontend Integration Guide

This guide describes how a frontend should call the local Co-Stars backend and use the API as a source of raw game data rather than as a source of fixed UI logic.

The backend now exposes:

1. Raw actor and movie data.
2. Raw suggestion lists for movies and costars.
3. Optional shortest-path hint metadata for each suggestion.
4. Full catalogs for actors and movies so the frontend can create its own game modes.

The frontend is expected to decide how to display, sort, filter, randomize, or rank those results.

## Local Server

Start the backend from the project root:

```bash
uvicorn fastapi_app.main:app --reload
```

Local base URL:

```text
http://localhost:8000
```

Frontend-reachable endpoints to copy and paste:

```text
http://localhost:8000/docs
http://localhost:8000/api/levels
http://localhost:8000/api/actors
http://localhost:8000/api/movies
http://localhost:8000/api/actor/Matt%20Damon
http://localhost:8000/api/actor/1461/movies?target_type=actor&target_id=1892
http://localhost:8000/api/movie/161/costars?exclude=George%20Clooney&target_type=actor&target_id=1892
```

Swagger docs:

```text
http://localhost:8000/docs
```

## Core Game Model

A game can start with any pair of nodes:

1. actor -> actor
2. movie -> movie
3. actor -> movie

The player wins by building a valid alternating path between the two start nodes.

Examples:

1. George Clooney -> Ocean's Eleven -> Matt Damon
2. George Clooney -> The Perfect Storm -> Mark Wahlberg -> The Departed -> Matt Damon

The frontend should treat the API as a graph API:

1. When the current node is an actor, fetch movies for that actor.
2. When the current node is a movie, fetch actors for that movie.
3. Append the selected node to the current path.
4. Optionally use target-aware path hints to highlight promising suggestions.
5. Validate or generate paths with the dedicated path endpoints.

## Design Principle

Popularity is now returned as raw data only.

The backend does not decide how the frontend should use popularity in the UI. The frontend may choose to:

1. Sort by popularity descending.
2. Shuffle first, then display popularity as a secondary label.
3. Ignore popularity entirely.
4. Blend popularity with shortest-path hints.
5. Use different ranking rules for different game modes.

Similarly, shortest-path hint metadata is returned so the frontend can choose whether to surface optimal or near-optimal moves. The backend does not force a single presentation rule.

## Endpoints

### 1. Levels

Use this for predefined actor-vs-actor games.

```http
GET http://localhost:8000/api/levels
```

Example response:

```json
[
  {
    "actor_a": "Matt Damon",
    "actor_b": "George Clooney",
    "stars": 3
  }
]
```

### 2. Full Actor Catalog

Use this for quick play, custom game setup, search, autocomplete, and speed-round modes.

```http
GET http://localhost:8000/api/actors
```

Example response:

```json
[
  {
    "id": 1892,
    "name": "Matt Damon",
    "popularity": 51.25
  },
  {
    "id": 1461,
    "name": "George Clooney",
    "popularity": 33.1
  }
]
```

### 3. Full Movie Catalog

Use this for quick play, custom game setup, search, autocomplete, and speed-round modes.

```http
GET http://localhost:8000/api/movies
```

Example response:

```json
[
  {
    "id": 161,
    "title": "Ocean's Eleven",
    "release_date": "2001-12-07"
  },
  {
    "id": 1422,
    "title": "The Departed",
    "release_date": "2006-10-04"
  }
]
```

### 4. Resolve Actor By Name

Useful when a level gives names but the frontend needs ids.

```http
GET http://localhost:8000/api/actor/Matt%20Damon
```

Example response:

```json
{
  "id": 1892,
  "name": "Matt Damon",
  "popularity": 51.25
}
```

### 5. Get All Movies For An Actor

This returns the full set of movies for the actor, plus optional target-aware path hints.

Without hints:

```http
GET http://localhost:8000/api/actor/1461/movies
```

With hints toward a target actor:

```http
GET http://localhost:8000/api/actor/1461/movies?target_type=actor&target_id=1892
```

Example response:

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
  },
  {
    "id": 10589,
    "title": "The Perfect Storm",
    "release_date": "2000-06-30",
    "path_hint": {
      "reachable": true,
      "steps_to_target": 3,
      "path": [
        { "id": 10589, "type": "movie", "label": "The Perfect Storm" },
        { "id": 13240, "type": "actor", "label": "Mark Wahlberg" },
        { "id": 1422, "type": "movie", "label": "The Departed" },
        { "id": 1892, "type": "actor", "label": "Matt Damon" }
      ]
    }
  }
]
```

How to use it:

1. Show all movies.
2. Sort by title, popularity of connected actors, or custom rules.
3. Highlight movies with lower `steps_to_target` if you want to surface more optimal routes.
4. Ignore `path_hint` entirely if you want a harder mode.

### 6. Get All Actors In A Movie

This returns the full set of actors for a movie, plus optional target-aware path hints.

Without hints:

```http
GET http://localhost:8000/api/movie/161/costars
```

With excludes and hints toward a target actor:

```http
GET http://localhost:8000/api/movie/161/costars?exclude=George%20Clooney&target_type=actor&target_id=1892
```

Example response:

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
  },
  {
    "id": 13240,
    "name": "Mark Wahlberg",
    "popularity": 28.0,
    "path_hint": {
      "reachable": true,
      "steps_to_target": 2,
      "path": [
        { "id": 13240, "type": "actor", "label": "Mark Wahlberg" },
        { "id": 1422, "type": "movie", "label": "The Departed" },
        { "id": 1892, "type": "actor", "label": "Matt Damon" }
      ]
    }
  }
]
```

How to use it:

1. Show all actors in the movie.
2. Use `exclude` to remove actor names already present in the current path.
3. Use `path_hint.steps_to_target` to surface a few optimal or near-optimal branches.
4. Use `popularity` however you want, or ignore it.

### 7. Validate A Path

```http
POST http://localhost:8000/api/path/validate
Content-Type: application/json
```

Body:

```json
{
  "path": ["George Clooney", "Ocean's Eleven", "Matt Damon"]
}
```

Example response:

```json
{
  "valid": true
}
```

### 8. Generate A Path Between Any Two Nodes

Use this for hint systems, solve buttons, path previews, or path-aware UI.

```http
POST http://localhost:8000/api/path/generate
Content-Type: application/json
```

Body:

```json
{
  "a": { "type": "actor", "value": "George Clooney" },
  "b": { "type": "actor", "value": "Matt Damon" }
}
```

Example response:

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

## Suggested Frontend Game Loop

Example for actor -> actor gameplay:

1. Load a start actor and target actor.
2. Resolve names to ids if needed.
3. Store the current path as alternating node labels.
4. When the current node is an actor, call `/api/actor/{actor_id}/movies`.
5. Optionally pass `target_type` and `target_id` to receive path hints.
6. Let the frontend decide how to display the returned list.
7. When the player picks a movie, append it to the path.
8. Call `/api/movie/{movie_id}/costars` with repeated `exclude` values for actors already used in the path.
9. Optionally pass the same target parameters for path hints.
10. Let the frontend decide whether to show all options, a subset, a shuffled set, or a hint-enhanced set.
11. When the player picks an actor, append it to the path and continue.
12. Call `/api/path/validate` to confirm the path.

## How The Frontend Can Use Popularity

The backend does not impose a rule. Example frontend strategies:

1. Sort all actors by popularity descending.
2. Randomly sample actors, then show popularity as a badge.
3. Sort by `path_hint.steps_to_target` first and popularity second.
4. Sort by popularity for quick-play but ignore popularity in challenge mode.
5. Hide popularity from the player but still use it for behind-the-scenes ordering.

## How The Frontend Can Use Optimal Path Data

Every suggestion endpoint can provide `path_hint` data when a target is supplied.

If the returned option is itself the target, the backend will return a `path_hint` with `steps_to_target: 0`. That gives the frontend an exact signal that the player can complete the match immediately with that choice.

That makes it possible for the frontend to:

1. Highlight the few best moves.
2. Show "best path" and "alternate path" badges.
3. Surface a mix of optimal and non-optimal suggestions.
4. Build an easy mode, normal mode, and hard mode from the same API.
5. Show previews of where a move is likely to lead.

## Quick Play And Speed Round

The new catalog endpoints make additional modes possible.

### Quick Play

Use `/api/actors` and `/api/movies` to let the user choose custom start and end nodes:

1. actor -> actor
2. movie -> movie
3. actor -> movie

Then run the normal alternating-node gameplay flow.

### Speed Round

A memory mode can use the raw catalog and suggestion endpoints like this:

1. Let the player choose one actor or movie.
2. If they choose an actor, call `/api/actor/{actor_id}/movies` and ask them to name matching movies.
3. If they choose a movie, call `/api/movie/{movie_id}/costars` and ask them to name matching actors.
4. The frontend decides whether to show all possibilities, none of them, or only partial hints.

## React-Friendly Types

```ts
export type NodeType = "actor" | "movie";

export type NodeSummary = {
  id: number;
  type: NodeType;
  label: string;
};

export type PathHint = {
  reachable: boolean;
  steps_to_target: number | null;
  path: NodeSummary[];
};

export type Actor = {
  id: number;
  name: string;
  popularity: number | null;
};

export type ActorSuggestion = Actor & {
  path_hint?: PathHint;
};

export type Movie = {
  id: number;
  title: string;
  release_date: string | null;
};

export type MovieSuggestion = Movie & {
  path_hint?: PathHint;
};
```

## React-Friendly Request Examples

### Fetch all actors

```ts
export async function fetchActors() {
  const response = await fetch("http://localhost:8000/api/actors");
  if (!response.ok) {
    throw new Error(`Actor catalog failed: ${response.status}`);
  }
  return response.json() as Promise<Actor[]>;
}
```

### Fetch all movies

```ts
export async function fetchMovies() {
  const response = await fetch("http://localhost:8000/api/movies");
  if (!response.ok) {
    throw new Error(`Movie catalog failed: ${response.status}`);
  }
  return response.json() as Promise<Movie[]>;
}
```

### Fetch actor movies with target hints

```ts
export async function fetchActorMovies(actorId: number, targetType?: NodeType, targetId?: number) {
  const params = new URLSearchParams();

  if (targetType && targetId !== undefined) {
    params.set("target_type", targetType);
    params.set("target_id", String(targetId));
  }

  const suffix = params.toString() ? `?${params.toString()}` : "";
  const response = await fetch(`http://localhost:8000/api/actor/${actorId}/movies${suffix}`);

  if (!response.ok) {
    throw new Error(`Actor movies lookup failed: ${response.status}`);
  }

  return response.json() as Promise<MovieSuggestion[]>;
}
```

### Fetch movie actors with excludes and target hints

```ts
export async function fetchMovieActors(movieId: number, excludedNames: string[], targetType?: NodeType, targetId?: number) {
  const params = new URLSearchParams();

  for (const name of excludedNames) {
    params.append("exclude", name);
  }

  if (targetType && targetId !== undefined) {
    params.set("target_type", targetType);
    params.set("target_id", String(targetId));
  }

  const response = await fetch(
    `http://localhost:8000/api/movie/${movieId}/costars?${params.toString()}`
  );

  if (!response.ok) {
    throw new Error(`Movie actors lookup failed: ${response.status}`);
  }

  return response.json() as Promise<ActorSuggestion[]>;
}
```

## Cross-Port Note

If the frontend runs on another localhost port such as `http://localhost:5173`, it should still call this backend at `http://localhost:8000`.

If the browser blocks the requests, enable CORS in the FastAPI app.# Frontend Versus Integration Guide

This guide is written for a frontend agent or developer that needs to call the local Co-Stars backend and reproduce the same decision logic used by the backend versus game.

## Local Server

Run the backend from the project root:

```bash
uvicorn fastapi_app.main:app --reload
```

When running locally, the base URL is:

```text
http://localhost:8000
```

Swagger docs are available at:

```text
http://localhost:8000/docs
```

## Goal

The frontend should be able to:

1. Start from one actor.
2. Show movie choices for the current actor.
3. After the player picks a movie, show costar choices that match the backend versus-game selection logic.
4. Continue alternating actor -> movie -> actor until the target actor is reached.
5. Validate the final path with the backend.

## Backend Logic To Match

The backend versus game does not simply show the full cast in arbitrary order.

For costar choices, the backend logic is:

1. Fetch candidate actors for the chosen movie.
2. Exclude any actor names already present in the current path.
3. Build a random pool of up to 20 actors.
4. Sort that pool by popularity descending.
5. Return the top 6 choices.

The API now exposes that exact behavior through `selection_mode=versus`.

## Endpoints To Use

### 1. Get levels

Use this to load predefined actor matchups.

```http
GET http://localhost:8000/api/levels
```

Example response:

```json
[
  {
    "actor_a": "Matt Damon",
    "actor_b": "Daniel Craig",
    "stars": 3
  }
]
```

### 2. Resolve an actor by name

Use this when the frontend needs the actor id and popularity for a known actor name.

```http
GET http://localhost:8000/api/actor/Matt Damon
```

Example response:

```json
{
  "id": 1892,
  "name": "Matt Damon",
  "popularity": 51.25
}
```

### 3. Get all movies for the current actor

Use this after an actor is selected.

```http
GET http://localhost:8000/api/actor/1892/movies
```

Example response:

```json
[
  {
    "id": 453,
    "title": "A Beautiful Mind"
  },
  {
    "id": 98,
    "title": "Gladiator"
  }
]
```

Important: this endpoint returns the actor's movies, but it does not currently apply the CLI's random 6-movie sampling logic. If the frontend wants the movie picker to feel exactly like the CLI, the frontend should randomize or limit the movie list on its own.

### 4. Get versus-mode costar choices for a movie

This is the critical endpoint for matching the backend versus-game logic.

```http
GET http://localhost:8000/api/movie/453/costars?selection_mode=versus&exclude=Matt%20Damon&exclude=Robin%20Williams
```

Use repeated `exclude` query parameters for every actor name that is already in the current path.

Example response:

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

Interpretation:

1. The list is already sorted for frontend use.
2. `popularity_rank = 1` is the highest-ranked costar within the selected versus pool.
3. The frontend should display these options in the order returned.
4. The frontend should not re-sort this list if it wants to match backend behavior.

### 5. Validate a completed or in-progress path

Use this to confirm that the path alternates correctly and that each actor/movie connection is valid.

```http
POST http://localhost:8000/api/path/validate
Content-Type: application/json
```

Body:

```json
{
  "path": ["Matt Damon", "Ocean's Eleven", "Brad Pitt"]
}
```

Example response:

```json
{
  "valid": true
}
```

### 6. Generate a path between two actors

Use this if the frontend wants hints, automated solving, or a fallback path generator.

```http
POST http://localhost:8000/api/path/generate
Content-Type: application/json
```

Body:

```json
{
  "a": { "type": "actor", "value": "Matt Damon" },
  "b": { "type": "actor", "value": "Daniel Craig" }
}
```

## Frontend Game Loop

The frontend should maintain a path array of alternating actor and movie names.

Example path state:

```json
[
  "Matt Damon",
  "Ocean's Eleven",
  "Brad Pitt"
]
```

Recommended turn flow:

1. Pick a level from `/api/levels`.
2. Resolve both actor names with `/api/actor/{name}` if ids or popularity are needed.
3. Let the player choose the starting actor.
4. Store the current path as `[startingActorName]`.
5. Load movies with `/api/actor/{actor_id}/movies`.
6. When the player picks a movie, append the movie title to the path.
7. Build an exclude list from actor names already in the path.
8. Call `/api/movie/{movie_id}/costars?selection_mode=versus` with repeated `exclude` params.
9. Render the returned costars in the order given.
10. When the player picks a costar, append that actor name to the path.
11. If the chosen actor matches the target actor, the round is complete.
12. Optionally call `/api/path/validate` before declaring success.
13. Otherwise repeat from the movie-fetch step using the newly selected actor.

## React-Friendly Request Examples

### Fetch actor details

```ts
export async function fetchActorByName(name: string) {
  const response = await fetch(
    `http://localhost:8000/api/actor/${encodeURIComponent(name)}`
  );

  if (!response.ok) {
    throw new Error(`Actor lookup failed: ${response.status}`);
  }

  return response.json() as Promise<{
    id: number;
    name: string;
    popularity: number | null;
  }>;
}
```

### Fetch versus-mode costars

```ts
type Costar = {
  id: number;
  name: string;
  popularity: number | null;
  popularity_rank: number;
};

export async function fetchVersusCostars(movieId: number, excludedNames: string[]) {
  const params = new URLSearchParams();
  params.set("selection_mode", "versus");

  for (const name of excludedNames) {
    params.append("exclude", name);
  }

  const response = await fetch(
    `http://localhost:8000/api/movie/${movieId}/costars?${params.toString()}`
  );

  if (!response.ok) {
    throw new Error(`Costar lookup failed: ${response.status}`);
  }

  return response.json() as Promise<Costar[]>;
}
```

### Validate a path

```ts
export async function validatePath(path: string[]) {
  const response = await fetch("http://localhost:8000/api/path/validate", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({ path }),
  });

  if (!response.ok) {
    throw new Error(`Path validation failed: ${response.status}`);
  }

  return response.json() as Promise<{ valid: boolean; message?: string }>;
}
```

## Recommended Frontend Types

```ts
export type Actor = {
  id: number;
  name: string;
  popularity: number | null;
};

export type Movie = {
  id: number;
  title: string;
};

export type RankedCostar = {
  id: number;
  name: string;
  popularity: number | null;
  popularity_rank: number;
};

export type Level = {
  actor_a: string;
  actor_b: string;
  stars: number;
};
```

## Important Behavior Notes

1. For costar picks, use the list returned by the API exactly as-is.
2. Do not sort the returned costars again on the frontend.
3. Always pass the current path's actor names as `exclude` values when requesting new costars.
4. `selection_mode=versus` is the endpoint mode that matches the backend game's popularity logic.
5. `selection_mode=all` is useful for inspection or alternate UI flows, but not for matching the versus game.

## Minimal Frontend Algorithm

```text
currentPath = [startingActorName]
currentActor = startingActor

while currentActor.name !== targetActor.name:
  movies = GET /api/actor/{currentActor.id}/movies
  chosenMovie = player selects movie
  currentPath.append(chosenMovie.title)

  excludedActorNames = every actor name already present in currentPath
  costars = GET /api/movie/{chosenMovie.id}/costars?selection_mode=versus&exclude=...
  chosenCostar = player selects costar from returned order
  currentPath.append(chosenCostar.name)

  currentActor = chosenCostar

POST /api/path/validate with currentPath
```

## If The Frontend Runs On A Different Port

If your React app runs on something like `http://localhost:5173`, it should still call this backend at:

```text
http://localhost:8000
```

If the browser blocks those requests, enable or configure CORS in the FastAPI app. The current guide only covers the request contract, not CORS configuration.