#!/usr/bin/env python
# -*- coding: utf-8 -*-

import dbus

from flask import Flask, render_template, jsonify, request

app = Flask(__name__)
bus = dbus.SystemBus()
manager = dbus.Interface(bus.get_object('net.connman', '/'), 'net.connman.Manager')


def get_wifi_services():
    services = []
    for path, props in manager.GetServices():
        if props['Type'] != 'wifi':
            continue

        identifier = path[path.rfind("/") + 1:]
        entry = {'id': identifier, 'strength': int(props['Strength']),
                'name': str(props['Name']), 'state': str(props['State'])}
        services.append(entry)

    return sorted(services, key=lambda k: k['strength'], reverse=True)

@app.route('/ajax/sys_state')
def sys_state():
    return jsonify(state=str(manager.GetProperties()['State']))

@app.route('/ajax/connections')
def connections():
    services = get_wifi_services()
    return render_template('connections.html', services=services)

@app.route('/ajax/forget')
def forget():
    id = request.args.get('id')
    service = dbus.Interface(bus.get_object('net.connman',
            '/net/connman/service/%s' % id), 'net.connman.Service')
    service.Remove()
    return jsonify(ok=True)

@app.route('/ajax/connect')
def connect():
    id = request.args.get('id')
    service = dbus.Interface(bus.get_object('net.connman',
            '/net/connman/service/%s' % id), 'net.connman.Service')
    service.Connect(timeout=60000)
    return jsonify(ok=True)

@app.route('/')
def state():
    return render_template('index.html')


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080, debug=True)

