# Map IP to Geolocation
Allows users to visualize the geographical locations of IP addresses using pre-defined GeoIP services.

## Features
- Supported IP geolocation services: `ipinfo.io`, `ip-api.com`, and `ipgeolocation.io`
- Parses any file for IPs; ideal for log files
- Automatically fetches IP location data and updates a global map at user-specified intervals (5s - 5m)
- Interactive map with details on IP, city, region, and organization

## Installation
Install the required dependencies:
```bash
pip install streamlit pandas requests pydeck
```

## Usage
Run the application using Streamlit:
```bash
streamlit run geoip-map.py
```

## File Format
Any file that contains IP addresses; the application uses regex to pull all IP addresses. If an address has already been processed, it will be ignored. RFC 1918 addresses are also ignored, but some other non-publicly routable addresses are not.

## API Keys
- **ipinfo.io** requires an API key
- **ipgeolocation.io** requires an API key
- **ip-api.com** does not require any API key

## Configuration
- Choose the geolocation service from the dropdown.
- Enter the API token if required.
- Set the refresh interval to determine update frequency.

## Output
- A table displaying IP address geolocation data.
- A global map highlighting the locations of the IP addresses.

- Output:
A map with points indicating the geographical location of the IP addresses.

## TODO
- Config file that allows users to specify GeoIP services
- Provide continuous monitoring/real-time updates

## License
GNU GENERAL PUBLIC LICENSE 3.0
