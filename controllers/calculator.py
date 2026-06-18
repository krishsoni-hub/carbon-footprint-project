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
    """
    Calculate the carbon footprint based on transportation, energy usage, and diet inputs.

    :param data_dict: A dictionary mapping activity categories to carbon emission parameters.
        Must contain:
        - "transport_km" (float or str)
        - "transport_type" (str)
        - "appliance_hours" (float or str)
        - "diet_type" (str)
    :type data_dict: Dict[str, Any]
    :return: A dictionary of computed emissions breakdown including "transport_emissions",
        "energy_emissions", "diet_emissions", and "total_emissions".
    :rtype: Dict[str, float]
    """
    # Extract properties with safety fallbacks
    try:
        transport_km = float(data_dict.get("transport_km", 0.0))
        if transport_km < 0:
            transport_km = 0.0
    except (ValueError, TypeError):
        transport_km = 0.0

    transport_type = str(data_dict.get("transport_type", "")).strip().lower()

    try:
        appliance_hours = float(data_dict.get("appliance_hours", 0.0))
        if appliance_hours < 0:
            appliance_hours = 0.0
    except (ValueError, TypeError):
        appliance_hours = 0.0

    diet_type = str(data_dict.get("diet_type", "")).strip().lower()

    # 1. Transport Emissions Calculation
    if "petrol" in transport_type:
        transport_factor = PETROL_CAR_FACTOR
    elif "diesel" in transport_type:
        transport_factor = DIESEL_CAR_FACTOR
    elif "ev" in transport_type or "electric" in transport_type:
        transport_factor = EV_CAR_FACTOR
    else:
        # Defaults to 0 if transport type is not recognized or not standard
        transport_factor = 0.0

    transport_emissions = transport_km * transport_factor

    # 2. Energy Emissions Calculation
    # Uses standard appliance active running factor of 0.45 kg per active hour
    energy_emissions = appliance_hours * APPLIANCE_ACTIVE_HOUR_FACTOR

    # 3. Dietary Emissions Calculation
    if "high_meat" in diet_type or "meat" in diet_type:
        diet_emissions = HIGH_MEAT_DIET_DAILY_FACTOR
    elif "vegetarian" in diet_type or "veg" in diet_type:
        diet_emissions = VEGETARIAN_DIET_DAILY_FACTOR
    else:
        # Defaults to 0 if diet type is not specified or not recognized
        diet_emissions = 0.0

    # 4. Total Cumulative emissions
    total_emissions = transport_emissions + energy_emissions + diet_emissions

    return {
        "transport_emissions": round(transport_emissions, 4),
        "energy_emissions": round(energy_emissions, 4),
        "diet_emissions": round(diet_emissions, 4),
        "total_emissions": round(total_emissions, 4)
    }
