CREATE TABLE IF NOT EXISTS sessions (
  session_id TEXT PRIMARY KEY,
  date TIMESTAMP NOT NULL,
  tag TEXT,
  comment TEXT,
  countdown_time INTEGER,
  unit TEXT,
  left_right BOOLEAN,
  alternate_mode TEXT,
  initial_side TEXT,
  switch_side_time INTEGER,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  UNIQUE (date, tag)
);

CREATE TABLE IF NOT EXISTS exercises (
  exercise_id INTEGER PRIMARY KEY AUTOINCREMENT,
  session_id TEXT NOT NULL,
  name TEXT NOT NULL,
  name_normalized TEXT NOT NULL,
  FOREIGN KEY (session_id) REFERENCES sessions (session_id),
  UNIQUE (session_id, name)
);

CREATE TABLE IF NOT EXISTS timeline (
  timeline_id INTEGER PRIMARY KEY AUTOINCREMENT,
  session_id TEXT NOT NULL,
  type TEXT NOT NULL,
  start_time TEXT,
  end_time TEXT,
  duration TEXT,
  side TEXT,
  target_low_pct REAL,
  target_high_pct REAL,
  mvc_data TEXT,
  set_num INTEGER,
  rep_num INTEGER,
  exercise_name TEXT,
  FOREIGN KEY (session_id) REFERENCES sessions (session_id)
);

CREATE TABLE IF NOT EXISTS reps (
  rep_id TEXT PRIMARY KEY,
  session_id TEXT NOT NULL,
  exercise_id INTEGER NOT NULL,
  set_num INTEGER NOT NULL,
  rep_num INTEGER NOT NULL,
  side TEXT NOT NULL,
  timeseries_path TEXT,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (session_id) REFERENCES sessions (session_id),
  FOREIGN KEY (exercise_id) REFERENCES exercises (exercise_id),
  UNIQUE (session_id, exercise_id, set_num, rep_num, side)
);

CREATE TABLE IF NOT EXISTS rep_stats (
  stat_id INTEGER PRIMARY KEY AUTOINCREMENT,
  rep_id TEXT NOT NULL,
  avg_weight REAL,
  peak_weight REAL,
  rfd2080 REAL,
  FOREIGN KEY (rep_id) REFERENCES reps (rep_id),
  UNIQUE (rep_id)
);

CREATE TABLE IF NOT EXISTS set_stats (
  stat_id INTEGER PRIMARY KEY AUTOINCREMENT,
  session_id TEXT NOT NULL,
  exercise_id INTEGER NOT NULL,
  set_num INTEGER NOT NULL,
  side TEXT NOT NULL,
  avg_weight REAL,
  peak_weight REAL,
  rfd2080 REAL,
  FOREIGN KEY (session_id) REFERENCES sessions (session_id),
  FOREIGN KEY (exercise_id) REFERENCES exercises (exercise_id),
  UNIQUE (session_id, exercise_id, set_num, side)
);

CREATE TABLE IF NOT EXISTS peakloads (
  peakload_id INTEGER PRIMARY KEY AUTOINCREMENT,
  date TIMESTAMP NOT NULL,
  tag TEXT,
  comment TEXT,
  unit TEXT,
  type TEXT,
  left_max_weight REAL,
  right_max_weight REAL,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  UNIQUE (date, tag)
);

CREATE INDEX IF NOT EXISTS idx_sessions_date ON sessions (date);

CREATE INDEX IF NOT EXISTS idx_sessions_tag ON sessions (tag);

CREATE INDEX IF NOT EXISTS idx_exercises_session ON exercises (session_id);

CREATE INDEX IF NOT EXISTS idx_reps_session ON reps (session_id);

CREATE INDEX IF NOT EXISTS idx_reps_exercise ON reps (exercise_id);

CREATE INDEX IF NOT EXISTS idx_timeline_session ON timeline (session_id);

CREATE INDEX IF NOT EXISTS idx_peakloads_date ON peakloads (date);

CREATE INDEX IF NOT EXISTS idx_peakloads_tag ON peakloads (tag);
