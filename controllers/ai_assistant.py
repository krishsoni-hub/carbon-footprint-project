import json
import google.generativeai as genai

# Embedded strict system prompt defining model role and expected schema
SYSTEM_INSTRUCTION = (
    "You are a deterministic parsing module embedded in a Carbon Tracking Application. "
    "Your sole task is to read raw human text inputs describing daily activities and "
    "return a strict, minified JSON object matching this schema exactly without markdown formatting wraps:\n"
    "{\n"
    '  "transport_km": float or 0.0,\n'
    '  "transport_type": "petrol" or "diesel" or "ev" or "none",\n'
    '  "appliance_hours": float or 0.0,\n'
    '  "diet_type": "meat" or "vegetarian" or "balanced"\n'
    "}\n"
    "Analyze patterns contextually. Example: \"Drove my civic 10 kilometers\" translates "
    "to transport_type: \"petrol\", transport_km: 10.0. Do not append conversational "
    "banter, intros, or raw explanations. Output only valid JSON."
)

def extract_metrics_from_chat(user_input_string, api_key_string):
    """
    Parses a user input activity string using Gemini 2.5 Flash and returns structured carbon metrics.

    Args:
        user_input_string (str): User's natural language input of their daily activities.
        api_key_string (str): Google Gemini API key.

    Returns:
        dict: A dictionary containing the parsed metrics or default values upon failure.
    """
    default_fallback = {
        "transport_km": 0.0,
        "transport_type": "none",
        "appliance_hours": 0.0,
        "diet_type": "balanced"
    }

    if not api_key_string or not user_input_string.strip():
        return default_fallback

    try:
        # Configure model client API credentials
        genai.configure(api_key=api_key_string)

        # Initialize the model instance using 'gemini-2.5-flash' with system instruction
        model = genai.GenerativeModel(
            model_name="gemini-2.5-flash",
            system_instruction=SYSTEM_INSTRUCTION
        )

        # Execute content generation with JSON output constraint configuration
        response = model.generate_content(
            user_input_string,
            generation_config={"response_mime_type": "application/json"}
        )

        if not response or not response.text:
            return default_fallback

        # Strip any accidental markdown formatting block wraps
        response_text = response.text.strip()
        if response_text.startswith("```"):
            lines = response_text.splitlines()
            if len(lines) >= 2 and lines[0].startswith("```"):
                response_text = "\n".join(lines[1:-1]).strip()

        # Parse generated string
        parsed_data = json.loads(response_text)

        # Validate exact keys in response structure
        required_keys = ["transport_km", "transport_type", "appliance_hours", "diet_type"]
        if not all(key in parsed_data for key in required_keys):
            return default_fallback

        # Normalize and validate types to prevent application failures
        metrics = {
            "transport_km": float(parsed_data.get("transport_km", 0.0)),
            "transport_type": str(parsed_data.get("transport_type", "none")).strip().lower(),
            "appliance_hours": float(parsed_data.get("appliance_hours", 0.0)),
            "diet_type": str(parsed_data.get("diet_type", "balanced")).strip().lower()
        }

        # Validate property choice constraint criteria
        if metrics["transport_type"] not in ["petrol", "diesel", "ev", "none"]:
            metrics["transport_type"] = "none"

        if metrics["diet_type"] not in ["meat", "vegetarian", "balanced"]:
            metrics["diet_type"] = "balanced"

        return metrics

    except Exception:
        # Cleanly intercept any library configurations, network timeouts, or parsing crashes
        return default_fallback
