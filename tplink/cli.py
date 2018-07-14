# -*- coding: utf-8 -*-
"""Console script for tplink."""
import json
import sys

import click

from tplink import tplink


@click.command()
@click.option('--host', default="192.168.1.1", help='Router ip address')
@click.argument(
    'password')
@click.option(
    '--username', default=None, help='The administrator account username')
def main(host, password, username):
    """Console script for tplink."""
    client = tplink.TpLinkClient(password)
    devices = client.get_connected_devices()
    click.echo(json.dumps(devices, indent=4))
    return 0


if __name__ == "__main__":
    sys.exit(main())  # pragma: no cover
