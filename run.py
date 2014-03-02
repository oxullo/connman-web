#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import dbus

from flask import Flask, render_template, jsonify, request

app = Flask(__name__)
bus = dbus.SystemBus()
manager = dbus.Interface(bus.get_object('net.connman', '/'), 'net.connman.Manager')

CONFIG_BASEDIR = '/var/lib/connman'
WIFI_CONFIG_TEMPLATE = '''[service_%(id)s]
Type = wifi
Name = %(ssid)s
Passphrase = %(passphrase)s
'''

def get_config_path(id):
    return os.path.join(CONFIG_BASEDIR, '%s.config' % id)

def is_config(id):
    return os.path.isfile(get_config_path(id))

def get_wifi_services():
    services = []
    for path, props in manager.GetServices():
        if props['Type'] != 'wifi':
            continue

        id = path[path.rfind("/") + 1:]
        entry = {'id': id, 'strength': int(props['Strength']),
                'name': str(props['Name']), 'state': str(props['State']),
                'is_config': is_config(id)}
        services.append(entry)

    return sorted(services, key=lambda k: k['strength'], reverse=True)

def write_wifi_config(id, ssid, passphrase):
    f = open(get_config_path(id), 'w')
    contents = WIFI_CONFIG_TEMPLATE % locals()
    print 'Writing:', contents
    f.write(contents)
    f.close()

def scan():
    technology = dbus.Interface(bus.get_object('net.connman',
            '/net/connman/technology/wifi'), 'net.connman.Technology')
    technology.Scan()

@app.route('/ajax/sys_state')
def sys_state():
    return jsonify(state=str(manager.GetProperties()['State']))

@app.route('/ajax/connections')
def connections():
    scan()
    services = get_wifi_services()
    print services
    return render_template('connections.html', services=services)

@app.route('/ajax/forget')
def forget():
    id = request.args.get('id')
    if is_config(id):
        os.unlink(get_config_path(id))
    else:
        service = dbus.Interface(bus.get_object('net.connman',
                '/net/connman/service/%s' % id), 'net.connman.Service')
        service.Remove()

    return jsonify(ok=True)

@app.route('/ajax/connect')
def connect():
    id = request.args.get('id')
    passphrase = request.args.get('passphrase')

    if not all((id, passphrase)):
        return jsonify(ok=False)

    services = get_wifi_services()

    wanted_service = None
    for service in services:
        if service['id'] == id:
            wanted_service = service

    if wanted_service:
        write_wifi_config(id, wanted_service['name'], passphrase)

    return jsonify(ok=True)

@app.route('/')
def state():
    return render_template('index.html')


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080, debug=True)

