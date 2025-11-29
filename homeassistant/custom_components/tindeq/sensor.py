"""Sensor platform for Tindeq integration."""

import logging
from datetime import datetime

from homeassistant.components.sensor import SensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN, SENSOR_TYPES

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Tindeq sensors from a config entry."""
    coordinator = hass.data[DOMAIN][entry.entry_id]

    # Create sensors for all defined types
    sensors = [TindeqSensor(coordinator, entry, sensor_type) for sensor_type in SENSOR_TYPES]

    async_add_entities(sensors)


class TindeqSensor(CoordinatorEntity, SensorEntity):
    """Representation of a Tindeq sensor."""

    def __init__(self, coordinator, config_entry, sensor_type):
        """Initialize the sensor."""
        super().__init__(coordinator)
        self._sensor_type = sensor_type
        self._config_entry = config_entry
        self._attr_unique_id = f"{config_entry.entry_id}_{sensor_type}"

        # Set sensor properties from SENSOR_TYPES
        sensor_config = SENSOR_TYPES[sensor_type]
        self._attr_name = f"Tindeq {sensor_config['name']}"
        self._attr_native_unit_of_measurement = sensor_config["unit"]
        self._attr_icon = sensor_config["icon"]
        self._attr_device_class = sensor_config["device_class"]
        self._attr_state_class = sensor_config["state_class"]

    @property
    def device_info(self):
        """Return device information about this entity."""
        return {
            "identifiers": {(DOMAIN, self._config_entry.entry_id)},
            "name": "Tindeq Training Tracker",
            "manufacturer": "Tindeq",
            "model": "Progressor",
            "sw_version": "0.1.0",
        }

    @property
    def native_value(self):
        """Return the state of the sensor."""
        if not self.coordinator.data:
            return None

        value = self.coordinator.data.get(self._sensor_type)

        # Handle timestamp conversion for datetime sensors
        if self._sensor_type == "last_session_date" and value:
            if isinstance(value, str):
                try:
                    return datetime.fromisoformat(value)
                except (ValueError, TypeError):
                    _LOGGER.warning("Invalid timestamp format: %s", value)
                    return None
            return value

        # Round numeric values to 1 decimal place for display
        if isinstance(value, (int, float)):
            return round(value, 1)

        return value

    @property
    def available(self) -> bool:
        """Return if entity is available."""
        return self.coordinator.last_update_success

    @property
    def extra_state_attributes(self):
        """Return additional state attributes."""
        if not self.coordinator.data:
            return {}

        attrs = {}

        # Add context-specific attributes
        if self._sensor_type == "training_frequency":
            attrs["days_with_data"] = self.coordinator.data.get("days_with_data")

        if self._sensor_type in ["max_force_trend", "avg_force_trend"]:
            # Could add slope, r_squared, etc. if available
            pass

        return attrs
