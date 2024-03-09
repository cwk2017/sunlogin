import functools
import hashlib
import json
import logging
import time
import uuid
import asyncio
import requests
import async_timeout
from datetime import timedelta

from urllib.parse import urlencode
from homeassistant.components.switch import DOMAIN as SWITCH_DOMAIN
from homeassistant.components.sensor import DOMAIN as SENSOR_DOMAIN

from homeassistant.const import (
    CONF_UNIT_OF_MEASUREMENT,
    CONF_PLATFORM,
)

from homeassistant.helpers.update_coordinator import (
    DataUpdateCoordinator,
)

_LOGGER = logging.getLogger(__name__)

APP_ID = 'kNUC97u86Zr7mt9xeZVl'
TERMINAL_NAME = 'iPhone14Plus'
PASSWORD = 'password'
SMS = 'securecode'
USER_AGENT = 'SLCC/13.5.0 (IOS,appname=sunloginControlClient)'
CLIENT_ID = '8ae73501-7def-5b19-b57d-52d15ae1e40b'
DEVICE_ID = '59db6b6abd82d8-a6ab17d7865e38c-7bdd362b-a3f44e-909e6a652509d1'
HTTPS_SUFFIX = 'https://'
HTTP_SUFFIX = 'http://'
BASE_URL = HTTPS_SUFFIX + 'api-std.sunlogin.oray.com'
AUTH_LOGIN = '/authorize/code'
AUTH_REFRESH = '/authorize/refreshing'
LOGIN_URL = BASE_URL + '/authorization'
DEVICES_URL = BASE_URL + '/wakeup/devices'
HEAD_AUTH = 'Authorization'
AUTH_SUFFIX = 'Bearer '
CLIENT_SALT = '==SunLogin@2023=='
LANGUAGE = 'zh-Hans_US'

class SunLogin:
    def __init__(self, hass, username, password, smscode):
        """Initialize the class."""
        self.hass = hass
        self.username = username
        self.password = password
        self.smscode = smscode
        self.access_token = ''
        self.refresh_token = ''
        self.client_id = ''
        self.device_id = ''
        self.refresh_expire = 0
        self.headers = {}
        self.device_list = {}
        self.cookies = []
        # self.random_cookies()
        self.fake_client()
        self.fake_headers()

    def fake_client(self, flag = 1):
        if flag == 1: 
            fake_host = '.'.join([self.username, CLIENT_SALT, 'xyz'])
            self.client_id = str(uuid.uuid5(uuid.NAMESPACE_DNS, fake_host))
        else:
            self.client_id = str(uuid.uuid4())

    def random_device(self):
        uuid16 = ''
        device_id = list()
        for _ in range(4):
           uuid16 += str(uuid.uuid4()).replace('-','')
        for i in [14, 15, 8, 6, 14]:
            device_id.append(uuid16[:i])
            uuid16 = uuid16[i:]
        self.device_id = '-'.join(device_id)

    def random_cookies(self):
        self.random_device()
        self.cookies[1]['sensorsdata2015jssdkcross']['distinct_id'] = self.device_id
        self.cookies[1]['sensorsdata2015jssdkcross']['$device_id'] = self.device_id

    def fake_headers(self):
        self.headers['User-Agent'] = USER_AGENT
        self.headers['X-AppID'] = APP_ID
        self.headers['Accept'] = '*/*'
        self.headers['Country-Region'] = LANGUAGE
        self.headers['Accept-Language'] = LANGUAGE
        self.headers['EX-ClientId'] = self.client_id
        # self.headers['Cookie'] = '; '.join([urlencode(_) for _ in self.cookies])

    async def async_req_login(self, fake_body):
        func = functools.partial(requests.post, LOGIN_URL, headers=self.headers, data=json.dumps(fake_body))

        response = await self.hass.async_add_executor_job(func)
        return response


    async def async_req_devices(self):
        fake_headers = self.headers.copy()
        fake_headers[HEAD_AUTH] = AUTH_SUFFIX + self.access_token

        func = functools.partial(requests.get, DEVICES_URL, headers=fake_headers)

        response = await self.hass.async_add_executor_job(func)
        return response
    
    async def async_get_access_token(self, method):
        fake_body = {
            "loginname" : self.username,
            "terminal_name" : TERMINAL_NAME,
        }
        if method == 'password':
            fake_body['type'] = PASSWORD
            fake_body['ismd5'] = True
            fake_body['password'] = hashlib.md5(self.password.encode()).hexdigest()
        else:
            fake_body['type'] = SMS
            fake_body['medium'] = 'sms'
            fake_body['code'] = self.smscode

        try:
            resp = await self.async_req_login(fake_body)  
        except requests.exceptions.ConnectionError:
            return "Request failed, status ConnectionError"

        if not resp.ok:
            r_json = {"error": ''}
            try: 
                r_json = resp.json()
            except: pass
            return r_json.get('error')

        r_json = resp.json()
        self.access_token = r_json.get('access_token', '')
        self.refresh_token = r_json.get('refresh_token', '')
        self.refresh_expire = time.time() + r_json.get('refresh_ttl', 0)/1000

        return "ok"

    async def async_get_devices_list(self):
        try:
            resp = await self.async_req_devices()
        except requests.exceptions.ConnectionError:
            return "Request failed, status ConnectionError"

        if not resp.ok:
            r_json = {"error": ''}
            try: 
                r_json = resp.json()
            except: pass
            return r_json.get('error')

        r_json = resp.json()
        if len(r_json["devices"]) == 0:
            return 'No device'
        
        self.device_list = {dev["sn"]: dev for dev in r_json["devices"]}
        
        return "ok"



class SunLoginDevice:

    ACTION = "action"
    ADDR = "addr"
    API = "_api"
    PATH = "/plug"
    KEY = "key"
    TIME = "time"
    PLUGIN_SCHEMA = "==smart-plug=="
    MEMORY_STATUS = "2"
    ELECTRIC_MODEL = ["C1-2", "C2", "P1", "P1Pro", "SunLogin generic"]
    API_ADD_CUT_DOWN = "plug_cntdown_add"
    API_BIND = "bind_plug"
    API_DELETE_CUT_DOWN = "plug_cntdown_del"
    API_DELETE_TIME = "plug_timer_del"
    API_ENABLE_TIME = "plug_timer_set"
    API_GET_CUT_DOWN = "plug_cntdown_get"
    API_GET_PLUG_ELECTRIC = "get_plug_electric"
    API_GET_PLUG_INFO = "get_plug_info"
    API_GET_POWER_STRIP_TIME = "plug_timer_get"
    API_GET_SN = "get_plug_sn"
    API_GET_STATUS = "get_plug_status"
    API_GET_VERSION = "get_plug_version"
    API_GET_WIFI_INFO = "get_plug_wifi"
    API_SET_PLUG_DFLTSTAT = "set_plug_dfltstat"
    API_SET_PLUG_LED = "set_plug_led"
    API_SET_STATUS = "set_plug_status"
    API_SET_TIME = "plug_timer_add"
    API_UPGRADE = "plug_upgrade"
    API_UPGRADE_STATUS = "plug_upgrade_status"
    DP_RELAY_0 = "relay0"
    DP_RELAY_1 = "relay1"
    DP_RELAY_2 = "relay2"
    DP_RELAY_3 = "relay3"
    DP_RELAY_4 = "relay4"
    DP_RELAY_5 = "relay5"
    DP_RELAY_6 = "relay6"
    DP_RELAY_7 = "relay7"
    DP_LED = "led"
    DP_DEFAULT = "def_st"
    DP_RELAY = "response"
    DP_ELECTRIC = "electric"


    def __init__(self, hass, config_entry, sn, scan_interval):
        self.hass = hass
        self.scan_interval = max(scan_interval, 60)
        self.config_entry = config_entry
        self.sn = sn
        self.ip = config_entry.get('ip', '')
        self.mac = config_entry.get('mac', '')
        self.friendly_name = config_entry.get('name', '智能插座')
        self.model = config_entry.get('model', 'SunLogin generic')
        self.host_name = ''
        self.outletcount = config_entry.get('outletcount', 0)
        self.version = ''
        self.address = config_entry.get('address', '')
        self.remote_address = config_entry.get('address', '')
        self.local_address = ''
        self.status = {}
        self.entities = []
        self.req_time = 0
        self.connect_task = None
        self.disconnect_task = None

    def async_connect(self):
        self.connect_task = asyncio.create_task(self.async_get_info())
        # await self.connect_task
    
    async def async_make_request(self, payload):
        address = self.address + self.PATH

        func = functools.partial(requests.get, address, params=payload)
        resp = await self.hass.async_add_executor_job(func)
        _LOGGER.debug("address: %s", address)
        _LOGGER.debug("payload: %s", payload)
        _LOGGER.debug("response: %s", resp.text)
        return resp

    def make_request(self, payload):
        address = self.address + self.PATH

        func = functools.partial(requests.get, address, params=payload)
        # resp = await self.hass.async_add_executor_job(func)
        resp = func()

        _LOGGER.debug("address: %s", address)
        _LOGGER.debug("payload: %s", payload)
        _LOGGER.debug("response: %s", resp.text)
        return resp
    
    def make_payload(self, api=None):
        t = self.get_time()
        key = self.device_key(t)
        payload = {
            self.API: api,
            self.KEY: key,
            self.TIME: t
        }
        return payload

    def set_dp(self, state, dp_id):
        dp = self.status[dp_id]
        api = dp.get('api', self.API_GET_STATUS)
        payload = self.make_payload(api)
        index = dp.get('index', 0)
        state_key = dp.get('key')
        value = dp.get('value')[state]
        payload['index'] = index
        payload[state_key] = value
        try:
            resp = self.make_request(payload)
        except requests.exceptions.ConnectionError:
            return "Request failed, status ConnectionError"

        if not resp.ok:
            return "Request failed, status " + str(resp.status_code)

        r_json = resp.json()
        if not r_json["result"]:
            self.status[dp_id]['state'] = state


    async def async_update(self):
        # if self.req_time + self.scan_interval <= time.time():
        if self.req_time <= time.time():
            await self.async_get_status()
            if self.model in self.ELECTRIC_MODEL:
                await self.async_get_electric()
            return True

        return False
            

    async def async_update_electric(self):
        payload = self.make_payload(self.API_GET_PLUG_ELECTRIC)
        try:
            resp = await self.async_make_request(payload)
        except requests.exceptions.ConnectionError:
            return "Request failed, status ConnectionError"

        if not resp.ok:
            return "Request failed, status " + str(resp.status_code)

        r_json = resp.json()
        if not r_json["result"]:
            vol = r_json['vol']
            curr = r_json['curr']
            power = r_json['power']
            self.status[self.DP_ELECTRIC]['vol']['state'] = vol
            self.status[self.DP_ELECTRIC]['curr']['state'] = curr
            self.status[self.DP_ELECTRIC]['power']['state'] = power
            self.req_time = time.time()


    async def async_update_status(self):
        payload = self.make_payload(self.API_GET_STATUS)
        try:
            resp = await self.async_make_request(payload)
        except requests.exceptions.ConnectionError:
            return "Request failed, status ConnectionError"

        if not resp.ok:
            return "Request failed, status " + str(resp.status_code)

        r_json = resp.json()
        if not r_json["result"]:
            relay = [self.DP_RELAY_0,self.DP_RELAY_1,self.DP_RELAY_2,self.DP_RELAY_3,
                self.DP_RELAY_4,self.DP_RELAY_5,self.DP_RELAY_6,self.DP_RELAY_7]
            led = r_json[self.DP_LED]
            def_st = r_json[self.DP_DEFAULT]
            for relay_state in r_json[self.DP_RELAY]:
                index = relay_state['index']
                state = relay_state['status']
                self.status[relay[index]]['state'] = state
            
            self.status[self.DP_LED]['state'] = led
            self.status[self.DP_DEFAULT]['state'] = def_st
            self.req_time = time.time()


    async def async_get_status(self):
        payload = self.make_payload(self.API_GET_STATUS)
        try:
            resp = await self.async_make_request(payload)
        except requests.exceptions.ConnectionError:
            return "Request failed, status ConnectionError"

        if not resp.ok:
            return "Request failed, status " + str(resp.status_code)

        r_json = resp.json()
        if not r_json["result"]:
            relay = [self.DP_RELAY_0,self.DP_RELAY_1,self.DP_RELAY_2,self.DP_RELAY_3,
                self.DP_RELAY_4,self.DP_RELAY_5,self.DP_RELAY_6,self.DP_RELAY_7]
            led = r_json.get(self.DP_LED, None)
            def_st = r_json.get(self.DP_DEFAULT, None)
            for relay_state in r_json[self.DP_RELAY]:
                index = relay_state['index']
                state = relay_state['status']
                self.status[relay[index]] = {'index':index,'state':state,'value':[0,1],'key':'status','api':self.API_SET_STATUS}
                self.entities.append({'dp_id': relay[index], CONF_PLATFORM: SWITCH_DOMAIN})
            if led is not None:
                self.status[self.DP_LED] = {'state':led,'value':[0,1],'key':'enabled','api':self.API_SET_PLUG_LED}
                self.entities.append({'dp_id': self.DP_LED, CONF_PLATFORM: SWITCH_DOMAIN})
            if def_st is not None:
                self.status[self.DP_DEFAULT] = {'state':def_st,'value':[0,self.MEMORY_STATUS],'key':'default','api':self.API_SET_PLUG_DFLTSTAT}
                self.entities.append({'dp_id': self.DP_DEFAULT, CONF_PLATFORM: SWITCH_DOMAIN})

        return 'ok'


    async def async_get_wifi_info(self):
        payload = self.make_payload(self.API_GET_WIFI_INFO)
        try:
            resp = await self.async_make_request(payload)
        except requests.exceptions.ConnectionError:
            return "Request failed, status ConnectionError"

        if not resp.ok:
            return "Request failed, status " + str(resp.status_code)

        r_json = resp.json()
        _LOGGER.debug('wifi info: %s', r_json)
        if not r_json["result"]:
            self.ip = r_json['ip']

        return 'ok'


    async def async_get_plug_info(self):
        payload = self.make_payload(self.API_GET_PLUG_INFO)
        try:
            resp = await self.async_make_request(payload)
        except requests.exceptions.ConnectionError:
            return "Request failed, status ConnectionError"

        if not resp.ok:
            return "Request failed, status " + str(resp.status_code)

        r_json = resp.json()
        if not r_json["result"]:
            # self.mac = r_json['mac']
            self.host_name = r_json['name']
            self.version = r_json['version']

        return 'ok'


    async def async_get_electric(self):
        payload = self.make_payload(self.API_GET_PLUG_ELECTRIC)
        try:
            resp = await self.async_make_request(payload)
        except requests.exceptions.ConnectionError:
            return "Request failed, status ConnectionError"

        if not resp.ok:
            return "Request failed, status " + str(resp.status_code)

        r_json = resp.json()
        if not r_json["result"]:
            scale_factor = 0.001
            vol = r_json['vol']
            curr = r_json['curr']
            power = r_json['power']
            self.status[self.DP_ELECTRIC] = {
                'vol': {'state': vol, 'scaling':scale_factor, CONF_UNIT_OF_MEASUREMENT:'V'}, 
                'curr': {'state': curr, 'scaling': scale_factor, CONF_UNIT_OF_MEASUREMENT:'mA'}, 
                'power': {'state': power, 'scaling': scale_factor, CONF_UNIT_OF_MEASUREMENT:'W'}
            }
            self.entities.append({'dp_id': self.DP_ELECTRIC, CONF_PLATFORM: SENSOR_DOMAIN})

        return 'ok'
    
    async def async_get_plug_sn(self):
        payload = self.make_payload(self.API_GET_SN)
        try:
            resp = await self.async_make_request(payload)
        except requests.exceptions.ConnectionError:
            return "Request failed, status ConnectionError"

        if not resp.ok:
            return "Request failed, status " + str(resp.status_code)

        r_json = resp.json()
        if not r_json["result"]:
            self.sn = r_json['sn']

        return 'ok'

    async def async_get_info(self):
        if not self.ip:
            await self.async_get_wifi_info()
        if self.ip:
            self.local_address = 'http://' + self.ip + ':6767'
            _LOGGER.debug("local address: %s", self.local_address)
            self.address = self.local_address
            self.scan_interval = self.scan_interval/2

        if self.sn[0] == '_':
            await self.async_get_plug_sn()
            
        result = await self.async_get_status()
        _LOGGER.debug("result %s", result)
        if result != 'ok':
            self.address = self.remote_address
            await self.async_get_status()
            self.scan_interval = self.scan_interval*2

        await self.async_get_plug_info()

        _LOGGER.debug("async_get_plug_info")
        if self.model in self.ELECTRIC_MODEL:
            await self.async_get_electric()
        
        _LOGGER.debug("async_get_electric")
        self.req_time = time.time()
        return 'ok'


    def get_time(self):
        return time.strftime('%m%d%H%M')

    def device_key(self, t):
        s = self.sn + self.PLUGIN_SCHEMA + t
        return hashlib.md5(s.encode()).hexdigest()
        



class MyCoordinator(DataUpdateCoordinator):
    """My custom coordinator."""

    def __init__(self, hass, device):
        """Initialize my coordinator."""
        super().__init__(
            hass,
            _LOGGER,
            # Name of the data. For logging purposes.
            name = f"sunlogin_{device.model}_{device.sn}",
            # Polling interval. Will only be polled if there are subscribers.
            update_interval=timedelta(seconds=device.scan_interval),
        )
        self.device = device

    async def _async_update_data(self):
        """Fetch data from API endpoint.

        This is the place to pre-process the data to lookup tables
        so entities can quickly look up their data.
        """
        try:
            # Note: asyncio.TimeoutError and aiohttp.ClientError are already
            # handled by the data update coordinator.
            async with async_timeout.timeout(10):
                # Grab active context variables to limit data required to be fetched from API
                # Note: using context is not required if there is no need or ability to limit
                # data retrieved from API.
                # listening_idx = set(self.async_contexts())
                return await self.device.async_update()
        except Exception as ex:
            # Raising ConfigEntryAuthFailed will cancel future updates
            # and start a config flow with SOURCE_REAUTH (async_step_reauth)
            f"""{ex}"""
        
