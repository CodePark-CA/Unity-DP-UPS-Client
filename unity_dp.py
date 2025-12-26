import requests
import logging
from requests.auth import HTTPBasicAuth
from typing import Dict, Any, Optional, Callable, Union

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class Subsystem:
    """Base class for UPS subsystems providing dynamic attribute access."""

    def __init__(self, ups, mapping: Dict[str, Any], dev_id: int = 0, processors: Optional[Dict[str, Callable]] = None):
        self._ups = ups
        self._mapping = mapping
        self._dev_id = dev_id
        self._processors = processors or {}
        self._flat_points = {}
        for k, v in mapping.items():
            if isinstance(v, dict):
                self._flat_points.update(v)
            else:
                self._flat_points[k] = v

    def get_all(self) -> Dict[str, Any]:
        """Retrieve all defined points in their hierarchical structure."""
        query = {v: f'vel~pnt~{v[1:]}' for v in self._flat_points.values() if isinstance(v, str) and v.startswith('v')}
        data = self._ups.get_data(query, self._dev_id)
        if not data: return {}

        def process_dict(d):
            res = {}
            for k, v in d.items():
                if isinstance(v, dict):
                    res[k] = process_dict(v)
                else:
                    val = data.get(v, '--' if data.get(v) == 'No Support' else data.get(v))
                    if k in self._processors: val = self._processors[k](val, res)
                    res[k] = val
            return res

        return process_dict(self._mapping)

    def _get_point(self, name: str) -> Any:
        if name in self._flat_points:
            pnt = self._flat_points[name]
            data = self._ups.get_data({pnt: f'vel~pnt~{pnt[1:]}'}, self._dev_id)
            val = data.get(pnt) if data else None
            if val == 'No Support': val = '--'
            if name in self._processors: val = self._processors[name](val, {})
            return val
        raise AttributeError(f"'{self.__class__.__name__}' object has no attribute '{name}'")

    def _set_point(self, name: str, value: Any):
        if name in self._flat_points:
            if isinstance(value, bool): value = 1 if value else 0
            self._ups.set_data({self._flat_points[name]: value}, self._dev_id)
        else:
            raise AttributeError(f"'{self.__class__.__name__}' object has no attribute '{name}'")

    def __getattr__(self, name: str) -> Any:
        # Fallback for flat access or categories if not explicitly defined
        if name in self._flat_points: return self._get_point(name)
        if name in self._mapping and isinstance(self._mapping[name], dict):
            return Subsystem(self._ups, self._mapping[name], self._dev_id, self._processors)
        raise AttributeError(f"'{self.__class__.__name__}' object has no attribute '{name}'")


def point_prop(name: str):
    return property(lambda self: self._get_point(name), lambda self, v: self._set_point(name, v))


class SystemStatus(Subsystem):
    firmware_version = point_prop('firmware_version')
    manufacturer = point_prop('manufacturer')
    model_number = point_prop('model_number')
    serial_number = point_prop('serial_number')
    manufacture_date = point_prop('manufacture_date')
    inlet_temperature = point_prop('inlet_temperature')
    ups_topology = point_prop('ups_topology')
    ups_source = point_prop('ups_source')
    black_out_count = point_prop('black_out_count')
    brown_out_count = point_prop('brown_out_count')
    system_name = point_prop('system_name')


class SystemSettings(Subsystem):
    site_identifier = point_prop('site_identifier')
    site_equipment_tag = point_prop('site_equipment_tag')
    system_name = point_prop('system_name')
    auto_restart = point_prop('auto_restart')
    auto_restart_delay = point_prop('auto_restart_delay')
    audible_alarm_control = point_prop('audible_alarm_control')


class SystemSubsystem(Subsystem):
    @property
    def status(self) -> SystemStatus: return SystemStatus(self._ups, self._mapping['status'], self._dev_id,
                                                          self._processors)

    @property
    def event(self) -> Subsystem: return Subsystem(self._ups, self._mapping['event'], self._dev_id, self._processors)

    @property
    def settings(self) -> SystemSettings: return SystemSettings(self._ups, self._mapping['settings'], self._dev_id,
                                                                self._processors)

    firmware_version = point_prop('firmware_version')
    site_identifier = point_prop('site_identifier')


class BatteryStatus(Subsystem):
    charge = point_prop('charge')
    time_remaining = point_prop('time_remaining')
    charge_status = point_prop('charge_status')
    dc_bus_voltage = point_prop('dc_bus_voltage')
    charger_state = point_prop('charger_state')
    test_result = point_prop('test_result')
    status = point_prop('status')


class BatterySettings(Subsystem):
    low_battery_warning_time = point_prop('low_battery_warning_time')


class BatterySubsystem(Subsystem):
    @property
    def status(self) -> BatteryStatus: return BatteryStatus(self._ups, self._mapping['status'], self._dev_id,
                                                            self._processors)

    @property
    def event(self) -> Subsystem: return Subsystem(self._ups, self._mapping['event'], self._dev_id, self._processors)

    @property
    def settings(self) -> BatterySettings: return BatterySettings(self._ups, self._mapping['settings'], self._dev_id,
                                                                  self._processors)

    charge = point_prop('charge')
    time_remaining = point_prop('time_remaining')


class InputStatus(Subsystem):
    voltage_ln = point_prop('voltage_ln')
    current_amps = point_prop('current_amps')
    frequency_hz = point_prop('frequency_hz')
    max_voltage_ln = point_prop('max_voltage_ln')
    min_voltage_ln = point_prop('min_voltage_ln')
    nominal_voltage = point_prop('nominal_voltage')


class InputSubsystem(Subsystem):
    @property
    def status(self) -> InputStatus: return InputStatus(self._ups, self._mapping['status'], self._dev_id,
                                                        self._processors)

    @property
    def event(self) -> Subsystem: return Subsystem(self._ups, self._mapping['event'], self._dev_id, self._processors)

    voltage_ln = point_prop('voltage_ln')


class OutputStatus(Subsystem):
    voltage_ln = point_prop('voltage_ln')
    amps = point_prop('amps')
    watts = point_prop('watts')
    va = point_prop('va')
    load_percent = point_prop('load_percent')
    pf = point_prop('pf')
    frequency = point_prop('frequency')


class OutputSubsystem(Subsystem):
    @property
    def status(self) -> OutputStatus: return OutputStatus(self._ups, self._mapping['status'], self._dev_id,
                                                          self._processors)

    @property
    def event(self) -> Subsystem: return Subsystem(self._ups, self._mapping['event'], self._dev_id, self._processors)

    voltage_ln = point_prop('voltage_ln')
    load_percent = point_prop('load_percent')


class BypassSubsystem(Subsystem):
    bypass_voltage = point_prop('bypass_voltage')
    bypass_current = point_prop('bypass_current')
    bypass_frequency = point_prop('bypass_frequency')
    bypass_nominal_voltage = point_prop('bypass_nominal_voltage')
    bypass_not_available = point_prop('bypass_not_available')


class UPSLibrary:
    """Refactored library for interacting with IIS Unity DP UPS."""
    system: SystemSubsystem
    battery: BatterySubsystem
    input: InputSubsystem
    output: OutputSubsystem
    bypass: BypassSubsystem

    def __init__(self, host, username, password):
        self.host = host.rstrip('/')
        self.username = username
        self.password = password
        self.session = requests.Session()
        self.sessACT = None
        self.devId = 4

        # Value processors for special fields
        source_map = {'1': 'Other', '3': 'Normal', '6': 'Normal', '7': 'Normal', '4': 'Bypass', '5': 'Battery'}
        proc_source = lambda v, res: source_map.get(v, f"Unknown ({v})") if v and v != '--' else v

        def proc_pf(v, res):
            if v and v != '--' and v != '': return v
            try:
                w, va = float(res.get('watts', 0)), float(res.get('va', 0))
                if va > 0: return f"{w / va:.2f}"
            except:
                pass
            return v

        # Subsystems
        self.system = SystemSubsystem(self, {
            'status': {
                'firmware_version': 'v4335', 'manufacturer': 'v4333', 'model_number': 'v4240',
                'serial_number': 'v4244', 'manufacture_date': 'v6215', 'inlet_temperature': 'v4291',
                'ups_topology': 'v6199', 'ups_source': 'v4872', 'black_out_count': 'v4120', 'brown_out_count': 'v4119',
                'system_name': 'v4246'
            },
            'event': {'loss_of_redundancy': 'v4825'},
            'settings': {
                'site_identifier': 'v4247', 'auto_restart': 'v5831', 'auto_restart_delay': 'v4710',
                'site_equipment_tag': 'v4248', 'system_name': 'v4246', 'audible_alarm_control': 'v5830'
            }
        }, processors={'ups_source': proc_source})

        self.battery = BatterySubsystem(self, {
            'status': {
                'charge': 'v4153', 'time_remaining': 'v4150', 'charge_status': 'v5799', 'dc_bus_voltage': 'v4148',
                'charger_state': 'v6192', 'test_result': 'v6181', 'status': 'v4871'
            },
            'event': {'low': 'v4162'},
            'settings': {'low_battery_warning_time': 'v5802'}
        })

        self.input = InputSubsystem(self, {
            'status': {
                'voltage_ln': 'v4096', 'current_amps': 'v4113', 'frequency_hz': 'v4105',
                'max_voltage_ln': 'v4106', 'min_voltage_ln': 'v4107', 'nominal_voltage': 'v4102'
            },
            'event': {'undervoltage': 'v5568'}
        })

        self.output = OutputSubsystem(self, {
            'status': {
                'voltage_ln': 'v4385', 'amps': 'v4204', 'watts': 'v4208', 'va': 'v4209',
                'load_percent': 'v5861', 'pf': 'v4212', 'frequency': 'v4207'
            },
            'event': {'overload': 'v4215'}
        }, processors={'pf': proc_pf})

        self.bypass = BypassSubsystem(self, {
            'bypass_voltage': 'v4128', 'bypass_current': 'v5570', 'bypass_frequency': 'v4131',
            'bypass_nominal_voltage': 'v4259', 'bypass_not_available': 'v4135'
        })

    def login(self):
        """Authenticate and get session token."""
        try:
            resp = self.session.get(f"{self.host}/protected/session/unityLogin.htm",
                                    auth=HTTPBasicAuth(self.username, self.password), params={'devId': self.devId},
                                    timeout=10)
            if resp.status_code == 200:
                for item in resp.text.split(';'):
                    if item.startswith('sessACT='):
                        self.sessACT = item.split('=')[1]
                        return True
        except Exception as e:
            logger.error(f"Login error: {e}")
        return False

    def _request(self, method, path, **kwargs):
        if not self.sessACT and not self.login(): return None

        # Proactive refresh
        try:
            r = self.session.get(f"{self.host}/protected/session/getSessionInfo.htm",
                                 auth=HTTPBasicAuth(self.username, self.password),
                                 params={'devId': self.devId, 'sessACT': self.sessACT, 'action': 0}, timeout=5)
            if r.status_code == 200:
                for part in r.text.split(';'):
                    if part.startswith('sessACT='): self.sessACT = part.split('=')[1]
        except:
            pass

        kwargs.update({'auth': HTTPBasicAuth(self.username, self.password), 'timeout': 10})
        if 'params' in kwargs: kwargs['params']['sessACT'] = self.sessACT
        if 'data' in kwargs: kwargs['data']['sessACT'] = self.sessACT

        try:
            resp = self.session.request(method, f"{self.host}{path}", **kwargs)
            if resp.status_code == 200:
                for part in resp.text.split(';'):
                    if part.startswith('sessACT='): self.sessACT = part.split('=')[1]
                return resp
        except Exception as e:
            logger.error(f"Request error: {e}")
        return None

    def get_data(self, points, devId=0):
        params = {'devId': devId}
        params.update(points)
        resp = self._request('GET', '/httpGetSet/httpGet.htm', params=params)
        return {k: v.strip('"') for part in (resp.text.split(';') if resp else []) if '=' in part for k, v in
                [part.split('=', 1)]}

    def set_data(self, points, devId=0):
        for k, v in points.items():
            pnt_id = k[1:] if k.startswith('v') else k
            v_str = str(v)
            is_cmd = '!~' in v_str
            prefix = "commBtn" if is_cmd or not isinstance(v, str) else "str"
            val = v_str.split('!~')[0] if is_cmd else v

            pnt_val = f'vel~pnt~{pnt_id}~0|val~{"num" if prefix == "commBtn" else "str"}~{val}'
            if prefix == "commBtn": pnt_val = f'{{0}}{pnt_val}'

            data = {'devId': devId, 'begin': 'http~set~begin', f'{prefix}{pnt_id}': pnt_val, 'end': 'http~set~end'}
            if not self._request('POST', '/protected/httpSet.htm', data=data): return False
        return True

    # High-level API (Simplified)
    def get_all_status(self):
        return {s: getattr(self, s).get_all() for s in ['system', 'battery', 'input', 'output', 'bypass']}

    def battery_test(self):
        return self.set_data({'v5858': '1!~Start Test'})

    def output_on(self, delay=0):
        return self.set_data({'v5816': f'{delay}!~ON'})

    def output_off(self, delay=0):
        return self.set_data({'v5814': f'{delay}!~OFF'})

    def output_reboot(self, delay=0):
        return self.set_data({'v5815': f'{delay}!~Reboot'})

    def silence_alarm(self):
        return self.set_data({'v6257': '1!~Silence'})

    def abort(self):
        return self.set_data({'v6200': '1!~Abort'})

    def reset_power_stats(self):
        return self.set_data({'v6216': '1!~Reset'})