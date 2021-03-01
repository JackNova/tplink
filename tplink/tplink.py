# -*- coding: utf-8 -*-
"""Main module."""
import base64
import json
import re
import socket
from urllib.parse import urlparse

import requests
from aiohttp.hdrs import (CONTENT_TYPE, COOKIE, REFERER)


class TpLinkClient(object):
    def __init__(self, password, host='192.168.1.1', username=None):
        self.host = host
        self.password = password
        self.username = username
        self.ssl_verify = False
        self.parse_macs = re.compile(
            'MACAddress=([0-9A-F]{2}:[0-9A-F]{2}:[0-9A-F]{2}:' +
            '[0-9A-F]{2}:[0-9A-F]{2}:[0-9A-F]{2})')

        self.parse_names = re.compile('hostName=(.*)')

        self.is_omada_controller = False
        self._detect_omada()

    def _detect_omada(self):
        base_url = urlparse(self.host)
        if not base_url.netloc:
            return
        base_url = base_url.scheme + "://" + base_url.netloc
        requests.packages.urllib3.disable_warnings()
        res = requests.get(base_url, allow_redirects=False, verify=self.ssl_verify)
        if 'TPEAP_SESSIONID' not in res.cookies:
            return
        # This seams to be an Omada controller
        self.is_omada_controller = True

    def _get_connected_devices_omada(self):
        login_path = "/api/user/login?ajax"
        clients_path = "/web/v1/controller?userStore&token="
        current_page_size = 10

        session = requests.Session()
        # Get SessionID
        # host variable should includes scheme and port (if not standard)
        # ie https://192.168.1.2:8043
        res = session.get(self.host, verify=self.ssl_verify)
        # Get actual URL
        actual_location = urlparse(res.history[-1].headers['location'])
        base_url = actual_location.scheme + "://" + actual_location.netloc
        # Login
        login_data = {"method": "login",
                      "params": {"name": self.username,
                                 "password": self.password
                                 }
                      }
        res = session.post(base_url + login_path,
                           data=json.dumps(login_data),
                           verify=self.ssl_verify)
        if res.json().get('msg') != 'Log in successfully.':
            raise Exception("AP didn't respond with JSON. "
                            "Check if credentials are correct")
        # Get token
        token = res.json()['result']['token']
        current_page = 1
        total_rows = current_page_size + 1
        list_of_devices = {}
        while (current_page - 1) * current_page_size <= total_rows:
            clients_data = {"method": "getGridActiveClients",
                            "params": {"sortOrder": "asc",
                                       "currentPage": current_page,
                                       "currentPageSize": current_page_size,
                                       "filters": {"type": "all"}
                                       }
                            }
            res = session.post(base_url + clients_path + token,
                               data=json.dumps(clients_data),
                               verify=self.ssl_verify)
            results = res.json()['result']
            total_rows = results['totalRows']
            for data in results['data']:
                key = data['mac'].replace('-', ':')
                if not data['name']:
                    name = ""
                    try:
                        fqdn = socket.gethostbyaddr(data['ip'])
                        name = fqdn[0].split(".")[0]
                    except socket.herror:
                        name = ""
                    if not name:
                        name = data['mac'].replace("-", "_").lower()
                else:
                    name = data['name']
                list_of_devices[key] = name

            current_page += 1

        return list_of_devices

    def get_connected_devices(self):
        if self.is_omada_controller:
            return self._get_connected_devices_omada()

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
