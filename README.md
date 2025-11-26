# Tindeq Exporter

A tool for importing, storing, and analyzing Tindeq finger strength training data.

## Features

- **Import** batch exports or individual sessions from Tindeq app
- **Import** peakload data from CSV files (manual max testing)
- **Store** data efficiently using SQLite + Parquet (organized by month)
- **Query** training history, exercise progress, and statistics
- **Analyze** comprehensive training metrics (consistency, performance, fatigue, recovery)
- **Analyze** peakload trends and left/right balance
- **Report** weekly and monthly summaries
- **Export** data to CSV/JSON for further analysis
- **NixOS Module** systemd service with inotify watching for automatic imports
- **Home Assistant** custom integration with 20+ sensors
- **Flexible schema** supports any custom training pattern

## Setup

Using Nix:

```bash
nix develop
poetry install
```

Or with just Poetry:

```bash
poetry install
```

## Usage

### CLI Commands

#### Import Data

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

#### List Sessions

```bash
# List all sessions
tindeq list

# Filter by tag
tindeq list --tag "morning"

# Filter by date range
tindeq list --from-date 2025-11-01 --to-date 2025-11-30
```

#### View Exercises

```bash
tindeq exercises
```

#### Track Progress

```bash
# View progress for an exercise
tindeq progress "4_finger"

# Export as CSV
tindeq progress "4_finger" --format csv > progress.csv

# Date range
tindeq progress "4_finger" --from-date 2025-11-01
```

#### Export Data

```bash
# Export all sessions
tindeq export sessions -o sessions.csv

# Export progress for specific exercise
tindeq export progress --exercise "4_finger" -o 4finger_progress.csv
```

#### Session Statistics

```bash
# Show session summary
tindeq stats <session_id>

# Detailed stats with per-exercise breakdown
tindeq stats <session_id> --detailed
```

#### Analytics

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

#### Reports

```bash
# Weekly summary report
tindeq report weekly --weeks 4

# Monthly summary report
tindeq report monthly --months 3

# Export as JSON
tindeq report monthly --months 3 --json > report.json
```

#### Peakload Data

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

📊 **For detailed analytics guide, see [ANALYTICS.md](ANALYTICS.md)**

### Python API

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

## Data Structure

### Storage Layout

```
tindeq_data/
├── metadata.db          # SQLite database with all metadata
└── timeseries/
    └── YYYY-MM/         # Parquet files organized by month
        └── *.parquet    # Individual rep force curves
```

### Database Schema

- **sessions** - Session metadata (date, tag, settings)
- **exercises** - Exercise definitions per session
- **timeline** - Workout structure (work periods, rest, etc.)
- **reps** - Individual rep metadata with references to timeseries
- **rep_stats** - Aggregated metrics per rep (avg/peak weight, RFD)
- **set_stats** - Aggregated metrics per set
- **peakloads** - Manual max testing data (left/right hand peaks)

### Timeseries Data

Each rep's force curve is stored as a Parquet file with:
- `time_s` - Timestamp in seconds
- `force_kg` - Force measurement in kilograms

## Deployment

### NixOS Systemd Service

The project includes a NixOS module for automatic import via systemd:

```nix
{
  imports = [ inputs.tindeq-exporter.nixosModules.default ];

  services.tindeq-exporter = {
    enable = true;
    watchDirectory = "/var/lib/tindeq/exports";
    databaseDirectory = "/var/lib/tindeq";
    deleteAfterImport = true;
    notifyOnImport = false;
  };
}
```

Features:
- **inotify watching** - Automatically imports new zip files when they appear
- **Automatic cleanup** - Optionally deletes zips after successful import
- **Security hardening** - Runs with minimal privileges, isolated filesystem
- **Systemd integration** - Logs via journald, status via `systemctl`

See `nixos-module/example.nix` for full configuration.

### Home Assistant Integration

Custom component providing 20+ sensors for training metrics:

```nix
services.home-assistant = {
  enable = true;
  customComponents = [
    inputs.tindeq-exporter.packages.${pkgs.system}.homeassistant-component
  ];
};
```

Sensors include:
- Training frequency, streaks, consistency
- Performance trends (max/avg force)
- Left/right balance and asymmetry
- Session fatigue and recovery quality
- Peakload current/max values and trends
- Total sessions and last session date

See `homeassistant/README.md` for installation and dashboard examples.

## Development

Run tests:

```bash
pytest
```

Start Jupyter:

```bash
jupyter lab
```

Build with Nix:

```bash
nix build                              # Build the CLI tool
nix build .#homeassistant-component    # Build HA component
nix run                                # Run the CLI
```

## Future Enhancements

### Data Import & Processing
- [ ] **Direct Bluetooth integration** - Connect to Tindeq device directly without app export
- [ ] **Batch peakload CSV import** - Support multiple entries in one CSV file
- [ ] **Auto-detect file format** - Smart detection of session vs batch vs peakload files
- [ ] **Video sync** - Import and sync training videos with force curve data
- [ ] **External API integration** - Import from other training platforms (Crimpd, Lattice, etc.)
- [ ] **Real-time monitoring** - Live force curve display during training sessions

### Analytics & Insights
- [ ] **Machine learning predictions** - Predict injury risk, performance plateau, deload needs
- [ ] **Periodization tracking** - Automatic detection and analysis of training phases
- [ ] **Volume and load metrics** - Calculate total training load, volume trends
- [ ] **Adaptive recommendations** - AI-powered training suggestions based on history
- [ ] **Comparison with population data** - Benchmark against other climbers (anonymized)
- [ ] **Injury correlation analysis** - Track injury events and identify risk patterns
- [ ] **Training effectiveness score** - Rate how well training translates to progress
- [ ] **Custom metric calculations** - User-defined formulas for specialized analysis

### Visualization
- [ ] **Web dashboard** - Interactive web UI with charts and graphs
- [ ] **Force curve overlays** - Compare multiple reps/sessions visually
- [ ] **Heatmaps** - Training density, time-of-day patterns, exercise focus
- [ ] **3D visualizations** - Multi-dimensional performance analysis
- [ ] **Progress photos integration** - Track physical changes alongside data
- [ ] **Export to training logs** - Generate formatted PDF/HTML reports

### Home Assistant
- [ ] **Per-exercise sensor selection** - Choose which exercises to track via UI
- [ ] **Training reminders** - Automations based on streak, rest days, volume
- [ ] **Voice notifications** - TTS announcements for milestones and PRs
- [ ] **Calendar integration** - Show training schedule in HA calendar
- [ ] **Multi-user support** - Track multiple athletes in one household
- [ ] **Lovelace custom cards** - Dedicated force curve and progress cards
- [ ] **Mobile app widgets** - Quick stats on phone home screen

### Integration & Ecosystem
- [ ] **Mobile companion app** - Dedicated iOS/Android app for quick data entry
- [ ] **Smartwatch integration** - View stats and reminders on wearables
- [ ] **Training plan integration** - Import and track structured programs
- [ ] **Coach/athlete portal** - Share data with coaches, receive feedback
- [ ] **Social features** - Share PRs, compare with training partners
- [ ] **Webhook notifications** - Trigger external services on new data
- [ ] **REST API** - External access for custom integrations

### NixOS & Deployment
- [ ] **Automatic backup module** - Scheduled backups of database and Parquet files
- [ ] **Multi-instance support** - Run multiple trackers for different users
- [ ] **Remote sync** - Sync data across devices (homelab, laptop, etc.)
- [ ] **Grafana integration** - Pre-built Grafana dashboards for NixOS users
- [ ] **Alerting module** - Send notifications via ntfy, email, SMS
- [ ] **Docker container** - Non-NixOS deployment option

### Data Quality & Management
- [ ] **Data validation** - Detect and flag anomalies, outliers, bad data
- [ ] **Duplicate detection** - Identify and merge duplicate sessions
- [ ] **Data migration tools** - Import from other systems (Excel, CSV dumps)
- [ ] **Session tagging system** - Enhanced tagging with autocomplete, categories
- [ ] **Notes and annotations** - Add context to sessions (felt strong, finger pain, etc.)
- [ ] **Equipment tracking** - Log gear used (hangboard model, grip type)

### Performance & Optimization
- [ ] **Incremental imports** - Only process new data in large batch files
- [ ] **Database optimization** - Automatic vacuuming, indexing suggestions
- [ ] **Parquet compression** - Optimize storage for large datasets
- [ ] **Lazy loading** - Load data on-demand for faster queries
- [ ] **Caching layer** - Cache frequently accessed analytics results

### Testing & Quality
- [ ] **Comprehensive test suite** - Unit, integration, and E2E tests
- [ ] **Test data generator** - Create synthetic training data for testing
- [ ] **Benchmarking suite** - Performance tests for large datasets
- [ ] **CI/CD pipeline** - Automated testing and releases
- [ ] **Documentation site** - Full docs with examples and tutorials

### Miscellaneous
- [ ] **Multi-language support** - i18n for CLI, HA component, and future UI
- [ ] **Configurable units** - Support imperial units (lbs, etc.)
- [ ] **Plugin system** - Allow users to write custom analyzers
- [ ] **Export templates** - Customizable export formats for coaches/apps
- [ ] **Data privacy tools** - Anonymize exports, selective sharing
- [ ] **GDPR compliance tools** - Data export, deletion, audit logs

## License

MIT
