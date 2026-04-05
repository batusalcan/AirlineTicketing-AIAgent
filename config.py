"""
Configuration module for the AI Agent.
Stores constant variables, credentials, and endpoint URLs.
"""

# The correct Ocelot API Gateway URL exposing the Midterm APIs
BASE_API_URL = "https://batu-airline-gateway-final-d0hbhnc6c8fadgee.italynorth-01.azurewebsites.net/gateway/v1"

# Hardcoded authentication credentials as per assignment requirements
AUTH_USERNAME = "admin"
AUTH_PASSWORD = "admin123"

# Local LLM Configuration (Strategy Pattern context)
LLM_MODEL_NAME = "llama3.1"