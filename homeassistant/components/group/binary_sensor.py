"""This platform allows several binary sensors to be grouped into one binary sensor."""
import logging
from typing import List, Optional, cast

import voluptuous as vol

from homeassistant.components import binary_sensor
from homeassistant.components.binary_sensor import PLATFORM_SCHEMA
from homeassistant.const import (
    ATTR_DEVICE_CLASS,
    CONF_DEVICE_CLASS,
    CONF_ENTITIES,
    CONF_NAME,
    STATE_ON,
)
from homeassistant.core import CALLBACK_TYPE, State, callback
import homeassistant.helpers.config_validation as cv
from homeassistant.helpers.event import async_track_state_change
from homeassistant.helpers.typing import ConfigType, HomeAssistantType
from homeassistant.util import slugify

# mypy: allow-incomplete-defs, allow-untyped-calls, allow-untyped-defs
# mypy: no-check-untyped-defs

_LOGGER = logging.getLogger(__name__)

DEFAULT_NAME = "Binary Sensor Group"

PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend(
    {
        vol.Optional(CONF_NAME, default=DEFAULT_NAME): cv.string,
        vol.Required(CONF_ENTITIES): cv.entities_domain(binary_sensor.DOMAIN),
        vol.Optional(CONF_DEVICE_CLASS): cv.string,
    }
)


async def async_setup_platform(
    hass: HomeAssistantType, config: ConfigType, async_add_entities, discovery_info=None
) -> None:
    """Initialize binary_sensor.group platform."""
    async_add_entities(
        [
            BinarySensorGroup(
                cast(str, config.get(CONF_NAME)),
                config[CONF_ENTITIES],
                cast(str, config.get(CONF_DEVICE_CLASS)),
            )
        ]
    )


class BinarySensorGroup(binary_sensor.BinarySensorEntity):
    """Representation of a binary sensor group."""

    def __init__(
        self, name: str, entity_ids: List[str], device_class: Optional[str]
    ) -> None:
        """Initialize a binary sensor group."""
        _LOGGER.debug("Created BinarySensorGroup %s", name)
        self.entity_id = "binary_sensor." + slugify(name)
        self._name = name
        self._entity_ids = entity_ids
        self._async_unsub_state_changed: Optional[CALLBACK_TYPE] = None
        self._is_on = False
        self._device_class = device_class

    async def async_added_to_hass(self) -> None:
        """Register callbacks."""

        @callback
        def async_state_changed_listener(
            entity_id: str, old_state: State, new_state: State
        ):
            """Handle child updates."""
            self.async_schedule_update_ha_state(True)

        assert self.hass is not None
        self._async_unsub_state_changed = async_track_state_change(
            self.hass, self._entity_ids, async_state_changed_listener
        )
        await self.async_update()

    async def async_will_remove_from_hass(self):
        """Handle removal from Home Assistant."""
        if self._async_unsub_state_changed is not None:
            self._async_unsub_state_changed()
            self._async_unsub_state_changed = None

    async def async_update(self):
        """Query all members and determine the binary sensor group state."""
        all_states = [self.hass.states.get(x) for x in self._entity_ids]
        states: List[State] = list(filter(None, all_states))
        _LOGGER.debug("Updating from states: %r", states)

        # on_states = [state for state in states if state.state == STATE_ON]
        self._is_on = any(state.state == STATE_ON for state in states)
        if self._device_class is None:
            self._device_class = most_common(
                state.attributes[ATTR_DEVICE_CLASS]
                for state in states
                if ATTR_DEVICE_CLASS in state.attributes
            )

    @property
    def is_on(self):
        """Return true if the binary sensor is on."""
        return self._is_on

    @property
    def device_class(self):
        """Return the class of this device, from component DEVICE_CLASSES."""
        return self._device_class


def most_common(iterable):
    """Find the most common element in the iterable input, and return it."""
    histogram = {}
    for value in iterable:
        histogram[value] = histogram.get(value, 0) + 1

    # find highest peak from histogram items
    value, _ = max(histogram.items(), default=("", 0), key=lambda tuple: tuple[1])
    return value
