import requests
metadata_url = "http://169.254.169.254/latest/meta-data/"

# Function to fetch instance metadata
def fetch_instance_metadata():
    metadata_url = "http://169.254.169.254/latest/meta-data/"
    try:
        response = requests.get(metadata_url)
        response.raise_for_status()
        return response.text
    except requests.exceptions.RequestException as e:
        print("Error fetching instance metadata:", e)
        return None

# Get instance public DNS name and IP address
metadata = fetch_instance_metadata()
if metadata:
    lines = metadata.split('\n')
    host = requests.get(metadata_url + 'public-hostname').text
    ip = requests.get(metadata_url + 'local-ipv4').text
    print("Public DNS Name:", host)
    print("Local IP Address:", ip)
else:
    # Fallback to static values
    host = 'ec2-54-236-191-88.compute-1.amazonaws.com'
    ip = '127.0.0.1'

# Other static configurations
port = 8080
buffer_size = 1024
cwd = '/'.join(__file__.split("/")[:-1])
