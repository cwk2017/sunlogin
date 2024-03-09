"""The SunLogin integration."""

import asyncio
import logging
import time
from datetime import timedelta

import homeassistant.helpers.config_validation as cv
import homeassistant.helpers.entity_registry as er
import voluptuous as vol
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import (
    CONF_DEVICE_ID,
    CONF_DEVICES,
    CONF_ENTITIES,
    CONF_PLATFORM,
    CONF_USERNAME,
    CONF_PASSWORD,
    CONF_SCAN_INTERVAL,
    EVENT_HOMEASSISTANT_STOP,
    SERVICE_RELOAD,
)
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers.device_registry import DeviceEntry
from homeassistant.helpers.event import async_track_time_interval

from .sunlogin import SunLogin, SunLoginDevice, MyCoordinator
# from .common import TuyaDevice, async_config_entry_by_device_id
from .config_flow import ENTRIES_VERSION
from .const import (
    CONF_USER_INPUT,
    SL_DEVICES,
    CLOUD_DATA,
    DOMAIN,
    SL_COORDINATOR,
)

_LOGGER = logging.getLogger(__name__)

UNSUB_LISTENER = "unsub_listener"

RECONNECT_INTERVAL = timedelta(seconds=60)

# CONFIG_SCHEMA = config_schema()

CONF_DP = "dp"
CONF_VALUE = "value"

SERVICE_SET_DP = "set_dp"
SERVICE_SET_DP_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_DEVICE_ID): cv.string,
        vol.Required(CONF_DP): int,
        vol.Required(CONF_VALUE): object,
    }
)

async def async_setup(hass: HomeAssistant, config: dict):
    """Set up the LocalTuya integration component."""
    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN][SL_DEVICES] = {}
    hass.data[DOMAIN][SL_COORDINATOR] = {}
    return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry):
    """Set up LocalTuya integration from a config entry."""
    # if entry.version < ENTRIES_VERSION:
    #     _LOGGER.debug(
    #         "Skipping setup for entry %s since its version (%s) is old",
    #         entry.entry_id,
    #         entry.version,
    #     )
    #     return

    # user_input = entry.data['user_input']
    # username = user_input[CONF_USERNAME]
    # password = user_input[CONF_PASSWORD]
    # smscode = user_input[CONF_SMSCODE]
    # cloud_api = SunLogin(hass, username, password, smscode)
    
    # res = await cloud_api.async_get_access_token()
    # if res != "ok":
    #     _LOGGER.error("Cloud API connection failed: %s", res)
    # else:
    #     _LOGGER.info("Cloud API connection succeeded.")
    #     res = await cloud_api.async_get_devices_list()
    # hass.data[DOMAIN][CLOUD_DATA] = cloud_api

    async def setup_entities(device_ids):
        platforms = set()
        for dev_id in device_ids:
            entities = entry.data[CONF_DEVICES][dev_id]
            # platforms = platforms.union(
            #     set(entity[CONF_PLATFORM] for entity in entities)
            # )
            hass.data[DOMAIN][SL_DEVICES][dev_id] = SunLoginDevice(hass, entities, dev_id,
                entry.data[CONF_USER_INPUT][CONF_SCAN_INTERVAL]
            )


        for dev_id in device_ids:
            # hass.data[DOMAIN][SL_DEVICES][dev_id].async_connect()
            await hass.data[DOMAIN][SL_DEVICES][dev_id].async_get_info()
            hass.data[DOMAIN][SL_COORDINATOR][dev_id] = MyCoordinator(hass, hass.data[DOMAIN][SL_DEVICES][dev_id])
            _LOGGER.debug(dev_id)


        await asyncio.gather(
            *[
                hass.config_entries.async_forward_entry_setup(entry, platform)
                for platform in ['switch','sensor']
            ]
        )

    _LOGGER.debug(entry.data)
    hass.async_create_task(setup_entities(entry.data[CONF_DEVICES].keys()))
    

    # unsub_listener = entry.add_update_listener(update_listener)
    # hass.data[DOMAIN][entry.entry_id] = {UNSUB_LISTENER: unsub_listener}

    return True

