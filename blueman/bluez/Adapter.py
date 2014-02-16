from PropertiesBlueZInterface import PropertiesBlueZInterface
from errors import raise_dbus_error, parse_dbus_error
from Device import Device
import dbus


class Adapter(PropertiesBlueZInterface):
    @raise_dbus_error
    def __init__(self, obj_path):
        if self.__class__.get_interface_version()[0] < 5:
            interface = 'org.bluez.Adapter'
        else:
            interface = 'org.bluez.Adapter1'
            proxy = dbus.SystemBus().get_object('org.bluez', '/', follow_name_owner_changes=True)
            self.manager_interface = dbus.Interface(proxy, 'org.freedesktop.DBus.ObjectManager')

        super(Adapter, self).__init__(interface, obj_path)

    @raise_dbus_error
    def find_device(self, address):
        devices = self.list_devices()
        for device in devices:
            if device.get_properties()['Address'] == address:
                return device

    @raise_dbus_error
    def list_devices(self):
        if self.__class__.get_interface_version()[0] < 5:
            devices = self.get_interface().ListDevices()
            return [Device(device) for device in devices]
        else:
            objects = self.manager_interface.GetManagedObjects()
            devices = []
            for path, interfaces in objects.items():
                if 'org.bluez.Device1' in interfaces:
                    devices.append(path)
            return [Device(device) for device in devices]

    @raise_dbus_error
    def create_device(self, address, reply_handler=None, error_handler=None):
        def reply_handler_wrapper(path):
            if not callable(reply_handler):
                return
            reply_handler(Device(path))

        def error_handler_wrapper(exception):
            exception = parse_dbus_error(exception)
            if not callable(error_handler):
                raise exception
            error_handler(exception)

        if reply_handler is None and error_handler is None:
            obj_path = self.get_interface().CreateDevice(address)
            return Device(obj_path)
        else:
            self.get_interface().CreateDevice(
                address, reply_handler=reply_handler_wrapper, error_handler=error_handler_wrapper
            )
            return None

    @raise_dbus_error
    def handle_signal(self, handler, signal, **kwargs):
        if signal in ['DeviceCreated', 'DeviceRemoved', 'DeviceFound']:
            if self.__class__.get_interface_version()[0] < 5:
                self._handle_signal(handler, signal, self.get_interface_name(), self.get_object_path(), **kwargs)
            else:
                if signal == 'DeviceFound':
                    return

                def wrapper(object_path, interfaces):
                    if 'org.bluez.Device1' in interfaces:
                        handler(object_path)

                signal = {
                    'DeviceCreated': 'InterfacesAdded',
                    'DeviceRemoved': 'InterfacesRemoved'
                }[signal]

                self._handle_signal(wrapper, signal, 'org.freedesktop.DBus.ObjectManager', '/', **kwargs)
        else:
            super(Adapter, self).handle_signal(handler, signal, **kwargs)

    @raise_dbus_error
    def start_discovery(self):
        self.get_interface().StartDiscovery()

    @raise_dbus_error
    def stop_discovery(self):
        self.get_interface().StopDiscovery()

    @raise_dbus_error
    def remove_device(self, device):
        self.get_interface().RemoveDevice(device.get_object_path())

    @raise_dbus_error
    def register_agent(self, agent, capability=''):
        # BlueZ 4 only!
        self.get_interface().RegisterAgent(agent.get_object_path(), capability)

    @raise_dbus_error
    def unregister_agent(self, agent):
        # BlueZ 4 only!
        self.get_interface().UnregisterAgent(agent.get_object_path())
