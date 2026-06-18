def get_contextual_advice(emissions_breakdown: dict):
    """
    Generates dynamic contextual recommendations based on calculated carbon emissions.

    Args:
        emissions_breakdown (dict): emissions calculation results containing keys:
            - transport_emissions (float)
            - energy_emissions (float)
            - diet_emissions (float)
            - total_emissions (float)

    Returns:
        dict: containing:
            - status_alert (str): summary statement of current carbon performance.
            - tips_list (list of str): list of actionable recommendation points.
    """
    transport = float(emissions_breakdown.get("transport_emissions", 0.0))
    energy = float(emissions_breakdown.get("energy_emissions", 0.0))
    diet = float(emissions_breakdown.get("diet_emissions", 0.0))
    total = float(emissions_breakdown.get("total_emissions", 0.0))

    tips_list = []
    
    # 1. Transportation footprint threshold validation (> 15 kg CO2)
    if transport > 15.0:
        tips_list.append(
            "Your transit emissions are elevated. To reduce your impact, try switching to public "
            "transportation, walking/cycling for short trips, carpooling, or considering an electric vehicle (EV)."
        )

    # 2. Home utility energy footprint threshold validation (> 10 kg CO2)
    if energy > 10.0:
        tips_list.append(
            "Your utility energy emissions are high. Consider adjusting heating/cooling thermostats, "
            "scheduling appliance runtimes during off-peak hours, or replacing older systems with energy-efficient setups."
        )

    # 3. Dietary emissions baseline validation (High Meat Daily impact > 3.0 kg CO2)
    if diet > 3.0:
        tips_list.append(
            "Your daily diet emissions are high. Swapping high-meat meals for plant-based, "
            "vegetarian, or locally sourced food alternatives is a simple way to lower emissions."
        )

    # Formulate contextual header alert text
    if len(tips_list) > 0:
        status_alert = (
            f"Your daily carbon footprint is elevated at {total:.2f} kg CO2. "
            "We have compiled localized actionable insights to help you decrease emissions."
        )
    elif total > 0.0:
        status_alert = (
            f"Your daily carbon footprint is at a moderate level of {total:.2f} kg CO2. "
            "Check out these small adjustments to improve further!"
        )
        tips_list.append("Keep logging your activities to trace your progression towards net-zero emissions.")
    else:
        status_alert = "Your logged activities indicate zero carbon emissions. Great job maintaining an eco-friendly profile!"
        tips_list.append("Continue monitoring your daily activities to lock in sustainable practices.")

    return {
        "status_alert": status_alert,
        "tips_list": tips_list
    }
