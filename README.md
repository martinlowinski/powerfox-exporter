# Powerfox Exporter

![Docker Pulls](https://img.shields.io/docker/pulls/martinlowinski/powerfox-exporter)
![Python Version](https://img.shields.io/badge/Python-3.12-3776AB.svg)

Service to scrape [powerfox](https://www.powerfox.energy/?utm_source=github&utm_campaign=exporter) metrics and to export them for prometheus.

![Screenshot of the powerfox grafana dashboard](https://grafana.com/api/dashboards/20350/images/15494/image)

## Configuration

Environment variables:

- `POLLING_INTERVAL_SECONDS`, the default is 60
- `EXPORTER_PORT`, the port where `/metrics` is exported, default is 9813
- `LOGLEVEL`, sets the threshold for the logging, default is `INFO`
- `POWERFOX_API_USER` as part of the powerfox credentials
- `POWERFOX_API_PASSWORD` as part of the powerfox credentials
- `POWERFOX_DEVICE`, the ID of the poweropti

## Usage

### Docker Compose

Docker images are automatically build for various architectures and pushed to [Docker Hub](https://hub.docker.com/r/martinlowinski/powerfox-exporter).

```yaml
version: '3.8'

services:
  powerfox-exporter:
    image: martinlowinski/powerfox-exporter:latest
    restart: always
    environment:
      - POWERFOX_API_USER=username
      - POWERFOX_API_PASSWORD=password
      - POWERFOX_DEVICE=123456789
```

This allows prometheus to scrape the metrics via inter-container communication on the default port `9813`.

### Prometheus scrape usage

```yaml
scrape_configs:
  - job_name: 'powerfox-exporter'
    scrape_interval: 60s
    static_configs:
      - targets: ['powerfox-exporter:9813']
```

### Grafana

I have created an example grafana [dashboard](https://grafana.com/grafana/dashboards/20350-powerfox/) for this exporter, feel free to use it.

## Collectors

The prometheus exporter collects the following metrics:

| Name                          | Description                       |
|-------------------------------|-----------------------------------|
| `powerfox_device_consumption` | Device consumption reading in kWh |
| `powerfox_device_feedin`      | Device feedin reading in kWh      |
| `powerfox_device_power`       | Device current power in W         |
| `powerfox_device_outdated`    | Device data is currently outdated |
