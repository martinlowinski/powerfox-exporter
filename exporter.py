"""powerfox exporter"""

import os
import time
import logging
import requests
from prometheus_client import start_http_server, Gauge
from requests.auth import HTTPBasicAuth
from dateutil import parser
from datetime import datetime


POWERFOX_API_ROOT = "https://backend.powerfox.energy"
POWERFOX_API_VERSION = "2.0"
POWERFOX_API_BOX_CURRENT = POWERFOX_API_ROOT + \
    "/api/{version}/my/{device_id}/current/"


class AppMetrics:
    """
    Representation of Prometheus metrics and loop to fetch and transform
    application metrics into Prometheus metrics.
    """

    def __init__(
            self,
            polling_interval_seconds=5,
            powerfox_user=None,
            powerfox_password=None,
            powerfox_device=None):
        logging.info("Initializing...")

        if not powerfox_device:
            logging.error(
                "No device specified. Please use the environment variable POWERFOX_DEVICE to set the serial.")
            return

        self.polling_interval_seconds = polling_interval_seconds
        self.powerfox_user = powerfox_user
        self.powerfox_password = powerfox_password
        self.powerfox_device = powerfox_device

        # Prometheus metrics to collect
        self.device_consumption = Gauge(
            "powerfox_device_consumption",
            "Device consumption reading in kWh",
            ["device_id"])
        self.device_feedin = Gauge(
            "powerfox_device_feedin",
            "Device feedin reading in kWh",
            ["device_id"])
        self.device_power = Gauge(
            "powerfox_device_power",
            "Device current power in W",
            ["device_id"])
        self.device_outdated = Gauge(
            "powerfox_device_outdated",
            "Device data is currently outdated",
            ["device_id"])

    def build_url(self, url: str, **kwargs) -> str:
        # Build the request URL with API version and additional args
        return url.format(version=POWERFOX_API_VERSION, **kwargs)

    def run_metrics_loop(self):
        """Metrics fetching loop"""

        logging.info("Metrics loop started.")
        while True:
            self.fetch()
            time.sleep(self.polling_interval_seconds)

    def fetch(self):
        """
        Get metrics from application and refresh Prometheus metrics with
        new values.
        """
        url = self.build_url(
            POWERFOX_API_BOX_CURRENT,
            device_id=self.powerfox_device)

        auth = HTTPBasicAuth(
            self.powerfox_user,
            self.powerfox_password
        )
        try:
            r = requests.get(url, auth=auth)
            r.raise_for_status()
        except requests.exceptions.HTTPError as errh:
            logging.error("HTTP error: %s", errh)
            if r.status_code == requests.codes.too_many_requests:
                logging.warning("Consider increasing the polling interval.")
            return None
        except requests.exceptions.RequestException as err:
            logging.error("Request failed: %s", err)
            return None

        current = r.json()

        self.device_consumption.labels(
            self.powerfox_device
        ).set(current['A_Plus'] / 1000)

        self.device_feedin.labels(
            self.powerfox_device
        ).set(current['A_Minus'] / 1000)

        self.device_power.labels(
            self.powerfox_device
        ).set(current['Watt'])

        self.device_outdated.labels(
            self.powerfox_device
        ).set(int(current['Outdated']))


def main():
    exporter_port = int(os.getenv("EXPORTER_PORT", "9813"))
    # Attention: The powerfox API is rate limited
    polling_interval_seconds = int(os.getenv("POLLING_INTERVAL_SECONDS", "60"))
    powerfox_user = os.getenv("POWERFOX_API_USER", "")
    powerfox_password = os.getenv("POWERFOX_API_PASSWORD", "")
    powerfox_device = os.getenv("POWERFOX_DEVICE", "")
    loglevel = os.environ.get('LOGLEVEL', 'INFO').upper()
    logging.basicConfig(level=loglevel, format='%(asctime)s - %(levelname)s - %(message)s')

    app_metrics = AppMetrics(
        polling_interval_seconds=polling_interval_seconds,
        powerfox_user=powerfox_user,
        powerfox_password=powerfox_password,
        powerfox_device=powerfox_device,
    )
    start_http_server(exporter_port)
    app_metrics.run_metrics_loop()


if __name__ == "__main__":
    main()
