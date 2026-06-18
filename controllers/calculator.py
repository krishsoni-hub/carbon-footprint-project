# Global carbon conversion factors (kg CO2)
PETROL_CAR_FACTOR = 0.192       # kg CO2 per km
DIESEL_CAR_FACTOR = 0.171       # kg CO2 per km
EV_CAR_FACTOR = 0.047           # kg CO2 per km

# Grid electricity emission rates
GRID_ELECTRICITY_KWH_FACTOR = 0.385  # kg CO2 per kWh
APPLIANCE_ACTIVE_HOUR_FACTOR = 0.45  # kg CO2 per active hour (equivalent average appliance state)

# Dietary daily contributions
HIGH_MEAT_DIET_DAILY_FACTOR = 3.3    # kg CO2 per day
VEGETARIAN_DIET_DAILY_FACTOR = 1.7   # kg CO2 per day

def calculate_footprint(data_dict):
    """
    Calculate the carbon footprint based on transportation, energy usage, and diet inputs.

    Input schema:
    {
        "transport_km": float,
        "transport_type": str,      # options: 'petrol', 'diesel', 'ev' / 'electric'
        "appliance_hours": float,
        "diet_type": str            # options: 'high_meat', 'vegetarian'
    }

    Returns a breakdown dictionary with total sum included:
    {
        "transport_emissions": float,
        "energy_emissions": float,
        "diet_emissions": float,
        "total_emissions": float
    }
    """
    # Extract properties with safety fallbacks
    transport_km = float(data_dict.get("transport_km", 0.0))
    transport_type = str(data_dict.get("transport_type", "")).strip().lower()
    appliance_hours = float(data_dict.get("appliance_hours", 0.0))
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
