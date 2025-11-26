# Features

- **Import** batch exports or individual sessions from Tindeq app
- **Import** peakload data from CSV files (manual max testing)
- **Store** data efficiently using SQLite + Parquet (organized by month)
- **Query** training history, exercise progress, and statistics
- **Analyze** comprehensive training metrics (consistency, performance, fatigue, recovery)
- **Analyze** peakload trends and left/right balance
- **Report** weekly and monthly summaries
- **Export** data to CSV/JSON for further analysis
- **Flexible schema** supports any custom training pattern


# Usage

## CLI Commands

### Import Data

Import a batch export (multiple sessions):

```bash
tindeq import --batch path/to/batch_export.zip

# Automatically delete the zip after successful import
tindeq import --batch path/to/batch_export.zip --delete-after
```

Import a single session:

```bash
tindeq import path/to/session.zip

# Automatically delete the zip after successful import
tindeq import path/to/session.zip --delete-after
```

**Note:** Imports use temporary directories that are automatically cleaned up after processing. No extraction artifacts are left in your working directory.

### List Sessions

```bash
# List all sessions
tindeq list

# Filter by tag
tindeq list --tag "morning"

# Filter by date range
tindeq list --from-date 2025-11-01 --to-date 2025-11-30
```

### View Exercises

```bash
tindeq exercises
```

### Track Progress

```bash
# View progress for an exercise
tindeq progress "4_finger"

# Export as CSV
tindeq progress "4_finger" --format csv > progress.csv

# Date range
tindeq progress "4_finger" --from-date 2025-11-01
```

### Export Data

```bash
# Export all sessions
tindeq export sessions -o sessions.csv

# Export progress for specific exercise
tindeq export progress --exercise "4_finger" -o 4finger_progress.csv
```

### Session Statistics

```bash
# Show session summary
tindeq stats <session_id>

# Detailed stats with per-exercise breakdown
tindeq stats <session_id> --detailed
```

### Analytics

```bash
# Training consistency (frequency, streaks, adherence)
tindeq analyze consistency --days 30

# Performance trends for an exercise
tindeq analyze performance --exercise "4_finger" --days 30

# Compare all exercises
tindeq analyze compare --days 30

# Recovery quality (morning vs evening)
tindeq analyze recovery --exercise "4_finger" --days 30

# Identify weak points and get recommendations
tindeq analyze weakpoints --days 30

# Intra-session fatigue analysis
tindeq analyze fatigue --session-id <id> --exercise "4_finger"
```

### Reports

```bash
# Weekly summary report
tindeq report weekly --weeks 4

# Monthly summary report
tindeq report monthly --months 3

# Export as JSON
tindeq report monthly --months 3 --json > report.json
```

### Peakload Data

Peakload data tracks max effort tests (typically left/right hand max hangs):

```bash
# Import peakload CSV file
tindeq peakload import peakload_data.csv

# List all peakload entries
tindeq peakload list

# Filter by date range
tindeq peakload list --from-date 2025-11-01 --to-date 2025-11-30

# Show trend analysis (current, max, trends, balance)
tindeq peakload trend

# Export as JSON
tindeq peakload list --format json > peakload.json
```

**CSV Format:**
```csv
date,tag,comment,unit,type,left max weight,right max weight
2025-11-18 20:44:57,Nov 2025,Evening test,SI,left/right,42.72,40.79
```

📊 **For detailed analytics guide, see [analytics.md](analytics.md)**

## Python API

```python
from tindeq_exporter import TindeqBatchExport, TindeqStorage

# Initialize storage
storage = TindeqStorage("tindeq_data")

# Import batch export
batch = TindeqBatchExport("path/to/batch.zip")
for i in range(len(batch.session_zips)):
    session = batch.load_session(i)
    storage.import_session(session)

# Query data
sessions = storage.list_sessions()
exercises = storage.get_all_exercises()
progress = storage.get_exercise_progress("4_finger")

# Get specific session data
summary = storage.get_session_summary(session_id)
rep_stats, set_stats = storage.get_exercise_stats(session_id, "4_finger")

# Load raw force curve data
timeseries = storage.get_rep_timeseries(rep_id)
```

# Data Structure

## Storage Layout

```
tindeq_data/
├── metadata.db          # SQLite database with all metadata
└── timeseries/
    └── YYYY-MM/         # Parquet files organized by month
        └── *.parquet    # Individual rep force curves
```

## Database Schema

- **sessions** - Session metadata (date, tag, settings)
- **exercises** - Exercise definitions per session
- **timeline** - Workout structure (work periods, rest, etc.)
- **reps** - Individual rep metadata with references to timeseries
- **rep_stats** - Aggregated metrics per rep (avg/peak weight, RFD)
- **set_stats** - Aggregated metrics per set
- **peakloads** - Manual max testing data (left/right hand peaks)

## Timeseries Data

Each rep's force curve is stored as a Parquet file with:
- `time_s` - Timestamp in seconds
- `force_kg` - Force measurement in kilograms
