from datetime import timedelta
import logging

from homeassistant.components.switch import DOMAIN as ENTITY_DOMAIN
from homeassistant.components.switch import SwitchEntity
from homeassistant.const import CONF_DEVICES, CONF_PLATFORM
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN, SL_DEVICES, SL_COORDINATOR

_LOGGER = logging.getLogger(__name__)

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

        _LOGGER.debug(device.entities)
        # asyncio.wait(device.connect_task)
        # await device.connect_task
        entities_to_setup = [
            entity
            for entity in device.entities
            if entity[CONF_PLATFORM] == ENTITY_DOMAIN
        ]

        if entities_to_setup:

            for entity in entities_to_setup:
                entities.append(
                    SunLoginHaSwitch(
                        device,
                        entity['dp_id'],
                        coordinator,
                    )
                )
    
    # async_add_entities(sensors, update_before_add=True)
    _LOGGER.debug(entities)
    async_add_entities(entities)


class SunLoginHaSwitch(CoordinatorEntity, SwitchEntity):
    """Tuya Switch Device."""

    platform = 'switch'

    # ToggleEntity

    def __init__(
        self,
        device,
        switchid,
        coordinator,
        **kwargs,
    ):
        super().__init__(coordinator, context=switchid)
        self.device = device
        self.dp_id = switchid
        self._state = False
        self.entity_id = f"{ENTITY_DOMAIN}.{self.device.model}_{self.device.sn}_{self.dp_id}"
        _LOGGER.debug("Initialized switch [%s]", self.dp_id)


    def _handle_coordinator_update(self):
        """Handle updated data from the coordinator."""
        # self._attr_is_on = self.coordinator.data[self.idx]["state"]
        self.async_write_ha_state()


    @property
    def is_on(self) -> bool:
        """Return true if switch is on."""
        # return self._state
        _LOGGER.debug("device_status %s", self.device.status)
        status = [False, True, True, True]
        return status[self.device.status[self.dp_id]['state']]

    def turn_on(self, **kwargs) -> None:
        """Turn the switch on."""
        self.device.set_dp(1, self.dp_id)

    def turn_off(self, **kwargs) -> None:
        """Turn the device off."""
        self.device.set_dp(0, self.dp_id)

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


class FakeSunLoginHaSwitch(SwitchEntity):
    """Tuya Switch Device."""

    platform = 'switch'

    # ToggleEntity

    def __init__(
        self,
        device,
        switchid,
        **kwargs,
    ):
        self.device = device
        self.dp_id = switchid
        self._state = False
        self.entity_id = "switch.Test007_001122334455" + self.dp_id
        _LOGGER.debug("Initialized switch [%s]", self.dp_id)


    async def async_update(self):
        pass

    @property
    def is_on(self) -> bool:
        """Return true if switch is on."""
        # return self._state
        return self._state

    def turn_on(self, **kwargs) -> None:
        """Turn the switch on."""
        self._state = True

    def turn_off(self, **kwargs) -> None:
        """Turn the device off."""
        self._state = False

    @property
    def device_info(self):
        """Return device information for the device registry."""
        model = "Test007"
        return {
            "identifiers": {
                # Serial numbers are unique identifiers within a specific domain
                (DOMAIN, '001122334455')
            },
            "name": "测试设备",
            "manufacturer": "SunLogin",
            "model": f"{model} (001122334455)",
            "sw_version": "0.0.1",
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
        return f"sunlogin_001122334455_{self.dp_id}"

    @property
    def available(self):
        """Return if device is available or not."""
        return True
