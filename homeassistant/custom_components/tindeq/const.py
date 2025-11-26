"""Constants for the Tindeq integration."""

DOMAIN = "tindeq"

# Configuration keys
CONF_STORAGE_DIR = "storage_dir"
CONF_SCAN_INTERVAL = "scan_interval"

# Default values
DEFAULT_SCAN_INTERVAL = 300  # 5 minutes

# Sensor types
SENSOR_TYPES = {
    # Consistency metrics
    "training_frequency": {
        "name": "Training Frequency",
        "unit": "sessions/week",
        "icon": "mdi:calendar-check",
        "device_class": None,
        "state_class": "measurement",
    },
    "current_streak": {
        "name": "Current Streak",
        "unit": "days",
        "icon": "mdi:fire",
        "device_class": None,
        "state_class": "measurement",
    },
    "longest_streak": {
        "name": "Longest Streak",
        "unit": "days",
        "icon": "mdi:trophy",
        "device_class": None,
        "state_class": "measurement",
    },
    "morning_sessions": {
        "name": "Morning Sessions",
        "unit": "sessions",
        "icon": "mdi:weather-sunset-up",
        "device_class": None,
        "state_class": "total_increasing",
    },
    "evening_sessions": {
        "name": "Evening Sessions",
        "unit": "sessions",
        "icon": "mdi:weather-sunset-down",
        "device_class": None,
        "state_class": "total_increasing",
    },
    # Performance metrics
    "max_force_trend": {
        "name": "Max Force Trend",
        "unit": "%",
        "icon": "mdi:trending-up",
        "device_class": None,
        "state_class": "measurement",
    },
    "avg_force_trend": {
        "name": "Average Force Trend",
        "unit": "%",
        "icon": "mdi:chart-line",
        "device_class": None,
        "state_class": "measurement",
    },
    "left_right_balance": {
        "name": "Left/Right Balance",
        "unit": "%",
        "icon": "mdi:scale-balance",
        "device_class": None,
        "state_class": "measurement",
    },
    # Fatigue metrics
    "intra_session_fatigue": {
        "name": "Session Fatigue",
        "unit": "%",
        "icon": "mdi:battery-alert",
        "device_class": None,
        "state_class": "measurement",
    },
    # Recovery metrics
    "recovery_quality": {
        "name": "Recovery Quality",
        "unit": "%",
        "icon": "mdi:sleep",
        "device_class": None,
        "state_class": "measurement",
    },
    # Latest session
    "last_session_date": {
        "name": "Last Session",
        "unit": None,
        "icon": "mdi:clock-outline",
        "device_class": "timestamp",
        "state_class": None,
    },
    "total_sessions": {
        "name": "Total Sessions",
        "unit": "sessions",
        "icon": "mdi:counter",
        "device_class": None,
        "state_class": "total_increasing",
    },
}
