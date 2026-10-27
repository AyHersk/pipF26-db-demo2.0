#!/usr/bin/env python3
"""Apply schema.sql and load class_dataset.csv into Railway Postgres."""

from __future__ import annotations

import csv
import os
import re
from pathlib import Path

import psycopg2

ROOT = Path(__file__).resolve().parent
ENV_PATH = ROOT / ".env"
SCHEMA_PATH = ROOT / "schema.sql"
CSV_PATH = ROOT / "class_dataset.csv"

KNOWN_TOOLS = {"Python", "JavaScript", "SQL", "Excel", "R"}
SLOT_RE = re.compile(r"^(Weekday|Weekend)\s+(mornings|afternoons|evenings)$")


def load_database_url() -> str:
    url = os.environ.get("DATABASE_URL")
    if ENV_PATH.exists():
        for raw in ENV_PATH.read_text().splitlines():
            line = raw.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, value = line.split("=", 1)
            if key.strip() == "DATABASE_URL":
                url = value.strip().strip('"').strip("'")
                break
            if url is None and "postgresql" in value.lower():
                url = value.strip().strip('"').strip("'")
    if not url:
        raise SystemExit(
            ".env is empty or missing DATABASE_URL. Save your Railway "
            "Postgres URL as DATABASE_URL=postgresql://..."
        )
    if url.startswith("postgres://"):
        url = "postgresql://" + url[len("postgres://") :]
    return url


def parse_tools(raw: str) -> list[str]:
    tools = []
    for part in raw.split(";"):
        name = part.strip()
        if not name or name.lower() == "none yet":
            continue
        if name not in KNOWN_TOOLS:
            raise ValueError(f"Unknown tool {name!r}")
        if name not in tools:
            tools.append(name)
    return tools


def parse_slots(raw: str) -> list[tuple[str, str]]:
    slots = []
    for part in raw.split(";"):
        label = " ".join(part.strip().split())
        if not label:
            continue
        match = SLOT_RE.match(label)
        if not match:
            raise ValueError(f"Unknown availability {label!r}")
        slot = (match.group(1), match.group(2))
        if slot not in slots:
            slots.append(slot)
    return slots


def main() -> None:
    url = load_database_url()
    conn = psycopg2.connect(url)
    conn.autocommit = False
    try:
        with conn.cursor() as cur:
            cur.execute(
                """
                DROP TABLE IF EXISTS student_availability, student_tools,
                    students, tools, availability_slots CASCADE
                """
            )
            cur.execute(SCHEMA_PATH.read_text())

            cur.execute("SELECT tool_id, name FROM tools")
            tool_ids = {name: tool_id for tool_id, name in cur.fetchall()}
            cur.execute(
                "SELECT slot_id, day_group, time_of_day FROM availability_slots"
            )
            slot_ids = {
                (day_group, time_of_day): slot_id
                for slot_id, day_group, time_of_day in cur.fetchall()
            }

            student_count = 0
            tool_links = 0
            slot_links = 0
            with CSV_PATH.open(newline="", encoding="utf-8") as fh:
                reader = csv.DictReader(fh)
                for row in reader:
                    cur.execute(
                        """
                        INSERT INTO students (
                            netid, name, school_year, intro_programming,
                            skill_programming, skill_data_stats,
                            skill_frontend_design, skill_business_pitch,
                            working_style, interests, semester_goal,
                            submitted_at
                        ) VALUES (
                            %(netid)s, %(name)s, %(school_year)s,
                            %(intro_programming)s, %(skill_programming)s,
                            %(skill_data_stats)s, %(skill_frontend_design)s,
                            %(skill_business_pitch)s, %(working_style)s,
                            %(interests)s, %(semester_goal)s, %(submitted_at)s
                        )
                        """,
                        {
                            "netid": row["netid"].strip(),
                            "name": row["name"].strip(),
                            "school_year": row["school_year"].strip(),
                            "intro_programming": row["intro_programming"].strip(),
                            "skill_programming": int(row["skill_programming"]),
                            "skill_data_stats": int(row["skill_data_stats"]),
                            "skill_frontend_design": int(
                                row["skill_frontend_design"]
                            ),
                            "skill_business_pitch": int(
                                row["skill_business_pitch"]
                            ),
                            "working_style": row["working_style"].strip() or None,
                            "interests": row["interests"].strip() or None,
                            "semester_goal": row["semester_goal"].strip() or None,
                            "submitted_at": row["submitted_at"].strip(),
                        },
                    )
                    student_count += 1
                    netid = row["netid"].strip()
                    for tool in parse_tools(row["tools"]):
                        cur.execute(
                            """
                            INSERT INTO student_tools (netid, tool_id)
                            VALUES (%s, %s)
                            """,
                            (netid, tool_ids[tool]),
                        )
                        tool_links += 1
                    for slot in parse_slots(row["availability"]):
                        cur.execute(
                            """
                            INSERT INTO student_availability (netid, slot_id)
                            VALUES (%s, %s)
                            """,
                            (netid, slot_ids[slot]),
                        )
                        slot_links += 1

        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()

    print(
        f"Loaded {student_count} students, {tool_links} tool links, "
        f"{slot_links} availability links."
    )


if __name__ == "__main__":
    main()
