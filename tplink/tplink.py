# -*- coding: utf-8 -*-
"""Main module."""
import base64
import re

import requests
from aiohttp.hdrs import (CONTENT_TYPE, COOKIE, REFERER)


class TpLinkClient(object):
    def __init__(self, password, host='192.168.1.1', username=None):
        self.host = host
        self.password = password
        self.username = username
        self.parse_macs = re.compile(
            'MACAddress=([0-9A-F]{2}:[0-9A-F]{2}:[0-9A-F]{2}:' +
            '[0-9A-F]{2}:[0-9A-F]{2}:[0-9A-F]{2})')

        self.parse_names = re.compile('hostName=(.*)')

    def get_connected_devices(self):
        connection_string = self.password
        if self.username is not None:
            connection_string = '{}:{}'.format(self.username, self.password)
        b64_encoded_password = base64.b64encode(
            connection_string.encode('ascii')).decode('ascii')
        cookie = 'Authorization=Basic {}' \
            .format(b64_encoded_password)

        payload = "[LAN_HOST_ENTRY#0,0,0,0,0,0#0,0,0,0,0,0]0,0\r\n"
        page = requests.post(
            'http://{}/cgi?5'.format(self.host),
            data=payload,
            headers={
                REFERER: "http://{}/".format(self.host),
                COOKIE: cookie,
                CONTENT_TYPE: "text/plain"
            },
            timeout=10)

        mac_addresses = self.parse_macs.findall(page.text)
        host_names = self.parse_names.findall(page.text)

        return dict(zip(mac_addresses, host_names))
