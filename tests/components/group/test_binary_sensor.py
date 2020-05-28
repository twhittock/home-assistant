"""The tests for the Group Light platform."""
from homeassistant.components.binary_sensor import (
    DEVICE_CLASS_WINDOW,
    DOMAIN as BINARY_SENSOR_DOMAIN,
)
from homeassistant.components.group import DOMAIN
from homeassistant.components.group.binary_sensor import most_common
from homeassistant.const import (
    ATTR_DEVICE_CLASS,
    CONF_DEVICE_CLASS,
    CONF_ENTITIES,
    CONF_NAME,
    CONF_PLATFORM,
    STATE_OFF,
    STATE_ON,
)
from homeassistant.setup import async_setup_component


async def test_default_state(hass):
    """Test binary sensor group default state."""
    await async_setup_component(
        hass,
        BINARY_SENSOR_DOMAIN,
        {
            BINARY_SENSOR_DOMAIN: {
                CONF_PLATFORM: DOMAIN,
                CONF_NAME: "Test Group",
                CONF_ENTITIES: [],
            }
        },
    )
    await hass.async_block_till_done()

    state = hass.states.get("binary_sensor.test_group")
    assert state is not None
    assert state.state == STATE_OFF
    assert state.attributes[ATTR_DEVICE_CLASS] == ""


async def test_override_device_class(hass):
    """Test binary sensor group when explicitly defining the device class."""
    await async_setup_component(
        hass,
        BINARY_SENSOR_DOMAIN,
        {
            BINARY_SENSOR_DOMAIN: {
                CONF_PLATFORM: DOMAIN,
                CONF_NAME: "Test Group",
                CONF_DEVICE_CLASS: DEVICE_CLASS_WINDOW,
                CONF_ENTITIES: [],
            }
        },
    )
    await hass.async_block_till_done()

    state = hass.states.get("binary_sensor.test_group")
    assert state is not None
    assert state.state == STATE_OFF
    assert state.attributes[ATTR_DEVICE_CLASS] == DEVICE_CLASS_WINDOW


async def test_state_reporting(hass):
    """Test the state reporting."""
    await async_setup_component(
        hass,
        BINARY_SENSOR_DOMAIN,
        {
            BINARY_SENSOR_DOMAIN: [
                {"platform": "demo"},
                {
                    "platform": DOMAIN,
                    "name": "Test Group",
                    "entities": ["binary_sensor.binary_1", "binary_sensor.binary_2"],
                },
            ],
        },
    )

    hass.states.async_set("binary_sensor.binary_1", STATE_ON)
    hass.states.async_set("binary_sensor.binary_2", STATE_ON)
    await hass.async_block_till_done()
    assert hass.states.get("binary_sensor.test_group").state == STATE_ON

    hass.states.async_set("binary_sensor.binary_1", STATE_ON)
    hass.states.async_set("binary_sensor.binary_2", STATE_OFF)
    await hass.async_block_till_done()
    assert hass.states.get("binary_sensor.test_group").state == STATE_ON

    hass.states.async_set("binary_sensor.binary_1", STATE_OFF)
    hass.states.async_set("binary_sensor.binary_2", STATE_ON)
    await hass.async_block_till_done()
    assert hass.states.get("binary_sensor.test_group").state == STATE_ON

    hass.states.async_set("binary_sensor.binary_1", STATE_OFF)
    hass.states.async_set("binary_sensor.binary_2", STATE_OFF)
    await hass.async_block_till_done()
    assert hass.states.get("binary_sensor.test_group").state == STATE_OFF


async def test_most_common(hass):
    """Test the common device class functionality."""
    assert most_common([]) == ""
    assert most_common(["a", "a", "a", "b"]) == "a"
    assert most_common(["a", "a", "b", "b"]) == "a"  # first wins when equal
