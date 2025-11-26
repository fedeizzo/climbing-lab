"""The Tindeq integration."""
import logging
from datetime import timedelta
from pathlib import Path

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .const import CONF_SCAN_INTERVAL, CONF_STORAGE_DIR, DEFAULT_SCAN_INTERVAL, DOMAIN

_LOGGER = logging.getLogger(__name__)

PLATFORMS = [Platform.SENSOR]


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Tindeq from a config entry."""
    storage_dir = entry.data[CONF_STORAGE_DIR]
    scan_interval = entry.options.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL)

    # Validate storage directory exists
    if not Path(storage_dir).exists():
        _LOGGER.error("Storage directory does not exist: %s", storage_dir)
        return False

    coordinator = TindeqDataUpdateCoordinator(
        hass,
        storage_dir=storage_dir,
        scan_interval=timedelta(seconds=scan_interval),
    )

    # Fetch initial data
    await coordinator.async_config_entry_first_refresh()

    # Store coordinator
    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN][entry.entry_id] = coordinator

    # Forward entry setup to platforms
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)

    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id)

    return unload_ok


class TindeqDataUpdateCoordinator(DataUpdateCoordinator):
    """Class to manage fetching Tindeq data."""

    def __init__(self, hass: HomeAssistant, storage_dir: str, scan_interval: timedelta):
        """Initialize."""
        self.storage_dir = storage_dir

        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=scan_interval,
        )

    async def _async_update_data(self):
        """Fetch data from Tindeq storage."""
        try:
            # Import here to avoid loading heavy dependencies during setup
            from tindeq_exporter.storage import TindeqStorage
            from tindeq_exporter.analytics import TindeqAnalytics

            return await self.hass.async_add_executor_job(
                self._update_data, TindeqStorage, TindeqAnalytics
            )
        except Exception as err:
            raise UpdateFailed(f"Error communicating with Tindeq storage: {err}") from err

    def _update_data(self, StorageClass, AnalyticsClass):
        """Fetch data from Tindeq storage (runs in executor)."""
        storage = StorageClass(self.storage_dir)
        analytics = AnalyticsClass(storage)

        data = {}

        try:
            # Get session count and last session
            sessions = storage.list_sessions()
            data["total_sessions"] = len(sessions)

            if sessions:
                last_session = max(sessions, key=lambda s: s["timestamp"])
                data["last_session_date"] = last_session["timestamp"]
            else:
                data["last_session_date"] = None

            # Analyze consistency (last 30 days)
            consistency = analytics.analyze_consistency(days=30)
            if consistency:
                data["training_frequency"] = consistency["frequency"]["sessions_per_week"]
                data["current_streak"] = consistency["streaks"]["current_streak"]
                data["longest_streak"] = consistency["streaks"]["longest_streak"]
                data["morning_sessions"] = consistency["time_of_day"]["morning_count"]
                data["evening_sessions"] = consistency["time_of_day"]["evening_count"]

            # Analyze performance trends (last 30 days)
            # Get all exercises
            exercises_list = storage.get_exercises()
            if exercises_list:
                # Use the first exercise for trend analysis
                # In the future, this could be configurable
                primary_exercise = exercises_list[0]["exercise_name"]

                performance = analytics.analyze_performance(
                    exercise_name=primary_exercise, days=30
                )
                if performance:
                    data["max_force_trend"] = performance["trends"]["max_force"]["change_percent"]
                    data["avg_force_trend"] = performance["trends"]["avg_force"]["change_percent"]

                    if performance["balance"]:
                        data["left_right_balance"] = performance["balance"]["balance_score"]

                # Analyze fatigue
                fatigue = analytics.analyze_session_fatigue(
                    exercise_name=primary_exercise, days=7
                )
                if fatigue and fatigue["sessions"]:
                    # Average fatigue across recent sessions
                    avg_fatigue = sum(
                        s["fatigue_percent"] for s in fatigue["sessions"] if s["fatigue_percent"] is not None
                    ) / len([s for s in fatigue["sessions"] if s["fatigue_percent"] is not None])
                    data["intra_session_fatigue"] = avg_fatigue

                # Analyze recovery
                recovery = analytics.analyze_recovery(
                    exercise_name=primary_exercise, days=7
                )
                if recovery and recovery["recoveries"]:
                    # Average recovery quality
                    avg_recovery = sum(
                        r["improvement_percent"] for r in recovery["recoveries"] if r["improvement_percent"] is not None
                    ) / len([r for r in recovery["recoveries"] if r["improvement_percent"] is not None])
                    data["recovery_quality"] = avg_recovery

        except Exception as err:
            _LOGGER.error("Error fetching Tindeq data: %s", err)
            raise

        return data
