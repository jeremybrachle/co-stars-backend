import json
from pathlib import Path

from db_helper import get_actor_by_id, get_movie_by_id


ROOT = Path(__file__).resolve().parent
V1_LEVELS_FILE = ROOT / "levels_v1.json"
V2_LEVELS_FILE = ROOT / "levels.json"


def _read_json(path):
    return json.loads(path.read_text(encoding="utf-8"))


def load_v1_levels():
    levels = _read_json(V1_LEVELS_FILE)
    if not isinstance(levels, list):
        raise ValueError("levels_v1.json must contain a top-level JSON array.")
    return levels


def load_v2_levels_document():
    document = _read_json(V2_LEVELS_FILE)
    if not isinstance(document, dict):
        raise ValueError("levels.json must contain a top-level JSON object.")

    levels = document.get("levels")
    if not isinstance(levels, list):
        raise ValueError("levels.json must include a top-level 'levels' array.")

    return document


def _require_non_empty_string(value, field_name):
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"Expected non-empty string for {field_name}.")
    return value.strip()


def _normalize_notes(notes):
    if notes is None:
        return {"text": ""}
    if not isinstance(notes, dict):
        raise ValueError("Game notes must be an object when provided.")

    text = notes.get("text", "")
    if not isinstance(text, str):
        raise ValueError("Game notes.text must be a string.")

    normalized = dict(notes)
    normalized["text"] = text
    return normalized


def _normalize_settings(settings):
    if settings is None:
        return {}
    if not isinstance(settings, dict):
        raise ValueError("Game settings must be an object when provided.")
    return dict(settings)


def _resolve_node(node, field_name):
    if not isinstance(node, dict):
        raise ValueError(f"{field_name} must be an object.")

    node_id = node.get("id")
    if not isinstance(node_id, int):
        raise ValueError(f"{field_name}.id must be an integer.")

    node_type = _require_non_empty_string(node.get("type"), f"{field_name}.type")
    if node_type not in {"actor", "movie"}:
        raise ValueError(f"{field_name}.type must be 'actor' or 'movie'.")

    raw_label = _require_non_empty_string(node.get("label"), f"{field_name}.label")

    if node_type == "actor":
        record = get_actor_by_id(node_id)
        if record is None:
            raise ValueError(f"{field_name} references missing actor id {node_id}.")
        canonical_label = record[1]
    else:
        record = get_movie_by_id(node_id)
        if record is None:
            raise ValueError(f"{field_name} references missing movie id {node_id}.")
        canonical_label = record[1]

    return {
        "id": node_id,
        "type": node_type,
        "label": canonical_label if raw_label.strip() else canonical_label,
    }


def build_v2_levels_export(document=None):
    document = document or load_v2_levels_document()
    schema_version = document.get("schema-version", 2)
    levels = []

    for level in document["levels"]:
        if not isinstance(level, dict):
            raise ValueError("Each v2 level must be an object.")

        level_id = _require_non_empty_string(level.get("level-id"), "level-id")
        level_name = _require_non_empty_string(level.get("level-name"), "level-name")
        game_data = level.get("game-data", [])
        if not isinstance(game_data, list):
            raise ValueError(f"Level {level_id} game-data must be an array.")

        normalized_games = []
        for game in game_data:
            if not isinstance(game, dict):
                raise ValueError(f"Level {level_id} contains a non-object game entry.")

            game_id = _require_non_empty_string(game.get("game-id"), "game-id")
            game_type = _require_non_empty_string(game.get("game-type"), "game-type")

            normalized_games.append(
                {
                    "game-id": game_id,
                    "game-type": game_type,
                    "startNode": _resolve_node(game.get("startNode"), "startNode"),
                    "targetNode": _resolve_node(game.get("targetNode"), "targetNode"),
                    "notes": _normalize_notes(game.get("notes")),
                    "settings": _normalize_settings(game.get("settings")),
                }
            )

        levels.append(
            {
                "level-id": level_id,
                "level-name": level_name,
                "game-data": normalized_games,
            }
        )

    return {
        "schema-version": schema_version,
        "levels": levels,
    }


def summarize_v2_levels(document):
    levels = document.get("levels", [])
    total_games = 0
    boss_games = 0

    for level in levels:
        for game in level.get("game-data", []):
            total_games += 1
            if game.get("game-type") == "boss-mode":
                boss_games += 1

    return {
        "level_group_count": len(levels),
        "level_count": total_games,
        "boss_game_count": boss_games,
        "normal_game_count": total_games - boss_games,
    }