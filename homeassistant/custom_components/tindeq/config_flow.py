"""Config flow for Tindeq integration."""

import logging
from pathlib import Path
from typing import Any

import homeassistant.helpers.config_validation as cv
import voluptuous as vol
from homeassistant.core import HomeAssistant, callback
from homeassistant.data_entry_flow import FlowResult

from homeassistant import config_entries

from .const import (
    CONF_SCAN_INTERVAL,
    CONF_STORAGE_DIR,
    DEFAULT_SCAN_INTERVAL,
    DOMAIN,
)

_LOGGER = logging.getLogger(__name__)

STEP_USER_DATA_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_STORAGE_DIR): cv.string,
        vol.Optional(CONF_SCAN_INTERVAL, default=DEFAULT_SCAN_INTERVAL): cv.positive_int,
    }
)


async def validate_storage_dir(hass: HomeAssistant, storage_dir: str) -> dict[str, Any]:
    """Validate the storage directory."""
    errors = {}

    # Check if directory exists
    path = Path(storage_dir)
    if not await hass.async_add_executor_job(path.exists):
        errors["base"] = "storage_dir_not_found"
        return errors

    if not await hass.async_add_executor_job(path.is_dir):
        errors["base"] = "storage_dir_not_directory"
        return errors

    # Check if we can access it (try to list contents)
    try:
        await hass.async_add_executor_job(lambda: list(path.iterdir()))
    except PermissionError:
        errors["base"] = "storage_dir_no_permission"
        return errors

    # Check if it looks like a tindeq storage directory
    # (should have tindeq.db or be empty)
    db_file = path / "tindeq.db"
    contents = await hass.async_add_executor_job(lambda: list(path.iterdir()))

    if not await hass.async_add_executor_job(db_file.exists) and contents:
        _LOGGER.warning(
            "Storage directory %s exists but doesn't contain tindeq.db. Will be created on first import.",
            storage_dir,
        )

    return errors


class TindeqConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Tindeq."""

    VERSION = 1

    async def async_step_user(self, user_input: dict[str, Any] | None = None) -> FlowResult:
        """Handle the initial step."""
        errors = {}

        if user_input is not None:
            # Validate storage directory
            errors = await validate_storage_dir(self.hass, user_input[CONF_STORAGE_DIR])

            if not errors:
                # Check if already configured with this storage directory
                await self.async_set_unique_id(user_input[CONF_STORAGE_DIR])
                self._abort_if_unique_id_configured()

                return self.async_create_entry(
                    title=f"Tindeq ({user_input[CONF_STORAGE_DIR]})",
                    data={CONF_STORAGE_DIR: user_input[CONF_STORAGE_DIR]},
                    options={CONF_SCAN_INTERVAL: user_input[CONF_SCAN_INTERVAL]},
                )

        return self.async_show_form(
            step_id="user",
            data_schema=STEP_USER_DATA_SCHEMA,
            errors=errors,
            description_placeholders={
                "storage_dir_example": "/var/lib/tindeq/tindeq_data",
            },
        )

    @staticmethod
    @callback
    def async_get_options_flow(
        config_entry: config_entries.ConfigEntry,
    ) -> config_entries.OptionsFlow:
        """Get the options flow for this handler."""
        return TindeqOptionsFlowHandler(config_entry)


class TindeqOptionsFlowHandler(config_entries.OptionsFlow):
    """Handle options flow for Tindeq."""

    def __init__(self, config_entry: config_entries.ConfigEntry) -> None:
        """Initialize options flow."""
        self.config_entry = config_entry

    async def async_step_init(self, user_input: dict[str, Any] | None = None) -> FlowResult:
        """Manage the options."""
        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)

        return self.async_show_form(
            step_id="init",
            data_schema=vol.Schema(
                {
                    vol.Optional(
                        CONF_SCAN_INTERVAL,
                        default=self.config_entry.options.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL),
                    ): cv.positive_int,
                }
            ),
        )
