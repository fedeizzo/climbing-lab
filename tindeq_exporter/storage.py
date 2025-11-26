import sqlite3
import pandas as pd
from pathlib import Path
from typing import Optional, List, Dict, Tuple
from datetime import datetime
import hashlib


class TindeqStorage:
    """
    Manages storage of Tindeq training data using SQLite + Parquet files.

    Schema supports any custom training pattern with flexible exercise/set/rep structure.
    """

    def __init__(self, storage_path: str = "tindeq_data"):
        """
        Initialize storage manager

        Args:
            storage_path: Root directory for data storage
        """
        self.storage_path = Path(storage_path)
        self.storage_path.mkdir(exist_ok=True)

        self.db_path = self.storage_path / "metadata.db"
        self.timeseries_path = self.storage_path / "timeseries"
        self.timeseries_path.mkdir(exist_ok=True)

        self._init_database()

    def _init_database(self):
        """Create database schema if not exists"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Sessions table - main metadata
        cursor.execute("""
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
                UNIQUE(date, tag)
            )
        """)

        # Exercises table - flexible to support any exercise type
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS exercises (
                exercise_id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id TEXT NOT NULL,
                name TEXT NOT NULL,
                name_normalized TEXT NOT NULL,
                FOREIGN KEY (session_id) REFERENCES sessions(session_id),
                UNIQUE(session_id, name)
            )
        """)

        # Timeline table - captures the workout structure
        cursor.execute("""
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
                FOREIGN KEY (session_id) REFERENCES sessions(session_id)
            )
        """)

        # Reps table - individual rep metadata
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS reps (
                rep_id TEXT PRIMARY KEY,
                session_id TEXT NOT NULL,
                exercise_id INTEGER NOT NULL,
                set_num INTEGER NOT NULL,
                rep_num INTEGER NOT NULL,
                side TEXT NOT NULL,
                timeseries_path TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (session_id) REFERENCES sessions(session_id),
                FOREIGN KEY (exercise_id) REFERENCES exercises(exercise_id),
                UNIQUE(session_id, exercise_id, set_num, rep_num, side)
            )
        """)

        # Rep stats table - aggregated metrics per rep
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS rep_stats (
                stat_id INTEGER PRIMARY KEY AUTOINCREMENT,
                rep_id TEXT NOT NULL,
                avg_weight REAL,
                peak_weight REAL,
                rfd2080 REAL,
                FOREIGN KEY (rep_id) REFERENCES reps(rep_id),
                UNIQUE(rep_id)
            )
        """)

        # Set stats table - aggregated metrics per set
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS set_stats (
                stat_id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id TEXT NOT NULL,
                exercise_id INTEGER NOT NULL,
                set_num INTEGER NOT NULL,
                side TEXT NOT NULL,
                avg_weight REAL,
                peak_weight REAL,
                rfd2080 REAL,
                FOREIGN KEY (session_id) REFERENCES sessions(session_id),
                FOREIGN KEY (exercise_id) REFERENCES exercises(exercise_id),
                UNIQUE(session_id, exercise_id, set_num, side)
            )
        """)

        # Indexes for common queries
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_sessions_date ON sessions(date)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_sessions_tag ON sessions(tag)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_exercises_session ON exercises(session_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_reps_session ON reps(session_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_reps_exercise ON reps(exercise_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_timeline_session ON timeline(session_id)")

        conn.commit()
        conn.close()

    def _generate_session_id(self, date: datetime, tag: str) -> str:
        """Generate unique session ID from date and tag"""
        unique_str = f"{date.isoformat()}_{tag}"
        return hashlib.md5(unique_str.encode()).hexdigest()[:16]

    def _generate_rep_id(self, session_id: str, exercise_id: int,
                         set_num: int, rep_num: int, side: str) -> str:
        """Generate unique rep ID"""
        unique_str = f"{session_id}_{exercise_id}_s{set_num}_r{rep_num}_{side}"
        return hashlib.md5(unique_str.encode()).hexdigest()[:16]

    def import_session(self, tindeq_session):
        """
        Import a TindeqSession into storage

        Args:
            tindeq_session: Instance of TindeqSession class
        """
        from .processor import TindeqSession

        if not isinstance(tindeq_session, TindeqSession):
            raise ValueError("Must provide a TindeqSession instance")

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        try:
            # Load session settings
            settings = tindeq_session.get_settings()
            date_str = settings['Date'].iloc[0]
            date = pd.to_datetime(date_str)
            tag = settings['Tag'].iloc[0]

            session_id = self._generate_session_id(date, tag)

            # Check if session already exists
            cursor.execute("SELECT session_id FROM sessions WHERE session_id = ?", (session_id,))
            if cursor.fetchone():
                print(f"Session {tag} from {date_str} already exists, skipping")
                conn.close()
                return session_id

            # Insert session
            cursor.execute("""
                INSERT INTO sessions
                (session_id, date, tag, comment, countdown_time, unit, left_right,
                 alternate_mode, initial_side, switch_side_time)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                session_id,
                date_str,
                tag,
                settings.get('Comment', [None]).iloc[0],
                settings.get('Countdown Time', [None]).iloc[0],
                settings.get('Unit', [None]).iloc[0],
                settings.get('Left/Right', [None]).iloc[0] == 'Yes',
                settings.get('Alternate Mode', [None]).iloc[0],
                settings.get('Initial Side', [None]).iloc[0],
                settings.get('Switch Side Time', [None]).iloc[0]
            ))

            # Import timeline
            timeline = tindeq_session.get_timeline()
            for _, row in timeline.iterrows():
                cursor.execute("""
                    INSERT INTO timeline
                    (session_id, type, start_time, end_time, duration, side,
                     target_low_pct, target_high_pct, mvc_data, set_num, rep_num, exercise_name)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    session_id,
                    row['Type'],
                    row.get('Start Time'),
                    row.get('End Time'),
                    row.get('Duration'),
                    row.get('Side'),
                    row.get('Target Low (%)'),
                    row.get('Target High (%)'),
                    row.get('MVC'),
                    row.get('Set'),
                    row.get('Rep'),
                    row.get('Name')
                ))

            # Import exercises and their data
            exercises = tindeq_session.list_exercises()

            for exercise_name in exercises:
                # Insert exercise
                exercise_normalized = exercise_name.lower().replace(" ", "_")
                cursor.execute("""
                    INSERT INTO exercises (session_id, name, name_normalized)
                    VALUES (?, ?, ?)
                """, (session_id, exercise_name, exercise_normalized))
                exercise_id = cursor.lastrowid

                # Load rep stats
                try:
                    reps_stats, sets_stats = tindeq_session.get_exercise_stats(exercise_name)

                    # Import set stats
                    for _, stat_row in sets_stats.iterrows():
                        for side in ['left', 'right']:
                            if f'Average Weight {side.capitalize()}' in stat_row:
                                cursor.execute("""
                                    INSERT INTO set_stats
                                    (session_id, exercise_id, set_num, side, avg_weight, peak_weight, rfd2080)
                                    VALUES (?, ?, ?, ?, ?, ?, ?)
                                """, (
                                    session_id,
                                    exercise_id,
                                    stat_row['Set'],
                                    side,
                                    stat_row.get(f'Average Weight {side.capitalize()}'),
                                    stat_row.get(f'Peak Weight {side.capitalize()}'),
                                    stat_row.get(f'RFD2080 {side.capitalize()}')
                                ))

                    # Import rep stats and timeseries data
                    for _, stat_row in reps_stats.iterrows():
                        set_num = int(stat_row['Set'])
                        rep_num = int(stat_row['Rep'])

                        for side in ['left', 'right']:
                            if f'Average Weight {side.capitalize()}' in stat_row:
                                # Generate rep ID
                                rep_id = self._generate_rep_id(session_id, exercise_id,
                                                               set_num, rep_num, side)

                                # Save timeseries data to parquet
                                try:
                                    rep_data = tindeq_session.get_rep_data(
                                        exercise_name, set_num, rep_num, side
                                    )

                                    # Organize by year-month
                                    year_month = date.strftime("%Y-%m")
                                    month_dir = self.timeseries_path / year_month
                                    month_dir.mkdir(exist_ok=True)

                                    parquet_filename = f"{rep_id}.parquet"
                                    parquet_path = month_dir / parquet_filename
                                    rep_data.to_parquet(parquet_path, index=False)

                                    relative_path = f"{year_month}/{parquet_filename}"
                                except FileNotFoundError:
                                    relative_path = None

                                # Insert rep
                                cursor.execute("""
                                    INSERT INTO reps
                                    (rep_id, session_id, exercise_id, set_num, rep_num, side, timeseries_path)
                                    VALUES (?, ?, ?, ?, ?, ?, ?)
                                """, (rep_id, session_id, exercise_id, set_num, rep_num, side, relative_path))

                                # Insert rep stats
                                cursor.execute("""
                                    INSERT INTO rep_stats
                                    (rep_id, avg_weight, peak_weight, rfd2080)
                                    VALUES (?, ?, ?, ?)
                                """, (
                                    rep_id,
                                    stat_row.get(f'Average Weight {side.capitalize()}'),
                                    stat_row.get(f'Peak Weight {side.capitalize()}'),
                                    stat_row.get(f'RFD2080 {side.capitalize()}')
                                ))

                except Exception as e:
                    print(f"Warning: Could not load stats for {exercise_name}: {e}")

            conn.commit()
            print(f"✓ Imported session: {tag} ({date_str})")
            return session_id

        except Exception as e:
            conn.rollback()
            raise e
        finally:
            conn.close()

    def list_sessions(self, tag: Optional[str] = None,
                     start_date: Optional[str] = None,
                     end_date: Optional[str] = None) -> pd.DataFrame:
        """
        List all sessions with optional filters

        Args:
            tag: Filter by tag (e.g., "morning off", "evening off")
            start_date: Filter sessions after this date (YYYY-MM-DD)
            end_date: Filter sessions before this date (YYYY-MM-DD)
        """
        query = "SELECT * FROM sessions WHERE 1=1"
        params = []

        if tag:
            query += " AND tag LIKE ?"
            params.append(f"%{tag}%")
        if start_date:
            query += " AND date >= ?"
            params.append(start_date)
        if end_date:
            query += " AND date <= ?"
            params.append(end_date)

        query += " ORDER BY date DESC"

        conn = sqlite3.connect(self.db_path)
        df = pd.read_sql_query(query, conn, params=params)
        conn.close()
        return df

    def get_session_summary(self, session_id: str) -> Dict:
        """Get summary of a session including exercises and stats"""
        conn = sqlite3.connect(self.db_path)

        # Session info
        session = pd.read_sql_query(
            "SELECT * FROM sessions WHERE session_id = ?",
            conn, params=(session_id,)
        ).iloc[0].to_dict()

        # Exercises
        exercises = pd.read_sql_query(
            "SELECT * FROM exercises WHERE session_id = ?",
            conn, params=(session_id,)
        )

        session['exercises'] = exercises.to_dict('records')
        conn.close()
        return session

    def get_exercise_stats(self, session_id: str, exercise_name: str) -> Tuple[pd.DataFrame, pd.DataFrame]:
        """Get rep and set stats for a specific exercise"""
        conn = sqlite3.connect(self.db_path)

        # Get exercise_id
        exercise = pd.read_sql_query(
            "SELECT exercise_id FROM exercises WHERE session_id = ? AND name = ?",
            conn, params=(session_id, exercise_name)
        )

        if exercise.empty:
            conn.close()
            raise ValueError(f"Exercise '{exercise_name}' not found in session")

        exercise_id = exercise['exercise_id'].iloc[0]

        # Get rep stats
        rep_stats = pd.read_sql_query("""
            SELECT r.set_num, r.rep_num, r.side, rs.avg_weight, rs.peak_weight, rs.rfd2080
            FROM reps r
            JOIN rep_stats rs ON r.rep_id = rs.rep_id
            WHERE r.exercise_id = ?
            ORDER BY r.set_num, r.rep_num, r.side
        """, conn, params=(exercise_id,))

        # Get set stats
        set_stats = pd.read_sql_query("""
            SELECT set_num, side, avg_weight, peak_weight, rfd2080
            FROM set_stats
            WHERE exercise_id = ?
            ORDER BY set_num, side
        """, conn, params=(exercise_id,))

        conn.close()
        return rep_stats, set_stats

    def get_rep_timeseries(self, rep_id: str) -> pd.DataFrame:
        """Load timeseries data for a specific rep"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("SELECT timeseries_path FROM reps WHERE rep_id = ?", (rep_id,))
        result = cursor.fetchone()
        conn.close()

        if not result or not result[0]:
            raise ValueError(f"No timeseries data found for rep {rep_id}")

        parquet_path = self.timeseries_path / result[0]
        return pd.read_parquet(parquet_path)

    def get_exercise_progress(self, exercise_name: str,
                             start_date: Optional[str] = None,
                             end_date: Optional[str] = None) -> pd.DataFrame:
        """
        Get progress over time for a specific exercise

        Returns DataFrame with date, session_id, set stats aggregated
        """
        conn = sqlite3.connect(self.db_path)

        query = """
            SELECT
                s.date,
                s.session_id,
                s.tag,
                e.name as exercise_name,
                ss.set_num,
                ss.side,
                ss.avg_weight,
                ss.peak_weight,
                ss.rfd2080
            FROM sessions s
            JOIN exercises e ON s.session_id = e.session_id
            JOIN set_stats ss ON e.exercise_id = ss.exercise_id
            WHERE e.name = ?
        """
        params = [exercise_name]

        if start_date:
            query += " AND s.date >= ?"
            params.append(start_date)
        if end_date:
            query += " AND s.date <= ?"
            params.append(end_date)

        query += " ORDER BY s.date, ss.set_num, ss.side"

        df = pd.read_sql_query(query, conn, params=params)
        conn.close()
        return df

    def get_all_exercises(self) -> List[str]:
        """Get list of all unique exercises across all sessions"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT DISTINCT name FROM exercises ORDER BY name")
        exercises = [row[0] for row in cursor.fetchall()]
        conn.close()
        return exercises
