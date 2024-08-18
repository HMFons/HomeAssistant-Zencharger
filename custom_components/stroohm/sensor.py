"""Stroohm sensor."""

from datetime import timedelta
import logging

from homeassistant.const import CONF_HOST, CONF_PASSWORD
from homeassistant.exceptions import IntegrationError
from homeassistant.helpers import device_registry as dr
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .const import (
    CONF_CREDENTIALS,
    DOMAIN,
    ID_REALTIME_POWER,
    ID_TOTAL_CURRENT_DAY_ENERGY,
    NAME_REALTIME_POWER,
    NAME_TOTAL_CURRENT_DAY_ENERGY,
)
from .device_real_kpi_coordinator import DeviceRealKpiDataCoordinator
from .stroohm.const import (
    ATTR_DATA_COLLECT_TIME,
    ATTR_DEVICE_REAL_KPI_ACTIVE_POWER,
    ATTR_STATION_CODE,
    ATTR_STATION_REAL_KPI_DATA_ITEM_MAP,
    ATTR_STATION_REAL_KPI_TOTAL_CURRENT_DAY_ENERGY,
)
from .stroohm.energy_sensor import StroohmEnergySensorTotalCurrentDay
from .stroohm.power_entity import StroohmPowerEntityRealtimeInWatt
from .stroohm.stroohm_api import StroohmApi, StroohmApiError

_LOGGER = logging.getLogger(__name__)


def filter_for_enabled_stations(station, device_registry):
    device_from_registry = device_registry.async_get_device(
        identifiers={(DOMAIN, station.code)}
    )
    if device_from_registry is not None and device_from_registry.disabled:
        _LOGGER.debug(
            "Station is disabled by the user",
            extra={"code": station.code, "station": station},
        )
        return False

    return True


async def add_entities_for_stations(
    hass, async_add_entities, stations, api: StroohmApi
):
    device_registry = dr.async_get(hass)
    stations = list(
        filter(lambda x: filter_for_enabled_stations(x, device_registry), stations)
    )
    station_codes = [station.code for station in stations]
    _LOGGER.debug("Adding entities for stations", extra={len(station_codes)})

    await _add_entities_for_stations_real_kpi_data(
        hass, async_add_entities, stations, api
    )
    await _add_entities_for_stations_year_kpi_data(
        hass, async_add_entities, stations, api
    )

    devices = await hass.async_add_executor_job(api.get_dev_list, station_codes)
    devices_grouped_per_type_id = {}
    for device in devices:
        if device.type_id not in devices_grouped_per_type_id:
            devices_grouped_per_type_id[device.type_id] = []
        devices_grouped_per_type_id[device.type_id].append(str(device.device_id))

    await _add_static_entities_for_devices(async_add_entities, devices)

    coordinator = DeviceRealKpiDataCoordinator(hass, api, devices)

    # Fetch initial data so we have data when entities subscribe
    # TODO
    await coordinator.async_refresh()

    for device in devices:
        async_add_entities(
            [
                StroohmPowerEntityRealtimeInWatt(
                    coordinator,
                    f"{DOMAIN}-{device.device_id}-{ID_REALTIME_POWER}",
                    f"{device.readable_name} - {NAME_REALTIME_POWER}",
                    ATTR_DEVICE_REAL_KPI_ACTIVE_POWER,
                    f"{DOMAIN}-{device.device_id}",
                    device.device_info(),
                ),
            ]
        )

        entities_to_create = [
            {
                "class": "StroohmRealtimeDeviceDataTranslatedSensor",
                "attribute": "meter_status",
                "name": "Meter status",
            },
            {
                "class": "StroohmRealtimeDeviceDataVoltageSensor",
                "attribute": "meter_u",
                "name": "Grid voltage",
            },
            {
                "class": "StroohmRealtimeDeviceDataCurrentSensor",
                "attribute": "meter_i",
                "name": "Grid current",
            },
            {
                "class": "StroohmRealtimeDeviceDataPowerInWattSensor",
                "attribute": "active_power",
                "name": "Active power",
            },
            {
                "class": "StroohmRealtimeDeviceDataReactivePowerInVarSensor",
                "attribute": "reactive_power",
                "name": "Reactive power",
            },
            {
                "class": "StroohmRealtimeDeviceDataPowerFactorSensor",
                "attribute": "power_factor",
                "name": "Power factor",
            },
            {
                "class": "StroohmRealtimeDeviceDataFrequencySensor",
                "attribute": "grid_frequency",
                "name": "Grid frequency",
            },
            {
                "class": "StroohmRealtimeDeviceDataEnergySensor",
                "attribute": "active_cap",
                "name": "Active energy (forward active energy)",
            },
            {
                "class": "StroohmRealtimeDeviceDataEnergySensor",
                "attribute": "reverse_active_cap",
                "name": "Reverse active energy",
            },
            {
                "class": "StroohmRealtimeDeviceDataStateBinarySensor",
                "attribute": "run_state",
                "name": "Status",
            },
        ]

        entities = []
        for entity_to_create in entities_to_create:
            class_name = globals()[entity_to_create["class"]]
            entities.append(
                class_name(
                    coordinator,
                    device,
                    entity_to_create["name"],
                    entity_to_create["attribute"],
                )
            )

        async_add_entities(entities)


async def _add_entities_for_stations_real_kpi_data(
    hass, async_add_entities, stations, api: StroohmApi
):
    device_registry = dr.async_get(hass)
    stations = list(
        filter(lambda x: filter_for_enabled_stations(x, device_registry), stations)
    )
    station_codes = [station.code for station in stations]
    _LOGGER.debug(
        "Adding stations_real_kpi_data entities for stations",
        extra={len(station_codes)},
    )

    async def async_update_station_real_kpi_data():
        """Fetch data."""
        data = {}

        if station_codes is None or len(station_codes) == 0:
            return data

        try:
            response = await hass.async_add_executor_job(
                api.get_station_real_kpi, station_codes
            )
        except StroohmApiError as error:
            raise UpdateFailed(f"OpenAPI Error: {error}")

        for response_data in response:
            data[f"{DOMAIN}-{response_data[ATTR_STATION_CODE]}"] = response_data[
                ATTR_STATION_REAL_KPI_DATA_ITEM_MAP
            ]

        return data

    coordinator = DataUpdateCoordinator(
        hass,
        _LOGGER,
        name="StroohmApiStationRealKpi",
        update_method=async_update_station_real_kpi_data,
        update_interval=timedelta(seconds=600),
    )

    # Fetch initial data so we have data when entities subscribe
    await coordinator.async_refresh()

    for station in stations:
        entities_to_create = [
            {
                "class": "StroohmStationAttributeEntity",
                "name": "Station Code",
                "suffix": "station_code",
                "value": station.code,
            },
            {
                "class": "StroohmStationAttributeEntity",
                "name": "Station Name",
                "suffix": "station_name",
                "value": station.name,
            },
            {
                "class": "StroohmStationAddressEntity",
                "name": "Station Address",
                "suffix": "station_address",
                "value": station.address,
            },
            {
                "class": "StroohmStationCapacityEntity",
                "name": "Capacity",
                "suffix": "capacity",
                "value": station.capacity,
            },
            {
                "class": "StroohmStationContactPersonEntity",
                "name": "Contact Person",
                "suffix": "contact_person",
                "value": station.contact_person,
            },
            {
                "class": "StroohmStationContactPersonPhoneEntity",
                "name": "Contact Phone",
                "suffix": "contact_phone",
                "value": station.contact_phone,
            },
        ]

        entities = []
        for entity_to_create in entities_to_create:
            class_name = globals()[entity_to_create["class"]]
            entities.append(
                class_name(
                    station,
                    entity_to_create["name"],
                    entity_to_create["suffix"],
                    entity_to_create["value"],
                )
            )
        async_add_entities(entities)

        async_add_entities(
            [
                StroohmEnergySensorTotalCurrentDay(
                    coordinator,
                    f"{DOMAIN}-{station.code}-{ID_TOTAL_CURRENT_DAY_ENERGY}",
                    f"{station.readable_name} - {NAME_TOTAL_CURRENT_DAY_ENERGY}",
                    ATTR_STATION_REAL_KPI_TOTAL_CURRENT_DAY_ENERGY,
                    f"{DOMAIN}-{station.code}",
                    station.device_info(),
                )
            ]
        )


async def _add_entities_for_stations_year_kpi_data(
    hass, async_add_entities, stations, api: StroohmApi
):
    device_registry = dr.async_get(hass)
    stations = list(
        filter(lambda x: filter_for_enabled_stations(x, device_registry), stations)
    )
    station_codes = [station.code for station in stations]
    _LOGGER.debug(
        "Adding stations_year_kpi_data entities for stations",
        extra={len(station_codes)},
    )

    async def async_update_station_year_kpi_data():
        data = {}

        if station_codes is None or len(station_codes) == 0:
            return data

        try:
            response = await hass.async_add_executor_job(
                api.get_kpi_station_year, station_codes
            )
        except StroohmApiError as error:
            raise UpdateFailed(f"OpenAPI Error: {error}")

        for response_data in response:
            key = f"{DOMAIN}-{response_data[ATTR_STATION_CODE]}"

            if key not in data:
                data[key] = {}

            data[key][response_data[ATTR_DATA_COLLECT_TIME]] = response_data[
                ATTR_STATION_REAL_KPI_DATA_ITEM_MAP
            ]

        _LOGGER.debug("async_update_station_year_kpi_data.", extra={data})

        return data

    coordinator = DataUpdateCoordinator(
        hass,
        _LOGGER,
        name="StroohmOpenAPIStationYearKpi",
        update_method=async_update_station_year_kpi_data,
        update_interval=timedelta(hours=1),
    )

    # Fetch initial data so we have data when entities subscribe
    await coordinator.async_refresh()

    for station in stations:
        entities_to_create = [
            {"class": "StroohmYearPlantDataInstalledCapacitySensor"},
            {"class": "StroohmYearPlantDataRadiationIntensitySensor"},
            {"class": "StroohmYearPlantDataTheoryPowerSensor"},
            {"class": "StroohmYearPlantDataPerformanceRatioSensor"},
            {"class": "StroohmYearPlantDataInverterPowerSensor"},
            {"class": "StroohmBackwardsCompatibilityTotalCurrentYear"},
            {"class": "StroohmYearPlantDataOngridPowerSensor"},
            {"class": "StroohmYearPlantDataUsePowerSensor"},
            {"class": "StroohmYearPlantDataPowerProfitSensor"},
            {"class": "StroohmYearPlantDataPerpowerRatioSensor"},
            {"class": "StroohmYearPlantDataReductionTotalCo2Sensor"},
            {"class": "StroohmYearPlantDataReductionTotalCoalSensor"},
            {"class": "StroohmYearPlantDataReductionTotalTreeSensor"},
            {"class": "StroohmLifetimePlantDataInverterPowerSensor"},
            {"class": "StroohmLifetimePlantDataOngridPowerSensor"},
            {"class": "StroohmLifetimePlantDataUsePowerSensor"},
            {"class": "StroohmLifetimePlantDataPowerProfitSensor"},
            {"class": "StroohmLifetimePlantDataPerpowerRatioSensor"},
            {"class": "StroohmLifetimePlantDataReductionTotalCo2Sensor"},
            {"class": "StroohmLifetimePlantDataReductionTotalCoalSensor"},
            {"class": "StroohmLifetimePlantDataReductionTotalTreeSensor"},
        ]

        entities = []
        for entity_to_create in entities_to_create:
            class_name = globals()[entity_to_create["class"]]
            entities.append(class_name(coordinator, station))
        async_add_entities(entities)


async def _add_static_entities_for_devices(async_add_entities, devices):
    for device in devices:
        entities_to_create = [
            {
                "class": "StroohmDeviceAttributeEntity",
                "name": "Device ID",
                "suffix": "device_id",
                "value": device.device_id,
            },
            {
                "class": "StroohmDeviceAttributeEntity",
                "name": "Device name",
                "suffix": "device_name",
                "value": device.name,
            },
            {
                "class": "StroohmDeviceAttributeEntity",
                "name": "Station code",
                "suffix": "station_code",
                "value": device.station_code,
            },
            {
                "class": "StroohmDeviceAttributeEntity",
                "name": "Serial number",
                "suffix": "esn_code",
                "value": device.esn_code,
            },
            {
                "class": "StroohmDeviceAttributeEntity",
                "name": "Device type ID",
                "suffix": "device_type_id",
                "value": device.type_id,
            },
            {
                "class": "StroohmDeviceAttributeEntity",
                "name": "Device type",
                "suffix": "device_type",
                "value": device.device_type,
            },
            {
                "class": "StroohmDeviceLatitudeEntity",
                "name": "Latitude",
                "suffix": "latitude",
                "value": device.latitude,
            },
            {
                "class": "StroohmDeviceLongitudeEntity",
                "name": "Longitude",
                "suffix": "longitude",
                "value": device.longitude,
            },
        ]

        entities = []
        for entity_to_create in entities_to_create:
            class_name = globals()[entity_to_create["class"]]
            entities.append(
                class_name(
                    device,
                    entity_to_create["name"],
                    entity_to_create["suffix"],
                    entity_to_create["value"],
                )
            )
        async_add_entities(entities)


async def async_setup_entry(hass, config_entry, async_add_entities):
    config = hass.data[DOMAIN][config_entry.entry_id]
    # Update our config to include new repos and remove those that have been removed.
    if config_entry.options:
        config.update(config_entry.options)

    if config[CONF_CREDENTIALS]:
        # get stations from openapi
        api = StroohmApi(
            config[CONF_CREDENTIALS][CONF_HOST],
            config[CONF_CREDENTIALS][CONF_PASSWORD],
        )
        stations = await hass.async_add_executor_job(api.get_station_list)

        if not stations:
            _LOGGER.error("No stations found")
            raise IntegrationError("No stations found in OpenAPI")

        if len(stations) > 100:
            _LOGGER.error("More than 100 stations found, which is not a good idea!")

        await add_entities_for_stations(hass, async_add_entities, stations, api)
