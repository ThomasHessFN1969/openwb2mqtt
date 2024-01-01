"""The openwbmqtt component for controlling the openWB wallbox via home assistant / MQTT."""
from __future__ import annotations

import copy
from datetime import timedelta
from homeassistant.components import mqtt
from homeassistant.components.sensor import SensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.device_registry import async_get as async_get_dev_reg
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.typing import StateType
from homeassistant.util import dt, slugify
import logging
import re
import json

from .common import OpenWBBaseEntity

# Import global values.
from .const import (
    # CHARGE_POINTS,
    MQTT_ROOT_TOPIC,
    SENSORS_GLOBAL,
    SENSORS_PER_LP,
    openwbSensorEntityDescription,
    SENSORS_PER_CHARGEPOINT,
    SENSORS_PER_COUNTER,
    SENSORS_PER_BATTERY,
    SENSORS_PER_PVGENERATOR,
    SENSORS_CONTROLLER,
    MANUFACTURER,
)

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant, config: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    """Set up sensors for openWB."""

    integrationUniqueID = config.unique_id
    mqttRoot = config.data[MQTT_ROOT_TOPIC]
    devicetype = config.data["DEVICETYPE"]
    deviceID = config.data["DEVICEID"]
    # nChargePoints = config.data[CHARGE_POINTS]
    sensorList = []

    if devicetype == "controller":
        SENSORS_CONTROLLER_CP = copy.deepcopy(SENSORS_CONTROLLER)
        for description in SENSORS_CONTROLLER_CP:
            description.mqttTopicCurrentValue = f"{mqttRoot}/{description.key}"
            sensorList.append(
                openwbSensor(
                    uniqueID=f"{integrationUniqueID}",
                    description=description,
                    device_friendly_name=MANUFACTURER,
                    mqtt_root=mqttRoot,
                )
            )

    if devicetype == "chargepoint":
        # Create sensors for chargepoint
        SENSORS_PER_CHARGEPOINT_CP = copy.deepcopy(SENSORS_PER_CHARGEPOINT)
        for description in SENSORS_PER_CHARGEPOINT_CP:
            description.mqttTopicCurrentValue = (
                # f"{mqttRoot}/{devicetype}/{deviceID}/get/{description.key}"
                f"{mqttRoot}/{devicetype}/{deviceID}/{description.key}"
            )
            sensorList.append(
                openwbSensor(
                    uniqueID=f"{integrationUniqueID}",
                    description=description,
                    device_friendly_name=f"Chargepoint {deviceID}",
                    mqtt_root=mqttRoot,
                )
            )
    if devicetype == "counter":
        # Create sensors for counters, for example EVU
        SENSORS_PER_COUNTER_CP = copy.deepcopy(SENSORS_PER_COUNTER)
        for description in SENSORS_PER_COUNTER_CP:
            description.mqttTopicCurrentValue = (
                f"{mqttRoot}/{devicetype}/{deviceID}/get/{description.key}"
            )
            sensorList.append(
                openwbSensor(
                    uniqueID=f"{integrationUniqueID}",
                    description=description,
                    device_friendly_name=f"Counter {deviceID}",
                    mqtt_root=mqttRoot,
                )
            )

    if devicetype == "bat":
        # Create sensors for batteries
        SENSORS_PER_BATTERY_CP = copy.deepcopy(SENSORS_PER_BATTERY)
        for description in SENSORS_PER_BATTERY_CP:
            description.mqttTopicCurrentValue = (
                f"{mqttRoot}/{devicetype}/{deviceID}/get/{description.key}"
            )
            sensorList.append(
                openwbSensor(
                    uniqueID=f"{integrationUniqueID}",
                    description=description,
                    device_friendly_name=f"Battery {deviceID}",
                    mqtt_root=mqttRoot,
                )
            )

    if devicetype == "pv":
        # Create sensors for batteries
        SENSORS_PER_PVGENERATOR_CP = copy.deepcopy(SENSORS_PER_PVGENERATOR)
        for description in SENSORS_PER_PVGENERATOR_CP:
            description.mqttTopicCurrentValue = (
                f"{mqttRoot}/{devicetype}/{deviceID}/get/{description.key}"
            )
            sensorList.append(
                openwbSensor(
                    uniqueID=f"{integrationUniqueID}",
                    description=description,
                    device_friendly_name=f"PV {deviceID}",
                    mqtt_root=mqttRoot,
                )
            )

    # # Create all global sensors.
    # global_sensors = copy.deepcopy(SENSORS_GLOBAL)
    # for description in global_sensors:
    #     description.mqttTopicCurrentValue = f"{mqttRoot}/{description.key}"
    #     _LOGGER.debug("mqttTopic: %s", description.mqttTopicCurrentValue)
    #     sensorList.append(
    #         openwbSensor(
    #             uniqueID=integrationUniqueID,
    #             description=description,
    #             device_friendly_name=integrationUniqueID,
    #             mqtt_root=mqttRoot,
    #         )
    #     )

    # # Create all sensors for each charge point, respectively.
    # for chargePoint in range(1, nChargePoints + 1):
    #     local_sensors_per_lp = copy.deepcopy(SENSORS_PER_LP)
    #     for description in local_sensors_per_lp:
    #         description.mqttTopicCurrentValue = (
    #             f"{mqttRoot}/lp/{str(chargePoint)}/{description.key}"
    #         )
    #         _LOGGER.debug("mqttTopic: %s", description.mqttTopicCurrentValue)
    #         sensorList.append(
    #             openwbSensor(
    #                 uniqueID=integrationUniqueID,
    #                 description=description,
    #                 nChargePoints=int(nChargePoints),
    #                 currentChargePoint=chargePoint,
    #                 device_friendly_name=integrationUniqueID,
    #                 mqtt_root=mqttRoot,
    #             )
    #         )

    async_add_entities(sensorList)


class openwbSensor(OpenWBBaseEntity, SensorEntity):
    """Representation of an openWB sensor that is updated via MQTT."""

    entity_description: openwbSensorEntityDescription

    def __init__(
        self,
        uniqueID: str | None,
        device_friendly_name: str,
        mqtt_root: str,
        description: openwbSensorEntityDescription,
        nChargePoints: int | None = None,
        currentChargePoint: int | None = None,
    ) -> None:
        """Initialize the sensor and the openWB device."""
        super().__init__(
            device_friendly_name=device_friendly_name,
            mqtt_root=mqtt_root,
        )

        self.entity_description = description

        if nChargePoints:
            self._attr_unique_id = slugify(
                f"{uniqueID}-CP{currentChargePoint}-{description.name}"
            )
            self.entity_id = (
                f"sensor.{uniqueID}-CP{currentChargePoint}-{description.name}"
            )
            self._attr_name = f"{description.name} (LP{currentChargePoint})"
        else:
            self._attr_unique_id = slugify(f"{uniqueID}-{description.name}")
            self.entity_id = f"sensor.{uniqueID}-{description.name}"
            self._attr_name = description.name

    async def async_added_to_hass(self):
        """Subscribe to MQTT events."""

        @callback
        def message_received(message):
            """Handle new MQTT messages."""
            self._attr_native_value = message.payload

            # Convert data if a conversion function is defined
            if self.entity_description.value_fn is not None:
                self._attr_native_value = self.entity_description.value_fn(
                    self._attr_native_value
                )

            # Map values as defined in the value map dict.
            # First try to map integer values, then string values.
            # If no value can be mapped, use original value without conversion.
            if self.entity_description.valueMap is not None:
                try:
                    self._attr_native_value = self.entity_description.valueMap.get(
                        int(self._attr_native_value)
                    )
                except ValueError:
                    self._attr_native_value = self.entity_description.valueMap.get(
                        self._attr_native_value, self._attr_native_value
                    )

            # Reformat TimeRemaining --> timestamp.
            if "TimeRemaining" in self.entity_description.key:
                now = dt.utcnow()
                if "H" in self._attr_native_value:
                    tmp = self._attr_native_value.split()
                    delta = timedelta(hours=int(tmp[0]), minutes=int(tmp[2]))
                    self._attr_native_value = now + delta
                elif "Min" in self._attr_native_value:
                    tmp = self._attr_native_value.split()
                    delta = timedelta(minutes=int(tmp[0]))
                    self._attr_native_value = now + delta
                else:
                    self._attr_native_value = None

            # Reformat uptime sensor
            if "uptime" in self.entity_id:
                reluptime = re.match(
                    ".*\sup\s(.*),.*\d*user.*", self._attr_native_value
                )[1]
                days = 0
                if re.match("(\d*)\sday.*", reluptime):
                    days = re.match("(\d*)\sday", reluptime)[1]
                    reluptime = re.match(".*,\s(.*)", reluptime)[1]
                if re.match(".*min", reluptime):
                    hours = 0
                    mins = re.match("(\d*)\s*min", reluptime)[1]
                else:
                    hours, mins = re.match("\s?(\d*):0?(\d*)", reluptime).group(1, 2)
                self._attr_native_value = f"{days} d {hours} h {mins} min"

            # If MQTT message contains IP --> set up configuration_url to visit the device
            elif "ip_adress" in self.entity_id:
                device_registry = async_get_dev_reg(self.hass)
                device = device_registry.async_get_device(
                    self.device_info.get("identifiers")
                )
                device_registry.async_update_device(
                    device.id,
                    configuration_url=f"http://{message.payload}",
                )
                # device_registry.async_update_device
            # If MQTT message contains version --> set sw_version of the device
            elif "version" in self.entity_id:
                device_registry = async_get_dev_reg(self.hass)
                device = device_registry.async_get_device(
                    self.device_info.get("identifiers")
                )
                device_registry.async_update_device(
                    device.id, sw_version=message.payload
                )
                # device_registry.async_update_device
            elif "ladepunkt" in self.entity_id:
                device_registry = async_get_dev_reg(self.hass)
                device = device_registry.async_get_device(
                    self.device_info.get("identifiers")
                )
                try:
                    device_registry.async_update_device(
                        device.id,
                        name=json.loads(message.payload).get("name").replace('"', ""),
                    )
                except:
                    NotImplemented

            # Update icon of countPhasesInUse
            elif (
                "countPhasesInUse" in self.entity_description.key
                or "phases_in_use" in self.entity_description.key
            ):
                if int(message.payload) == 0:
                    self._attr_icon = "mdi:numeric-0-circle-outline"
                elif int(message.payload) == 1:
                    self._attr_icon = "mdi:numeric-1-circle-outline"
                elif int(message.payload) == 3:
                    self._attr_icon = "mdi:numeric-3-circle-outline"
                else:
                    self._attr_icon = "mdi:numeric"

            # Update entity state with value published on MQTT.
            self.async_write_ha_state()

        # Subscribe to MQTT topic and connect callack message
        await mqtt.async_subscribe(
            self.hass,
            self.entity_description.mqttTopicCurrentValue,
            message_received,
            1,
        )
        _LOGGER.debug(
            "Subscribed to MQTT topic: %s",
            self.entity_description.mqttTopicCurrentValue,
        )
