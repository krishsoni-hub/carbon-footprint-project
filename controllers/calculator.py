"""Carbon footprint calculator module.

This module provides global conversion factors and logic to calculate daily
carbon footprint values based on transportation, home appliance energy usage,
and diet type parameters.
"""

from typing import Dict, Any

# Global carbon conversion factors (kg CO2)
PETROL_CAR_FACTOR: float = 0.192       # kg CO2 per km
DIESEL_CAR_FACTOR: float = 0.171       # kg CO2 per km
EV_CAR_FACTOR: float = 0.047           # kg CO2 per km

# Grid electricity emission rates
GRID_ELECTRICITY_KWH_FACTOR: float = 0.385  # kg CO2 per kWh
APPLIANCE_ACTIVE_HOUR_FACTOR: float = 0.45  # kg CO2 per active hour (equivalent average appliance state)

# Dietary daily contributions
HIGH_MEAT_DIET_DAILY_FACTOR: float = 3.3    # kg CO2 per day
VEGETARIAN_DIET_DAILY_FACTOR: float = 1.7   # kg CO2 per day


def calculate_footprint(data_dict: Dict[str, Any]) -> Dict[str, float]:
    """Calculate the carbon footprint based on transportation, energy usage, and diet inputs.

    Args:
        data_dict (Dict[str, Any]): A dictionary mapping activity categories to carbon emission parameters.
            Expected keys include:
            - "transport_km" (Union[float, int, str]): Distance traveled.
            - "transport_type" (str): Type of vehicle (e.g., "petrol", "diesel", "ev").
            - "appliance_hours" (Union[float, int, str]): Appliance usage duration in hours.
            - "diet_type" (str): Dietary profile (e.g., "meat", "vegetarian").

    Returns:
        Dict[str, float]: A dictionary containing calculated carbon emissions breakdown:
            - "transport_emissions" (float): Emissions from transport in kg CO2.
            - "energy_emissions" (float): Emissions from appliance energy in kg CO2.
            - "diet_emissions" (float): Emissions from daily diet in kg CO2.
            - "total_emissions" (float): Total cumulative emissions in kg CO2.

    Raises:
        None: Coerces invalid types and values safely into default bounds.
    """
    # Extract properties with safety fallbacks
    try:
        transport_km: float = float(data_dict.get("transport_km", 0.0))
        if transport_km < 0:
            transport_km = 0.0
    except (ValueError, TypeError):
        transport_km = 0.0

    transport_type: str = str(data_dict.get("transport_type", "")).strip().lower()

    try:
        appliance_hours: float = float(data_dict.get("appliance_hours", 0.0))
        if appliance_hours < 0:
            appliance_hours = 0.0
    except (ValueError, TypeError):
        appliance_hours = 0.0

    diet_type: str = str(data_dict.get("diet_type", "")).strip().lower()

    # 1. Transport Emissions Calculation
    if "petrol" in transport_type:
        transport_factor: float = PETROL_CAR_FACTOR
    elif "diesel" in transport_type:
        transport_factor = DIESEL_CAR_FACTOR
    elif "ev" in transport_type or "electric" in transport_type:
        transport_factor = EV_CAR_FACTOR
    else:
        # Defaults to 0 if transport type is not recognized or not standard
        transport_factor = 0.0

    transport_emissions: float = transport_km * transport_factor

    # 2. Energy Emissions Calculation
    # Uses standard appliance active running factor of 0.45 kg per active hour
    energy_emissions: float = appliance_hours * APPLIANCE_ACTIVE_HOUR_FACTOR

    # 3. Dietary Emissions Calculation
    if "high_meat" in diet_type or "meat" in diet_type:
        diet_emissions: float = HIGH_MEAT_DIET_DAILY_FACTOR
    elif "vegetarian" in diet_type or "veg" in diet_type:
        diet_emissions = VEGETARIAN_DIET_DAILY_FACTOR
    else:
        # Defaults to 0 if diet type is not specified or not recognized
        diet_emissions = 0.0

    # 4. Total Cumulative emissions
    total_emissions: float = transport_emissions + energy_emissions + diet_emissions

    return {
        "transport_emissions": round(transport_emissions, 4),
        "energy_emissions": round(energy_emissions, 4),
        "diet_emissions": round(diet_emissions, 4),
        "total_emissions": round(total_emissions, 4)
    }
