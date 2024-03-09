"""Constants for sunlogin integration."""

DOMAIN = "sunlogin"
CLOUD_DATA = "cloud_data"

# Platforms in this list must support config flows
PLATFORMS = [
    "binary_sensor",
    "light",
    "number",
    "select",
    "sensor",
    "switch"
]

SL_DEVICES = "sunlogin_devices"
SL_COORDINATOR = "sunlogin_coordinator"

CONF_SCAN_INTERVAL = "scan_interval"
CONF_NO_CLOUD = "no_cloud"
CONF_SMSCODE = "smscode"
CONF_LOGIN_METHOD = 'login_method'

CONF_USER_INPUT = "user_input"

CONF_LOCAL_KEY = "local_key"
CONF_ENABLE_DEBUG = "enable_debug"
CONF_PROTOCOL_VERSION = "protocol_version"
CONF_DPS_STRINGS = "dps_strings"
CONF_MODEL = "model"
CONF_PRODUCT_KEY = "product_key"
CONF_PRODUCT_NAME = "product_name"
CONF_USER_ID = "user_id"
CONF_ENABLE_ADD_ENTITIES = "add_entities"

CONF_ACTION = "action"
CONF_ADD_DEVICE = "add_device"
CONF_EDIT_DEVICE = "edit_device"
CONF_SETUP_CLOUD = "setup_cloud"
CONF_NO_CLOUD = "no_cloud"
CONF_MANUAL_DPS = "manual_dps_strings"
CONF_DEFAULT_VALUE = "dps_default_value"
CONF_RESET_DPIDS = "reset_dpids"
CONF_PASSIVE_ENTITY = "is_passive_entity"

CONF_SMARTPLUG = "sl_smartplug"
CONF_DEVICE_ID = "device_id"
CONF_DEVICE_TYPE = "device_type"
CONF_DEVICE_SN = "sn"
CONF_DEVICE_MAC = "mac"
CONF_DEVICE_NAME = "name"
CONF_DEVICE_MODEL = "model"
CONF_DEVICE_OUTLET_COUNT = "outletcount"
CONF_DEVICE_ADDRESS = "address"
CONF_IS_ONLINE_ENABLE = "1"
CONF_IS_ONLINE_OFFLINE = "0"

SL_ELECTRIC_MODEL = "C1-2"
SL_ELECTRIC_MODEL_C1_PRO = "C1Pro"
SL_ELECTRIC_MODEL_C2 = "C2"
SL_ELECTRIC_MODEL_V1 = "C1"
SL_POWER_STRIP_MODEL = "P1"
SL_POWER_STRIP_P1PRO_MODEL = "P1Pro"
SL_POWER_STRIP_P2_MODEL = "P2"

MIN_REQUEST_INTERVAL = 60
DEFAULT_SCAN_INTERVAL = 60
