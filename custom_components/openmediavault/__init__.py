"""The OpenMediaVault integration."""

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryNotReady
from homeassistant.helpers.device_registry import DeviceEntry

from .const import DOMAIN, PLATFORMS
from .omv_controller import OMVControllerData


# ---------------------------
#   async_setup
# ---------------------------
async def async_setup(hass: HomeAssistant, config_entry: ConfigEntry) -> bool:
    """Set up configured OMV Controller."""
    hass.data[DOMAIN] = {}
    return True


# ---------------------------
#   update_listener
# ---------------------------
async def _async_update_listener(hass: HomeAssistant, config_entry: ConfigEntry):
    """Handle options update."""
    await hass.config_entries.async_reload(config_entry.entry_id)


# ---------------------------
#   async_setup_entry
# ---------------------------
async def async_setup_entry(hass: HomeAssistant, config_entry: ConfigEntry) -> bool:
    """Set up OMV config entry."""
    hass.data.setdefault(DOMAIN, {})
    controller = OMVControllerData(hass, config_entry)
    await controller.async_hwinfo_update()
    await controller.async_update()

    if not controller.data:
        raise ConfigEntryNotReady()

    await controller.async_init()
    hass.data[DOMAIN][config_entry.entry_id] = controller

    await hass.config_entries.async_forward_entry_setups(config_entry, PLATFORMS)
    config_entry.async_on_unload(
        config_entry.add_update_listener(_async_update_listener)
    )

    return True


# ---------------------------
#   async_unload_entry
# ---------------------------
async def async_unload_entry(hass: HomeAssistant, config_entry: ConfigEntry) -> bool:
    """Unload OMV config entry."""
    unload_ok = await hass.config_entries.async_unload_platforms(
        config_entry, PLATFORMS
    )
    if unload_ok:
        controller = hass.data[DOMAIN][config_entry.entry_id]
        await controller.async_reset()
        hass.data[DOMAIN].pop(config_entry.entry_id)

    return True


# ---------------------------
#   async_remove_config_entry_device
# ---------------------------
async def async_remove_config_entry_device(
    hass: HomeAssistant, config_entry: ConfigEntry, device_entry: DeviceEntry
) -> bool:
    """Allow manual removal of a stale device while the entry stays loaded.

    Without this, Home Assistant only ever offers "disable" for devices
    tied to a still-loaded config entry, never "delete". Device identity
    here (see model.py's device_info) is partly derived from live data
    (e.g. the System device keys off the fetched hostname), which only
    ever shows its real value once a connection has actually succeeded -
    before that, entities register under an "unknown"-keyed device. If
    the very first connection attempt after adding the integration fails
    (which was common before the OMV 7/8 fixes in this fork), that
    "unknown" device is orphaned forever once a later successful update
    creates a second, correctly-keyed device - Home Assistant does not
    merge them automatically. Always allowing removal here is safe: any
    device that is still genuinely backed by live entities gets
    recreated automatically on the next coordinator update.
    """
    return True
