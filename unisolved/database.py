from __future__ import annotations

import json
import sqlite3
from pathlib import Path

from unisolved.models import Mentor, Resource, Restaurant
from unisolved.seed_data import SEED_MENTORS, SEED_RESOURCES, SEED_RESTAURANTS, SEED_VERSION


def _connect(db_path: Path) -> sqlite3.Connection:
    db_path.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(db_path)
    connection.row_factory = sqlite3.Row
    return connection


def ensure_database(db_path: Path) -> None:
    with _connect(db_path) as connection:
        connection.executescript(
            """
            CREATE TABLE IF NOT EXISTS app_metadata (
                key TEXT PRIMARY KEY,
                value TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS mentors (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                phone TEXT NOT NULL,
                email TEXT NOT NULL,
                program TEXT NOT NULL,
                year INTEGER NOT NULL,
                languages TEXT NOT NULL,
                courses TEXT NOT NULL,
                help_topics TEXT NOT NULL,
                bio TEXT NOT NULL,
                availability TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS resources (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                category TEXT NOT NULL,
                campus TEXT NOT NULL,
                area TEXT NOT NULL,
                description TEXT NOT NULL,
                tags TEXT NOT NULL,
                source_url TEXT NOT NULL,
                is_official INTEGER NOT NULL
            );

            CREATE TABLE IF NOT EXISTS restaurants (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                category TEXT NOT NULL,
                campus TEXT NOT NULL,
                area TEXT NOT NULL,
                description TEXT NOT NULL,
                tags TEXT NOT NULL,
                source_url TEXT NOT NULL,
                is_official INTEGER NOT NULL
            );
            """
        )

        current_version = connection.execute(
            "SELECT value FROM app_metadata WHERE key = 'seed_version'"
        ).fetchone()
        if current_version and current_version["value"] == str(SEED_VERSION):
            return

        connection.execute("DELETE FROM mentors")
        connection.execute("DELETE FROM resources")
        connection.execute("DELETE FROM restaurants")

        connection.executemany(
            """
            INSERT INTO mentors (
                name, phone, email, program, year, languages, courses, help_topics, bio, availability
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            [
                (
                    mentor["name"],
                    mentor["phone"],
                    mentor["email"],
                    mentor["program"],
                    mentor["year"],
                    json.dumps(mentor["languages"]),
                    json.dumps(mentor["courses"]),
                    json.dumps(mentor["help_topics"]),
                    mentor["bio"],
                    mentor["availability"],
                )
                for mentor in SEED_MENTORS
            ],
        )
        connection.executemany(
            """
            INSERT INTO resources (
                name, category, campus, area, description, tags, source_url, is_official
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            [
                (
                    resource["name"],
                    resource["category"],
                    resource["campus"],
                    resource["area"],
                    resource["description"],
                    json.dumps(resource["tags"]),
                    resource["source_url"],
                    int(resource["is_official"]),
                )
                for resource in SEED_RESOURCES
            ],
        )
        connection.executemany(
            """
            INSERT INTO restaurants (
                name, category, campus, area, description, tags, source_url, is_official
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            [
                (
                    restaurant["name"],
                    restaurant["category"],
                    restaurant["campus"],
                    restaurant["area"],
                    restaurant["description"],
                    json.dumps(restaurant["tags"]),
                    restaurant["source_url"],
                    int(restaurant["is_official"]),
                )
                for restaurant in SEED_RESTAURANTS
            ],
        )
        connection.execute(
            """
            INSERT INTO app_metadata (key, value)
            VALUES ('seed_version', ?)
            ON CONFLICT(key) DO UPDATE SET value = excluded.value
            """,
            (str(SEED_VERSION),),
        )


def fetch_mentors(db_path: Path) -> list[Mentor]:
    with _connect(db_path) as connection:
        rows = connection.execute(
            """
            SELECT name, phone, email, program, year, languages, courses, help_topics, bio, availability
            FROM mentors
            ORDER BY year DESC, name ASC
            """
        ).fetchall()
    return [
        Mentor(
            name=row["name"],
            phone=row["phone"],
            email=row["email"],
            program=row["program"],
            year=row["year"],
            languages=json.loads(row["languages"]),
            courses=json.loads(row["courses"]),
            help_topics=json.loads(row["help_topics"]),
            bio=row["bio"],
            availability=row["availability"],
        )
        for row in rows
    ]


def fetch_resources(db_path: Path) -> list[Resource]:
    with _connect(db_path) as connection:
        rows = connection.execute(
            """
            SELECT name, category, campus, area, description, tags, source_url, is_official
            FROM resources
            ORDER BY is_official DESC, name ASC
            """
        ).fetchall()
    return [
        Resource(
            name=row["name"],
            category=row["category"],
            campus=row["campus"],
            area=row["area"],
            description=row["description"],
            tags=json.loads(row["tags"]),
            source_url=row["source_url"],
            is_official=bool(row["is_official"]),
        )
        for row in rows
    ]


def fetch_restaurants(db_path: Path) -> list[Restaurant]:
    with _connect(db_path) as connection:
        rows = connection.execute(
            """
            SELECT name, category, campus, area, description, tags, source_url, is_official
            FROM restaurants
            ORDER BY name ASC
            """
        ).fetchall()
    return [
        Restaurant(
            name=row["name"],
            category=row["category"],
            campus=row["campus"],
            area=row["area"],
            description=row["description"],
            tags=json.loads(row["tags"]),
            source_url=row["source_url"],
            is_official=bool(row["is_official"]),
        )
        for row in rows
    ]
