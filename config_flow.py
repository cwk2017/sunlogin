"""Configuration flows."""

import errno
import logging
#import time
from importlib import import_module

import homeassistant.helpers.config_validation as cv
import homeassistant.helpers.entity_registry as er
import voluptuous as vol
from homeassistant import config_entries, core, exceptions
from homeassistant.const import (
    CONF_DEVICE_ID,
    CONF_DEVICES,
    CONF_ENTITIES,
    CONF_FRIENDLY_NAME,
    CONF_PLATFORM,
    CONF_SCAN_INTERVAL,
    CONF_USERNAME,
    CONF_PASSWORD,
)
from homeassistant.core import callback
from .sunlogin import SunLogin
from .const import (
    CONF_SMARTPLUG,
    CONF_USER_INPUT,
    CONF_SMSCODE,
    CONF_LOGIN_METHOD,
    DOMAIN,
    PLATFORMS,
)
#from .discovery import discover

_LOGGER = logging.getLogger(__name__)

ENTRIES_VERSION = 1

PLATFORM_TO_ADD = "platform_to_add"
NO_ADDITIONAL_ENTITIES = "no_additional_entities"
SELECTED_DEVICE = "selected_device"

CUSTOM_DEVICE = "..."

# CONF_ACTIONS = {
#     CONF_ADD_DEVICE: "Add a new device",
#     CONF_EDIT_DEVICE: "Edit a device",
#     CONF_SETUP_CLOUD: "Reconfigure Cloud API account",
# }

# CONFIGURE_SCHEMA = vol.Schema(
#     {
#         vol.Required(CONF_ACTION, default=CONF_ADD_DEVICE): vol.In(CONF_ACTIONS),
#     }
# )

CLOUD_SETUP_SCHEMA = vol.Schema(
    {    
        vol.Required(CONF_USERNAME): cv.string,
        vol.Optional(CONF_PASSWORD): cv.string,
        vol.Optional(CONF_SCAN_INTERVAL, default=60): int,
        vol.Required(CONF_LOGIN_METHOD, default="local"): vol.In(["local", "password", "sms",])
    }
)


 
# PICK_ENTITY_SCHEMA = vol.Schema(
#     {vol.Required(PLATFORM_TO_ADD, default="switch"): vol.In(PLATFORMS)}
# )


def schema_defaults(schema, dps_list=None, **defaults):
    """Create a new schema with default values filled in."""
    copy = schema.extend({})
    for field, field_type in copy.schema.items():
        if isinstance(field_type, vol.In):
            value = None
            for dps in dps_list or []:
                if dps.startswith(f"{defaults.get(field)} "):
                    value = dps
                    break

            if value in field_type.container:
                field.default = vol.default_factory(value)
                continue

        if field.schema in defaults:
            field.default = vol.default_factory(defaults[field])
    return copy


async def attempt_connection(hass, user_input):
    """Create device."""
    if user_input.get(CONF_LOGIN_METHOD) != 'local':
        cloud_api = SunLogin(
            hass,
            user_input.get(CONF_USERNAME),
            user_input.get(CONF_PASSWORD),
            user_input.get(CONF_PASSWORD)
        )

        res = await cloud_api.async_get_access_token(user_input.get(CONF_LOGIN_METHOD))
        if res != "ok":
            _LOGGER.error("Cloud API connection failed: %s", res)
            return cloud_api, {"reason": "authentication_failed", "msg": res}

        res = await cloud_api.async_get_devices_list()
        if res != "ok":
            _LOGGER.error("Cloud API get_devices_list failed: %s", res)
            return cloud_api, {"reason": "device_list_failed", "msg": res}

    # res = await cloud_api.get_devices_list()
    # if res != "ok":
    #     _LOGGER.error("Cloud API connection failed: %s", res)
    #     return cloud_api, {"reason": "authentication_failed", "msg": res}
    _LOGGER.info("Cloud API connection succeeded.")

    return cloud_api, {}


class SunLoginConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for LocalTuya integration."""

    VERSION = ENTRIES_VERSION
    CONNECTION_CLASS = config_entries.CONN_CLASS_LOCAL_POLL

    # @staticmethod
    # @callback
    # def async_get_options_flow(config_entry):
    #     """Get options flow for this handler."""
    #     return LocalTuyaOptionsFlowHandler(config_entry)

    def __init__(self):
        """Initialize a new LocaltuyaConfigFlow."""

    async def async_step_user(self, user_input=None):
        """Handle the initial step."""
        errors = {}
        placeholders = {}
        if user_input is not None:
            if user_input.get(CONF_LOGIN_METHOD) != 'local':
                cloud_api, res = await attempt_connection(self.hass, user_input)

                if not res:
                    return await self._create_entry(user_input, cloud_api)
                errors["base"] = res["reason"]
                placeholders = {"msg": res["msg"]}

            else:
                return await self._create_entry_by_ip(user_input)
        defaults = {}
        defaults.update(user_input or {})

        return self.async_show_form(
            step_id="user",
            data_schema=schema_defaults(CLOUD_SETUP_SCHEMA, **defaults),
            errors=errors,
            description_placeholders=placeholders,
        )

    async def _create_entry(self, user_input, cloud_api):
        """Register new entry."""
        # if self._async_current_entries():
        #     return self.async_abort(reason="already_configured")

        await self.async_set_unique_id(user_input.get(CONF_USERNAME))

        devices = {}
        for sn, dev in cloud_api.device_list.items():
            device_type = dev.get('device_type', 'unknow')
            if device_type == CONF_SMARTPLUG and dev.get('isenable', False):
                # SunLoginDevice(hass, dev, sn)
                devices[sn] = dev

        entry = {CONF_USER_INPUT: user_input, CONF_DEVICES: devices}
        return self.async_create_entry(
            title=user_input.get(CONF_USERNAME),
            data=entry,
        )
    
    async def _create_entry_by_ip(self, user_input):
        """Register new entry."""
        # if self._async_current_entries():
        #     return self.async_abort(reason="already_configured")

        await self.async_set_unique_id(user_input.get(CONF_USERNAME))

        devices = {"_sn_": {'ip':user_input.get(CONF_USERNAME).strip()}}

        entry = {CONF_USER_INPUT: user_input, CONF_DEVICES: devices}
        return self.async_create_entry(
            title=user_input.get(CONF_USERNAME),
            data=entry,
        )

    async def async_step_import(self, user_input):
        """Handle import from YAML."""
        _LOGGER.error(
            "Configuration via YAML file is no longer supported by this integration."
        )


class LocalTuyaOptionsFlowHandler(config_entries.OptionsFlow):
    """Handle options flow for LocalTuya integration."""

    def __init__(self, config_entry):
        """Initialize localtuya options flow."""
        self.config_entry = config_entry
        # self.dps_strings = config_entry.data.get(CONF_DPS_STRINGS, gen_dps_strings())
        # self.entities = config_entry.data[CONF_ENTITIES]
        self.selected_device = None
        self.editing_device = False
        self.device_data = None
        self.dps_strings = []
        self.selected_platform = None
        self.discovered_devices = {}
        self.entities = []

    async def async_step_init(self, user_input=None):
        """Manage basic options."""
        # device_id = self.config_entry.data[CONF_DEVICE_ID]
        if user_input is not None:
            if user_input.get(CONF_ACTION) == CONF_SETUP_CLOUD:
                return await self.async_step_cloud_setup()
            if user_input.get(CONF_ACTION) == CONF_ADD_DEVICE:
                return await self.async_step_add_device()
            if user_input.get(CONF_ACTION) == CONF_EDIT_DEVICE:
                return await self.async_step_edit_device()

        return self.async_show_form(
            step_id="init",
            data_schema=CONFIGURE_SCHEMA,
        )

    async def async_step_yaml_import(self, user_input=None):
        """Manage YAML imports."""
        _LOGGER.error(
            "Configuration via YAML file is no longer supported by this integration."
        )
        # if user_input is not None:
        #     return self.async_create_entry(title="", data={})
        # return self.async_show_form(step_id="yaml_import")

    @property
    def current_entity(self):
        """Existing configuration for entity currently being edited."""
        return self.entities[len(self.device_data[CONF_ENTITIES])]


class CannotConnect(exceptions.HomeAssistantError):
    """Error to indicate we cannot connect."""


class InvalidAuth(exceptions.HomeAssistantError):
    """Error to indicate there is invalid auth."""


class EmptyDpsList(exceptions.HomeAssistantError):
    """Error to indicate no datapoints found."""
