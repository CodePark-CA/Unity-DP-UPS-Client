from flask import Flask, render_template, jsonify, request, session, redirect, url_for
from unity_dp import UPSLibrary
import logging
import os

app = Flask(__name__)
app.secret_key = os.urandom(24)


def get_ups_instance():
    """Helper to get UPSLibrary instance from session credentials."""
    host = session.get('ups_host')
    user = session.get('ups_user')
    password = session.get('ups_pass')

    if not host or not user or not password:
        return None

    return UPSLibrary(host, user, password)


@app.route('/')
def index():
    """Render the main dashboard page."""
    if 'ups_host' not in session:
        return redirect(url_for('login'))
    return render_template('index.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    """Handle user login and credential verification."""
    if request.method == 'POST':
        host = request.form.get('host')
        user = request.form.get('user')
        password = request.form.get('password')

        # Basic validation
        if not host.startswith('http'):
            host = 'http://' + host

        # Try to connect/login to verify credentials
        ups_test = UPSLibrary(host, user, password)
        try:
            if ups_test.login():
                session['ups_host'] = host
                session['ups_user'] = user
                session['ups_pass'] = password
                return redirect(url_for('index'))
            else:
                return render_template('login.html', error="Failed to login to UPS. Check credentials.")
        except Exception as e:
            return render_template('login.html', error=f"Connection error: {str(e)}")

    return render_template('login.html')


@app.route('/logout')
def logout():
    """Clear the session and log out the user."""
    session.clear()
    return redirect(url_for('login'))


@app.route('/api/status')
def get_status():
    """API endpoint to retrieve all UPS status data."""
    ups = get_ups_instance()
    if not ups:
        return jsonify({"error": "Not logged in"}), 401

    if not ups.login():
        return jsonify({"error": "Failed to login to UPS"}), 500

    try:
        data = ups.get_all_status()
        return jsonify(data)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/api/update_settings', methods=['POST'])
def update_settings():
    """API endpoint to update UPS settings."""
    ups = get_ups_instance()
    if not ups:
        return jsonify({"error": "Not logged in"}), 401

    if not ups.login():
        return jsonify({"error": "Failed to login to UPS"}), 500

    data = request.json
    try:
        # System Settings
        if 'site_identifier' in data:
            ups.system.settings.site_identifier = data['site_identifier']
        if 'site_equipment_tag' in data:
            ups.system.settings.site_equipment_tag = data['site_equipment_tag']
        if 'system_name' in data:
            ups.system.settings.system_name = data['system_name']
        if 'auto_restart' in data:
            ups.system.settings.auto_restart = bool(data['auto_restart'])
        if 'auto_restart_delay' in data:
            ups.system.settings.auto_restart_delay = int(data['auto_restart_delay'])
        if 'audible_alarm_control' in data:
            ups.system.settings.audible_alarm_control = data['audible_alarm_control']

        # Battery Settings
        if 'low_battery_warning_time' in data:
            ups.battery.settings.low_battery_warning_time = int(data['low_battery_warning_time'])

        return jsonify({"success": True})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 400


@app.route('/api/command', methods=['POST'])
def send_command():
    """API endpoint to send commands to the UPS."""
    ups = get_ups_instance()
    if not ups:
        return jsonify({"error": "Not logged in"}), 401

    if not ups.login():
        return jsonify({"error": "Failed to login to UPS"}), 500

    data = request.json
    cmd = data.get('command')
    delay = int(data.get('delay', 0))

    try:
        # System Commands
        if cmd == 'silence_alarm':
            ups.silence_alarm()
            return jsonify({"success": True, "message": "Alarm silenced"})
        elif cmd == 'abort_command':
            ups.abort()
            return jsonify({"success": True, "message": "Command aborted"})
        elif cmd == 'reset_power_stats':
            ups.reset_power_stats()
            return jsonify({"success": True, "message": "Power statistics reset"})

        # Battery Commands
        elif cmd == 'battery_test':
            ups.battery_test()
            return jsonify({"success": True, "message": "Battery test started"})

        # Output Commands
        elif cmd == 'output_on':
            ups.output_on(delay)
            return jsonify({"success": True, "message": f"Output ON command sent (delay: {delay}s)"})
        elif cmd == 'output_off':
            ups.output_off(delay)
            return jsonify({"success": True, "message": f"Output OFF command sent (delay: {delay}s)"})
        elif cmd == 'output_reboot':
            ups.output_reboot(delay)
            return jsonify({"success": True, "message": f"Output Reboot command sent (delay: {delay}s)"})

        # Agent Commands
        elif cmd == 'restart_card':
            ups.restart_card()
            return jsonify({"success": True, "message": "Agent Card restart command sent"})

        else:
            return jsonify({"error": "Unknown command"}), 400
    except Exception as e:
        return jsonify({"error": str(e)}), 500


if __name__ == '__main__':
    print("Starting UPS Web Monitor...")
    print("Open http://127.0.0.1:5000 in your browser")
    app.run(debug=True, host='0.0.0.0', port=5000)
