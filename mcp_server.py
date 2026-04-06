"""
Standalone MCP (Model Context Protocol) Server.
This server explicitly exposes the Midterm API tools to any connected MCP Client.
"""

from mcp.server.fastmcp import FastMCP
import requests
import config

# Create the official MCP Server instance
mcp = FastMCP("AirlineMCPServer")

_JWT_TOKEN = None

def get_auth_token(force_refresh: bool = False) -> str:
    """Authenticates the admin user and retrieves a JWT Bearer token.

    If force_refresh is True, ignores the cached token and fetches a new one.
    This is used to recover from expired tokens (401 Unauthorized responses).
    """
    global _JWT_TOKEN
    if _JWT_TOKEN is None or force_refresh:
        auth_payload = {
            "username": config.AUTH_USERNAME,
            "password": config.AUTH_PASSWORD
        }
        response = requests.post(f"{config.BASE_API_URL}/auth/login", json=auth_payload)
        if response.status_code == 200:
            _JWT_TOKEN = response.json().get("token") or response.json().get("Token")
        else:
            raise PermissionError(f"Auth failed. Status: {response.status_code}")
    return _JWT_TOKEN

@mcp.tool()
def query_available_flights(
    airport_from: str,
    airport_to: str,
    date_from: str,
    number_of_people: int = 1
) -> str:
    """
    Queries the airline system to find available flights between two airports on a specific date.
    Input parameters should be 3-letter airport codes (e.g., 'IST', 'FRA', 'ESB').
    The date_from must be in 'YYYY-MM-DD' format.
    number_of_people is the number of passengers (default: 1).
    """
    params = {
        "airportFrom": airport_from,
        "airportTo": airport_to,
        "dateFrom": date_from,
        "dateTo": date_from,
        "numberOfPeople": number_of_people,
        "isRoundTrip": False
    }
    try:
        response = requests.get(f"{config.BASE_API_URL}/flight", params=params)
        if response.status_code == 200:
            flights = response.json()
            if not flights:
                return "No flights found for the given route and date."
            return str(flights)
        return f"Failed to query flights. API returned status code: {response.status_code}"
    except Exception as e:
        return f"Network error occurred while querying flights: {str(e)}"

@mcp.tool()
def book_flight_ticket(flight_number: str, date: str, passenger_name: str) -> str:
    """
    Books a flight ticket for a passenger on a specific flight.
    This operation reduces the flight capacity by 1.
    """
    try:
        token = get_auth_token()
        headers = {"Authorization": f"Bearer {token}"}
        payload = {
            "flightNumber": flight_number,
            "date": date,
            "passengerName": passenger_name
        }
        response = requests.post(f"{config.BASE_API_URL}/ticket/buy", json=payload, headers=headers)

        # If token expired, refresh once and retry
        if response.status_code == 401:
            token = get_auth_token(force_refresh=True)
            headers = {"Authorization": f"Bearer {token}"}
            response = requests.post(f"{config.BASE_API_URL}/ticket/buy", json=payload, headers=headers)

        if response.status_code in [200, 201]:
            return f"Success! Ticket booked. Details: {response.json()}"
        return f"Failed to book ticket. Reason: {response.text}"
    except Exception as e:
        return f"Error booking ticket: {str(e)}"

@mcp.tool()
def check_in_passenger(flight_number: str, date: str, passenger_name: str) -> str:
    """
    Performs the check-in process for a passenger.
    Requires the flight_number (e.g., TK9999), the date of the flight (YYYY-MM-DD), and the passenger_name.
    """
    try:
        token = get_auth_token()
        headers = {"Authorization": f"Bearer {token}"}
        payload = {
            "flightNumber": flight_number.strip(),
            "date": date.strip(),
            "passengerName": passenger_name.strip()
        }
        response = requests.post(f"{config.BASE_API_URL}/ticket/checkin", json=payload, headers=headers)

        # If token expired, refresh once and retry
        if response.status_code == 401:
            token = get_auth_token(force_refresh=True)
            headers = {"Authorization": f"Bearer {token}"}
            response = requests.post(f"{config.BASE_API_URL}/ticket/checkin", json=payload, headers=headers)

        if response.status_code in [200, 201]:
            return f"Check-in successful. Details: {response.json()}"
        return f"Check-in failed. API Status: {response.status_code}. Reason: {response.text}"
    except Exception as e:
        return f"Error during check-in: {str(e)}"

if __name__ == "__main__":
    # Start the server using standard I/O (the standard local communication protocol for MCP)
    mcp.run()
