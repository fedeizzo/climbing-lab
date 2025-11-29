import re
import tempfile
import zipfile
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import pandas as pd


class TindeqSession:
    """Represents a single Tindeq training session"""

    def __init__(self, zip_path: str, temp_dir: Optional[str] = None):
        """
        Initialize a Tindeq session from a zip file

        Args:
            zip_path: Path to the session zip file
            temp_dir: Optional temporary directory to use for extraction.
                     If not provided, creates its own temp directory.
        """
        self.zip_path = zip_path
        self.session_name = Path(zip_path).stem
        self._owns_temp_dir = temp_dir is None
        self._temp_dir_obj = None

        if self._owns_temp_dir:
            # Create our own temp directory
            self._temp_dir_obj = tempfile.TemporaryDirectory(prefix="tindeq_session_")
            self._temp_base = Path(self._temp_dir_obj.name)
        else:
            # Use provided temp directory
            self._temp_base = Path(temp_dir)

        self._extract_session()

    def _extract_session(self):
        """Extract session contents to a temporary directory"""
        self.session_dir = self._temp_base / self.session_name
        self.session_dir.mkdir(exist_ok=True, parents=True)

        with zipfile.ZipFile(self.zip_path, "r") as zf:
            zf.extractall(self.session_dir)

        # Extract nested data and stats zips
        data_zip = self.session_dir / "data.zip"
        stats_zip = self.session_dir / "stats.zip"

        if data_zip.exists():
            self.data_dir = self.session_dir / "data"
            self.data_dir.mkdir(exist_ok=True)
            with zipfile.ZipFile(data_zip, "r") as zf:
                zf.extractall(self.data_dir)

        if stats_zip.exists():
            self.stats_dir = self.session_dir / "stats"
            self.stats_dir.mkdir(exist_ok=True)
            with zipfile.ZipFile(stats_zip, "r") as zf:
                zf.extractall(self.stats_dir)

    def cleanup(self):
        """Clean up temporary directory if we own it"""
        if self._owns_temp_dir and self._temp_dir_obj is not None:
            self._temp_dir_obj.cleanup()
            self._temp_dir_obj = None

    def __enter__(self):
        """Context manager entry"""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit - cleanup temp directory"""
        self.cleanup()
        return False

    def __del__(self):
        """Cleanup on deletion"""
        self.cleanup()

    def get_settings(self) -> pd.DataFrame:
        """Load session settings"""
        return pd.read_csv(self.session_dir / "settings.csv")

    def get_timeline(self) -> pd.DataFrame:
        """Load session timeline"""
        return pd.read_csv(self.session_dir / "timeline.csv")

    def get_rep_data(self, exercise: str, set_num: int, rep_num: int, side: str) -> pd.DataFrame:
        """
        Load force data for a specific rep

        Args:
            exercise: Exercise name (e.g., "4_finger", "3_finger_drag")
            set_num: Set number
            rep_num: Rep number
            side: "left" or "right"
        """
        # Normalize exercise name (replace spaces with underscores, lowercase)
        exercise_normalized = exercise.lower().replace(" ", "_")
        filename = f"{exercise_normalized}_s{set_num}_r{rep_num}_{side.lower()}.csv"
        filepath = self.data_dir / filename

        if not filepath.exists():
            raise FileNotFoundError(f"Rep data not found: {filename}")

        # Read, skipping the first 2 header rows
        df = pd.read_csv(filepath, skiprows=2)
        df.columns = ["time_s", "force_kg"]
        return df

    def get_exercise_stats(self, exercise: str) -> Tuple[pd.DataFrame, pd.DataFrame]:
        """
        Load statistics for an exercise

        Returns:
            (reps_df, sets_df): DataFrames with rep-level and set-level statistics
        """
        exercise_normalized = exercise.lower().replace(" ", "_")
        stats_folder = self.stats_dir / f"stats_{exercise_normalized}"

        reps_df = pd.read_csv(stats_folder / "reps.csv")
        sets_df = pd.read_csv(stats_folder / "sets.csv")

        return reps_df, sets_df

    def list_exercises(self) -> List[str]:
        """List all exercises in this session"""
        exercises = set()
        for filename in self.data_dir.glob("*.csv"):
            # Parse exercise name from filename
            match = re.match(r"(.+?)_s\d+_r\d+_(left|right)\.csv", filename.name)
            if match:
                exercises.add(match.group(1))
        return sorted(exercises)

    def get_all_reps_for_exercise(self, exercise: str) -> Dict[str, pd.DataFrame]:
        """
        Load all rep data for a specific exercise

        Returns:
            Dict with keys like "s1_r1_left" mapping to DataFrames
        """
        exercise_normalized = exercise.lower().replace(" ", "_")
        reps = {}

        for filename in self.data_dir.glob(f"{exercise_normalized}_*.csv"):
            match = re.match(r".+_s(\d+)_r(\d+)_(left|right)\.csv", filename.name)
            if match:
                set_num, rep_num, side = match.groups()
                key = f"s{set_num}_r{rep_num}_{side}"
                df = pd.read_csv(filename, skiprows=2)
                df.columns = ["time_s", "force_kg"]
                reps[key] = df

        return reps


class TindeqBatchExport:
    """Process a batch export of Tindeq sessions"""

    def __init__(self, batch_zip_path: str):
        """
        Initialize batch export processor

        Args:
            batch_zip_path: Path to the batch export zip file
        """
        self.batch_zip_path = batch_zip_path
        self._temp_dir_obj = tempfile.TemporaryDirectory(prefix="tindeq_batch_")
        self.extract_dir = Path(self._temp_dir_obj.name)
        self._extract_batch()

    def _extract_batch(self):
        """Extract the batch zip to get individual session zips"""
        with zipfile.ZipFile(self.batch_zip_path, "r") as zf:
            zf.extractall(self.extract_dir)

        # Find all session zip files
        self.session_zips = sorted(self.extract_dir.glob("customSession_*.zip"))

    def load_session(self, index: int = 0) -> TindeqSession:
        """
        Load a specific session by index

        Note: The returned TindeqSession will use the batch's temp directory
        """
        return TindeqSession(str(self.session_zips[index]), temp_dir=str(self.extract_dir))

    def load_all_sessions(self) -> List[TindeqSession]:
        """Load all sessions (uses batch's temp directory)"""
        return [TindeqSession(str(zip_path), temp_dir=str(self.extract_dir)) for zip_path in self.session_zips]

    def list_sessions(self) -> List[str]:
        """List all session names with their dates"""
        sessions = []
        for zip_path in self.session_zips:
            # Parse date from filename
            match = re.search(
                r"customSession_(\d{4}_\d{2}_\d{2}_\d{2}_\d{2}[AP]M_.+)\.zip",
                zip_path.name,
            )
            if match:
                sessions.append(match.group(1))
        return sessions

    def cleanup(self):
        """Clean up temporary directory"""
        if self._temp_dir_obj is not None:
            self._temp_dir_obj.cleanup()
            self._temp_dir_obj = None

    def __enter__(self):
        """Context manager entry"""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit - cleanup temp directory"""
        self.cleanup()
        return False

    def __del__(self):
        """Cleanup on deletion"""
        self.cleanup()


# Example usage
if __name__ == "__main__":
    # Load the batch export
    batch = TindeqBatchExport("vibecoded/customSession_batch_export_2025_11_26.zip")

    print(f"Found {len(batch.session_zips)} sessions:")
    for i, session_name in enumerate(batch.list_sessions()):
        print(f"  {i}: {session_name}")

    print("\n" + "=" * 80 + "\n")

    # Load first session as example
    session = batch.load_session(0)
    print(f"Session: {session.session_name}\n")

    # Show settings
    print("Settings:")
    print(session.get_settings())
    print()

    # Show exercises
    exercises = session.list_exercises()
    print(f"Exercises in session: {exercises}\n")

    # Example: Load stats for first exercise
    if exercises:
        exercise = exercises[0]
        print(f"Statistics for '{exercise}':")
        reps_df, sets_df = session.get_exercise_stats(exercise)
        print("\nRep-level stats:")
        print(reps_df.head())
        print("\nSet-level stats:")
        print(sets_df)
        print()

        # Example: Load force data for a specific rep
        print(f"Force data for {exercise}, set 1, rep 1, left hand:")
        rep_data = session.get_rep_data(exercise, 1, 1, "left")
        print(rep_data.head(10))
        print(f"... ({len(rep_data)} data points total)")
