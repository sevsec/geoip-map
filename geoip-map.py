import streamlit as st
import pandas as pd
import requests
import pydeck as pdk
import re

# Regex to capture IP addresses from a file
ip_regex = re.compile('((?:(?:25[0-5]|(?:2[0-4]|1[0-9]|[1-9]|)[0-9])\.){3}(?:25[0-5]|(?:2[0-4]|1[0-9]|[1-9]|)[0-9]))')

# Regex to filter RFC-1918 IPs
rfc1918_ip = re.compile('(?:(?:127\.0\.0\.1)|(?:10\.)|(?:172\.1[6-9]\.)|(?:172\.2[0-9]\.)|(?:172\.3[0-1]\.)|(?:192\.168\.)|(?:169\.254)|(?:0\.0\.0\.0))')

# Fetch IP geolocation from ipinfo.io
def fetch_ipinfo(ip, token):
    if not token:
        st.warning("ipinfo.io requires a valid API token.")
        return None
    url = f"https://ipinfo.io/{ip}?token={token}"
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        data = response.json()
        if 'loc' in data:
            latitude, longitude = map(float, data['loc'].split(','))
            return {
                "ip": ip, "latitude": latitude, "longitude": longitude,
                "city": data.get("city", ""), "region": data.get("region", ""),
                "country": data.get("country", ""), "org": data.get("org", ""),
                "service": "ipinfo.io"
            }
    except requests.exceptions.RequestException as e:
        st.error(f"Error fetching data for {ip} from ipinfo.io: {e}")
    return None


# Fetch IP geolocation from ip-api.com
def fetch_ip_api(ip):
    # No HTTPS for free version
    url = f"http://ip-api.com/json/{ip}"
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        data = response.json()
        if data.get("status") == "success":
            return {
                "ip": ip, "latitude": data.get("lat"), "longitude": data.get("lon"),
                "city": data.get("city", ""), "region": data.get("regionName", ""),
                "country": data.get("country", ""), "org": data.get("org", ""),
                "service": "ip-api.com"
            }
    except requests.exceptions.RequestException as e:
        st.error(f"Error fetching data for {ip} from ip-api.com: {e}")
    return None


# Fetch IP geolocation from ipgeolocation.io
def fetch_ipgeolocation(ip, token):
    if not token:
        st.warning("ipgeolocation.io requires a valid API token.")
        return None
    url = f"https://api.ipgeolocation.io/ipgeo?apiKey={token}&ip={ip}"
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        data = response.json()
        return {
            "ip": ip, "latitude": float(data.get("latitude", 0)), "longitude": float(data.get("longitude", 0)),
            "city": data.get("city", ""), "region": data.get("state_prov", ""),
            "country": data.get("country_name", ""), "org": data.get("organization", ""),
            "service": "ipgeolocation.io"
        }
    except requests.exceptions.RequestException as e:
        st.error(f"Error fetching data for {ip} from ipgeolocation.io: {e}")
    return None


# Unified fetcher function
def fetch_geolocation(ip, service, token):
    fetchers = {
        "ipinfo.io": lambda: fetch_ipinfo(ip, token),
        "ip-api.com": lambda: fetch_ip_api(ip),
        "ipgeolocation.io": lambda: fetch_ipgeolocation(ip, token),
    }
    return fetchers.get(service, lambda: None)()


# Load IP addresses
def load_ip_addresses(uploaded_file):
    try:
        content = uploaded_file.read().decode("utf-8")
        return list(dict.fromkeys(ip for ip in ip_regex.findall(content) if not rfc1918_ip.match(ip)))
    except Exception as e:
        st.error(f"Error loading file: {e}")
        return []


# Fetch user's IP address and geolocation
def fetch_user_ip():
    try:
        response = requests.get("https://api.ipify.org?format=json", timeout=10)
        response.raise_for_status()
        user_ip = response.json().get("ip")
        if user_ip:
            geolocation = fetch_ip_api(user_ip)
            if geolocation:
                return geolocation
    except requests.exceptions.RequestException as e:
        st.error(f"Error fetching user's IP: {e}")
    return None


# Streamlit App
def main():
    st.set_page_config(layout="wide")
    st.sidebar.header("IP Geolocation")

    # Fetch user's IP
    user_location = fetch_user_ip()
    if user_location:
        st.sidebar.write(f"User IP: **{user_location['ip']}**")
    else:
        st.sidebar.warning("(N/A)")

    # Service selection
    service = st.sidebar.selectbox("Geolocation Service:", ["ip-api.com", "ipinfo.io", "ipgeolocation.io"])

    # Input API token
    token = ""
    if service != "ip-api.com":
        token = st.sidebar.text_input(f"API Token for {service}:", type="password")

    # Upload file
    uploaded_file = st.sidebar.file_uploader("Log File", type=["txt", "log"])

    if uploaded_file:
        ip_addresses = load_ip_addresses(uploaded_file)

        if not ip_addresses:
            st.warning("No valid IP addresses found in the file.")
            return

        # Fetch geolocation
        st.info("Fetching geolocation data...")
        data = []
        for ip in ip_addresses:
            result = fetch_geolocation(ip, service, token)
            if result:
                data.append(result)

        if data:
            df = pd.DataFrame(data)

            # Line data to connect user location to other IPs
            line_data = [
                {
                    "start_lat": user_location["latitude"],
                    "start_lon": user_location["longitude"],
                    "end_lat": row["latitude"],
                    "end_lon": row["longitude"]
                }
                for _, row in df.iterrows() if row["org"] != "Your Location"
            ]

            # House icon data for user's location
            icon_data = pd.DataFrame([
                {
                    "latitude": user_location["latitude"],
                    "longitude": user_location["longitude"],
                    "icon": "https://upload.wikimedia.org/wikipedia/commons/e/ec/RedDot.svg"
                }
            ])

            # Create pydeck map with Mapbox tiles
            user_layer = pdk.Layer(
                "ScatterplotLayer",
                data=df,
                get_position=["longitude", "latitude"],
                get_radius=70000,
                get_color=[255, 0, 0, 255],
                pickable=True,
            )

            line_layer = pdk.Layer(
                "LineLayer",
                data=line_data,
                get_source_position=["start_lon", "start_lat"],
                get_target_position=["end_lon", "end_lat"],
                get_color=[0, 150, 255, 150],
                get_width=1,
            )

            icon_layer = pdk.Layer(
                "IconLayer",
                data=icon_data,
                get_position=["longitude", "latitude"],
                get_icon="icon",
                get_size=2,
                pickable=True,
            )

            view_state = pdk.ViewState(
                latitude=df["latitude"].mean(), longitude=df["longitude"].mean(), zoom=2
            )

            st.pydeck_chart(pdk.Deck(
                map_style="mapbox://styles/mapbox/streets-v11",
                initial_view_state=view_state,
                layers=[user_layer, line_layer, icon_layer],
                tooltip={"html": "<b>IP:</b> {ip}<br><b>City:</b> {city}, {region}<br><b>Country:</b> {country}"}
                ),
            use_container_width=True,
            # Statically defined for now
            height=1080
            )
        else:
            st.warning("No geolocation data found. Please check your API token or input file.")

if __name__ == "__main__":
    main()
