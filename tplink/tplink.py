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
            'associatedDeviceMACAddress=([0-9A-F]{2}:[0-9A-F]{2}:[0-9A-F]{2}:' +
            '[0-9A-F]{2}:[0-9A-F]{2}:[0-9A-F]{2})')


    def get_connected_devices(self):
        connection_string = self.password
        if self.username is not None:
            connection_string = '{}:{}'.format(self.username, self.password)
        b64_encoded_password = base64.b64encode(
            connection_string.encode('ascii')).decode('ascii')
        cookie = 'Authorization=Basic {}' \
            .format(b64_encoded_password)

        payload = ("[LAN_WLAN_ASSOC_DEV#0,0,0,0,0,0#1,0,0,0,0,0]0,4\r\n"
                "AssociatedDeviceMACAddress\r\n"
                "X_TP_TotalPacketsSent\r\n"
                "X_TP_TotalPacketsReceived\r\n"
                "X_TP_HostName\r\n")

        page = requests.post(
            'http://{}/cgi?6'.format(self.host),
            data=payload,
            headers={
                REFERER: "http://{}/".format(self.host),
                COOKIE: cookie,
                CONTENT_TYPE: "text/plain"
            },
            timeout=10)

        mac_addresses = self.parse_macs.findall(page.text)

        return dict((mac_address, None) for mac_address in mac_addresses)
