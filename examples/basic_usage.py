from unity_dp import UPSLibrary

if __name__ == "__main__":
    ups = UPSLibrary("http://192.168.1.100", "admin", "password")
    print(f"Firmware: {ups.system.firmware_version}")
    print(f"Battery: {ups.battery.charge}%")
    ups.system.site_identifier = "Main Rack"