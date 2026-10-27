-- Class survey schema derived from class_dataset.csv
-- One student row in the CSV becomes one students row plus
-- many-to-many rows for tools and availability slots.

CREATE TABLE students (
    netid               TEXT PRIMARY KEY,
    name                TEXT NOT NULL,
    school_year         TEXT NOT NULL CHECK (school_year IN ('Sophomore', 'Junior', 'Senior')),
    intro_programming   TEXT NOT NULL CHECK (intro_programming IN ('took_it', 'equivalent', 'neither')),
    skill_programming   INTEGER NOT NULL CHECK (skill_programming BETWEEN 1 AND 5),
    skill_data_stats    INTEGER NOT NULL CHECK (skill_data_stats BETWEEN 1 AND 5),
    skill_frontend_design INTEGER NOT NULL CHECK (skill_frontend_design BETWEEN 1 AND 5),
    skill_business_pitch INTEGER NOT NULL CHECK (skill_business_pitch BETWEEN 1 AND 5),
    working_style       TEXT,
    interests           TEXT,
    semester_goal       TEXT,
    submitted_at        TIMESTAMPTZ NOT NULL
);

CREATE TABLE tools (
    tool_id   INTEGER PRIMARY KEY,
    name      TEXT NOT NULL UNIQUE
);

CREATE TABLE student_tools (
    netid     TEXT NOT NULL REFERENCES students (netid) ON DELETE CASCADE,
    tool_id   INTEGER NOT NULL REFERENCES tools (tool_id) ON DELETE RESTRICT,
    PRIMARY KEY (netid, tool_id)
);

CREATE TABLE availability_slots (
    slot_id      INTEGER PRIMARY KEY,
    day_group    TEXT NOT NULL CHECK (day_group IN ('Weekday', 'Weekend')),
    time_of_day  TEXT NOT NULL CHECK (time_of_day IN ('mornings', 'afternoons', 'evenings')),
    UNIQUE (day_group, time_of_day)
);

CREATE TABLE student_availability (
    netid    TEXT NOT NULL REFERENCES students (netid) ON DELETE CASCADE,
    slot_id  INTEGER NOT NULL REFERENCES availability_slots (slot_id) ON DELETE RESTRICT,
    PRIMARY KEY (netid, slot_id)
);

INSERT INTO availability_slots (slot_id, day_group, time_of_day) VALUES
    (1, 'Weekday', 'mornings'),
    (2, 'Weekday', 'afternoons'),
    (3, 'Weekday', 'evenings'),
    (4, 'Weekend', 'mornings'),
    (5, 'Weekend', 'afternoons'),
    (6, 'Weekend', 'evenings');

INSERT INTO tools (tool_id, name) VALUES
    (1, 'Python'),
    (2, 'JavaScript'),
    (3, 'SQL'),
    (4, 'Excel'),
    (5, 'R');
