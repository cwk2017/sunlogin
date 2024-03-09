from datetime import timedelta
import logging

from homeassistant.components.sensor import DOMAIN as ENTITY_DOMAIN
from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorStateClass,
)
from homeassistant.const import CONF_DEVICES, CONF_PLATFORM, CONF_UNIT_OF_MEASUREMENT
import async_timeout
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN, SL_DEVICES, SL_COORDINATOR

_LOGGER = logging.getLogger(__name__)

DEFAULT_PRECISION = 2
SCAN_INTERVAL = timedelta(minutes=1)


async def async_setup_entry(
    hass, config_entry, async_add_entities
):
    """Setup switch from a config entry created in the integrations UI."""
    entities = []

    _LOGGER.debug("entities: %s", hass.data[DOMAIN][SL_DEVICES])
    for dev_id in config_entry.data[CONF_DEVICES]:
        device = hass.data[DOMAIN][SL_DEVICES][dev_id]
        coordinator = hass.data[DOMAIN][SL_COORDINATOR][dev_id]
        
        entities_to_setup = [
            entity
            for entity in device.entities
            if entity[CONF_PLATFORM] == ENTITY_DOMAIN
        ]

        if entities_to_setup:

            for entity in entities_to_setup:
                entities.append(
                    SunLoginHaSensor(
                        device,
                        entity['dp_id'],
                        coordinator,
                    )
                )
    
    # async_add_entities(sensors, update_before_add=True)
    _LOGGER.debug(entities)
    async_add_entities(entities)


class SunLoginHaSensor(CoordinatorEntity, SensorEntity):
    """Representation of a Tuya sensor."""

    platform = 'sensor'

    def __init__(
        self,
        device,
        sensorid,
        coordinator,
        **kwargs,
    ):
        """Initialize the Tuya sensor."""
        
        super().__init__(coordinator, context=sensorid)
        self.device = device
        self.dp_id = sensorid
        self._state = False
        self.entity_id = f"{ENTITY_DOMAIN}.{self.device.model}_{self.device.sn}_{self.dp_id}"
        _LOGGER.debug("Initialized switch [%s]", self.dp_id)


    def _handle_coordinator_update(self):
        """Handle updated data from the coordinator."""
        # self._attr_is_on = self.coordinator.data[self.idx]["state"]
        self.async_write_ha_state()


    @property
    def state(self):
        """Return sensor state."""
        state = self.device.status[self.dp_id]['power']['state']
        scale_factor = self.device.status[self.dp_id]['power']['scaling']
        if scale_factor is not None and isinstance(state, (int, float)):
            state = round(state * scale_factor, DEFAULT_PRECISION)
        return state


    @property
    def unit_of_measurement(self):
        """Return the unit of measurement of this entity, if any."""
        return self.device.status[self.dp_id]['power'][CONF_UNIT_OF_MEASUREMENT]

    @property
    def device_info(self):
        """Return device information for the device registry."""
        model = self.device.model
        return {
            "identifiers": {
                # Serial numbers are unique identifiers within a specific domain
                (DOMAIN, self.device.sn)
            },
            "name": self.device.friendly_name,
            "manufacturer": "SunLogin",
            "model": f"{model} ({self.device.sn})",
            "sw_version": self.device.version,
        }
    
    @property
    def name(self):
        """Get name of Tuya entity."""
        return self.dp_id

    @property
    def should_poll(self):
        """Return if platform should poll for updates."""
        return True

    @property
    def unique_id(self):
        """Return unique device identifier."""
        return f"sunlogin_{self.device.sn}_{self.dp_id}"

    @property
    def available(self):
        """Return if device is available or not."""
        return str(self.dp_id) in self.device.status

    @property
    def extra_state_attributes(self):
        attributes = {}
        if self.device.status[self.dp_id]['vol']['state']:
            state = self.device.status[self.dp_id]['vol']['state']
            scale_factor = self.device.status[self.dp_id]['vol']['scaling']
            if scale_factor is not None and isinstance(state, (int, float)):
                state = round(state * scale_factor, DEFAULT_PRECISION)
            unit = self.device.status[self.dp_id]['vol'][CONF_UNIT_OF_MEASUREMENT]
            key = f'Voltage({unit})'
            attributes[key] = state
        if self.device.status[self.dp_id]['curr']['state']:
            state = self.device.status[self.dp_id]['curr']['state']
            scale_factor = self.device.status[self.dp_id]['curr']['scaling']
            if scale_factor is not None and isinstance(state, (int, float)):
                state = round(state * scale_factor, DEFAULT_PRECISION)
            unit = self.device.status[self.dp_id]['curr'][CONF_UNIT_OF_MEASUREMENT]
            key = f'Current({unit})'
            attributes[key] = state
        return attributes



    # No need to restore state for a sensor

