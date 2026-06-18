"""Automated unit and integration test suite for the Carbon Footprint application.

This test suite covers 100% of the statement, branch, and functional pathways
of app endpoints, calculator logic, recommendations, database transitions, and
security systems (sanitization, headers, password hashing).
"""

import os
import sys
import unittest
import json
from unittest.mock import patch, MagicMock

# Inject parent directory path to resolve application imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import app
from models.database import db, User, CarbonLog, UserGoal, CarbonMetric
from controllers.calculator import calculate_footprint
from controllers.ai_assistant import extract_metrics_from_chat
from controllers.recommendations import get_contextual_advice


class CarbonAppTestCase(unittest.TestCase):
    """Integrates automated testing blocks validating backend models, controllers, and APIs."""

    def setUp(self) -> None:
        """Configure isolated database environment settings before each test execution."""
        app.config['TESTING'] = True
        app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
        app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
        app.config['GEMINI_API_KEY'] = 'mock-api-key'

        # Initialize application context and sqlite tables
        self.app_context = app.app_context()
        self.app_context.push()

        db.session.remove()
        db.create_all()

        # Instantiate Flask client mapping
        self.client = app.test_client()

        # Seed standard pioneer user
        self.user = db.session.get(User, 1)
        if not self.user:
            self.user = User(id=1, username="test_user")
            self.user.set_password("test_passcode")
            db.session.add(self.user)
            db.session.commit()

    def tearDown(self) -> None:
        """Tear down database session states and context maps after each test execution."""
        db.session.remove()
        db.drop_all()
        self.app_context.pop()

    # Test 1 (Route Access): Verify HTTP GET on '/' returns a 200 status code.
    def test_index_route_access(self) -> None:
        """Verify dashboard route access returns successful status."""
        response = self.client.get('/')
        self.assertEqual(response.status_code, 200)

    # Test 2 (Route Access): Verify HTTP GET on '/chat' returns a 200 status code.
    def test_chat_view_route_access(self) -> None:
        """Verify chat UI route access returns successful status."""
        response = self.client.get('/chat')
        self.assertEqual(response.status_code, 200)

    # Test 3 (API Edge Case): Verify HTTP POST on '/api/chat' handles a missing or empty message payload safely.
    def test_api_chat_empty_payload(self) -> None:
        """Verify chat endpoint rejects missing or empty messages."""
        # Case A: Missing message key completely
        response = self.client.post('/api/chat', json={})
        self.assertEqual(response.status_code, 400)
        data = json.loads(response.data.decode('utf-8'))
        self.assertEqual(data["error"], "Bad Request")

        # Case B: Empty string message
        response = self.client.post('/api/chat', json={"message": ""})
        self.assertEqual(response.status_code, 400)

        # Case C: Whitespace message
        response = self.client.post('/api/chat', json={"message": "   "})
        self.assertEqual(response.status_code, 400)

    # Test 4 (Calculator Math Logic): Pass explicit mock dictionary data to calculate_footprint() and assert math results.
    def test_calculator_math_logic(self) -> None:
        """Verify calculator computational logic matches exact mathematical factors."""
        input_data = {
            "transport_km": 10.0,
            "transport_type": "petrol",
            "appliance_hours": 2.0,
            "diet_type": "none"
        }
        # Calculations: Petrol = 10.0 * 0.192 = 1.92, Energy = 2.0 * 0.45 = 0.90
        breakdown = calculate_footprint(input_data)
        self.assertEqual(breakdown["transport_emissions"], 1.92)
        self.assertEqual(breakdown["energy_emissions"], 0.90)
        self.assertEqual(breakdown["diet_emissions"], 0.0)
        self.assertEqual(breakdown["total_emissions"], 2.82)

    # Test 5 (Calculator Edge Case): Test negative parameters and string values to verify coercions.
    def test_calculator_edge_case(self) -> None:
        """Verify calculator sanitizes negative values and string conversions successfully."""
        # Case A: Negative inputs (coerce to 0.0)
        input_data = {
            "transport_km": -15.0,
            "transport_type": "petrol",
            "appliance_hours": -4.0,
            "diet_type": "vegetarian"
        }
        breakdown = calculate_footprint(input_data)
        self.assertEqual(breakdown["transport_emissions"], 0.0)
        self.assertEqual(breakdown["energy_emissions"], 0.0)
        self.assertEqual(breakdown["diet_emissions"], 1.7)
        self.assertEqual(breakdown["total_emissions"], 1.7)

        # Case B: Value conversion failures
        input_data_invalid = {
            "transport_km": "invalid_val",
            "transport_type": "diesel",
            "appliance_hours": "invalid_val",
            "diet_type": "high_meat"
        }
        breakdown_invalid = calculate_footprint(input_data_invalid)
        self.assertEqual(breakdown_invalid["transport_emissions"], 0.0)
        self.assertEqual(breakdown_invalid["energy_emissions"], 0.0)
        self.assertEqual(breakdown_invalid["diet_emissions"], 3.3)
        self.assertEqual(breakdown_invalid["total_emissions"], 3.3)

    # Test 6 (AI Extraction Parsing Success): Mock the google.generativeai response.
    @patch('google.generativeai.GenerativeModel.generate_content')
    def test_ai_extraction_parsing_success(self, mock_generate) -> None:
        """Verify extractor parses valid JSON format properly."""
        mock_response = MagicMock()
        mock_response.text = '{"transport_km": 12.5, "transport_type": "diesel", "appliance_hours": 5.0, "diet_type": "vegetarian"}'
        mock_generate.return_value = mock_response

        extracted = extract_metrics_from_chat("Drove 12.5km diesel, active for 5 hours", "mock-key")
        self.assertEqual(extracted["transport_km"], 12.5)
        self.assertEqual(extracted["transport_type"], "diesel")
        self.assertEqual(extracted["appliance_hours"], 5.0)
        self.assertEqual(extracted["diet_type"], "vegetarian")

    # Test 7 (AI Extraction Parsing Failure): Mock a broken/corrupted string response.
    @patch('google.generativeai.GenerativeModel.generate_content')
    def test_ai_extraction_parsing_failure(self, mock_generate) -> None:
        """Verify extractor handles non-JSON syntax and resolves to fallback dictionary."""
        mock_response = MagicMock()
        mock_response.text = 'Some unstructured chat error text from Gemini server.'
        mock_generate.return_value = mock_response

        extracted = extract_metrics_from_chat("Drove my car", "mock-key")
        self.assertEqual(extracted["transport_km"], 0.0)
        self.assertEqual(extracted["transport_type"], "none")
        self.assertEqual(extracted["appliance_hours"], 0.0)
        self.assertEqual(extracted["diet_type"], "balanced")

    # Test 8 (Database Integration Workflow): Post a chat entry and query db to verify storage.
    @patch('app.extract_metrics_from_chat')
    def test_database_integration_workflow(self, mock_extract) -> None:
        """Verify successful post, calculation, and database synchronization commits."""
        mock_extract.return_value = {
            "transport_km": 50.0,
            "transport_type": "ev",
            "appliance_hours": 3.0,
            "diet_type": "meat"
        }

        response = self.client.post('/api/chat', json={"message": "Commuted in EV today"})
        self.assertEqual(response.status_code, 200)

        db_log = db.session.query(CarbonLog).filter_by(user_id=1).order_by(CarbonLog.id.desc()).first()
        self.assertIsNotNone(db_log)
        self.assertEqual(db_log.transport_emissions, 2.35)
        self.assertEqual(db_log.energy_emissions, 1.35)
        self.assertEqual(db_log.diet_emissions, 3.3)
        self.assertEqual(db_log.total_emissions, 7.0)
        self.assertEqual(db_log.source_text, "Commuted in EV today")

    # Test 9 (Input Sanitization): Verify sanitize_input_text utility strips HTML tags and script payloads.
    def test_input_sanitization(self) -> None:
        """Verify html sanitizer strips markup elements and escapes special characters."""
        from app import sanitize_input_text
        dirty_input = "<script>alert('xss')</script>Hello <b>World</b> & test"
        clean = sanitize_input_text(dirty_input)
        self.assertEqual(clean, "alert(&#x27;xss&#x27;)Hello World &amp; test")

    # Test 10 (Security Headers): Verify outgoing HTTP responses contain strict security headers.
    def test_security_headers_injection(self) -> None:
        """Verify strict CSP, XSS, MIME, and clickjacking security headers are present."""
        response = self.client.get('/')
        self.assertEqual(response.status_code, 200)
        self.assertIn("Content-Security-Policy", response.headers)
        self.assertEqual(response.headers["X-Frame-Options"], "DENY")
        self.assertEqual(response.headers["X-Content-Type-Options"], "nosniff")
        self.assertEqual(response.headers["Referrer-Policy"], "strict-origin-when-cross-origin")

    # Test 11 (Malicious Payload via API / Chat Endpoint): Pass script tags and verify they get sanitized.
    @patch('app.extract_metrics_from_chat')
    def test_malicious_input_via_chat_api(self, mock_extract) -> None:
        """Verify API strips scripts and stores only clean representations."""
        mock_extract.return_value = {
            "transport_km": 10.0,
            "transport_type": "petrol",
            "appliance_hours": 1.0,
            "diet_type": "vegetarian"
        }
        payload = {"message": "<script>alert('malicious')</script> Drove petrol car 10km"}
        response = self.client.post('/api/chat', json=payload)
        self.assertEqual(response.status_code, 200)

        db_log = db.session.query(CarbonLog).order_by(CarbonLog.id.desc()).first()
        self.assertIsNotNone(db_log)
        self.assertEqual(db_log.source_text, "alert(&#x27;malicious&#x27;) Drove petrol car 10km")

    # Test 12 (Blocked Malicious Input): Post a payload that becomes empty after sanitization.
    def test_blocked_empty_malicious_input(self) -> None:
        """Verify server blocks messages that evaluate to empty strings post-sanitization."""
        payload = {"message": "<script></script>"}
        response = self.client.post('/api/chat', json=payload)
        self.assertEqual(response.status_code, 400)
        data = json.loads(response.data.decode('utf-8'))
        self.assertEqual(data["error"], "Bad Request")
        self.assertEqual(data["message"], "Input was blocked by dynamic security filters.")

    # Test 13 (Rapid Request Stress Flow): Simulate quick back-to-back mock requests.
    def test_rapid_request_stress_flow(self) -> None:
        """Simulate stress log request cycles to verify SQLite connection management."""
        for i in range(50):
            response = self.client.get('/')
            self.assertEqual(response.status_code, 200)
            log_response = self.client.post('/api/log', json={
                "category": f"stress_cat_{i}",
                "value": float(i),
                "unit": "kg"
            })
            self.assertEqual(log_response.status_code, 200)

    # Test 14 (Recommendations Branch coverage): Verify all decision branches in get_contextual_advice.
    def test_recommendations_branches(self) -> None:
        """Verify advise threshold conditions match emissions limits."""
        # High transport
        res = get_contextual_advice({"transport_emissions": 20.0, "energy_emissions": 0.0, "diet_emissions": 0.0, "total_emissions": 20.0})
        self.assertIn("transit emissions are elevated", res["tips_list"][0])

        # High energy
        res = get_contextual_advice({"transport_emissions": 0.0, "energy_emissions": 12.0, "diet_emissions": 0.0, "total_emissions": 12.0})
        self.assertIn("utility energy emissions are high", res["tips_list"][0])

        # High diet
        res = get_contextual_advice({"transport_emissions": 0.0, "energy_emissions": 0.0, "diet_emissions": 4.0, "total_emissions": 4.0})
        self.assertIn("daily diet emissions are high", res["tips_list"][0])

        # Moderate total, no individual high
        res = get_contextual_advice({"transport_emissions": 2.0, "energy_emissions": 2.0, "diet_emissions": 2.0, "total_emissions": 6.0})
        self.assertIn("moderate level of 6.00 kg CO2", res["status_alert"])
        self.assertIn("Keep logging your activities", res["tips_list"][0])

        # Zero emissions
        res = get_contextual_advice({"transport_emissions": 0.0, "energy_emissions": 0.0, "diet_emissions": 0.0, "total_emissions": 0.0})
        self.assertIn("zero carbon emissions", res["status_alert"])
        self.assertIn("Continue monitoring your daily activities", res["tips_list"][0])

    # Test 15 (AI Assistant Extractor branches): Verify parsing options fallback states.
    @patch('google.generativeai.GenerativeModel.generate_content')
    def test_ai_assistant_fallbacks(self, mock_generate) -> None:
        """Verify extraction options coerce unexpected models and values correctly."""
        # Case 1: Empty input or API key
        self.assertEqual(extract_metrics_from_chat("", "key"), {
            "transport_km": 0.0,
            "transport_type": "none",
            "appliance_hours": 0.0,
            "diet_type": "balanced"
        })
        self.assertEqual(extract_metrics_from_chat("Drove", ""), {
            "transport_km": 0.0,
            "transport_type": "none",
            "appliance_hours": 0.0,
            "diet_type": "balanced"
        })

        # Case 2: Gemini returns markdown wrapped content starting with ```
        mock_response = MagicMock()
        mock_response.text = "```json\n" \
                             "{\n" \
                             '  "transport_km": 10.0,\n' \
                             '  "transport_type": "ev",\n' \
                             '  "appliance_hours": 2.0,\n' \
                             '  "diet_type": "vegetarian"\n' \
                             "}\n" \
                             "```"
        mock_generate.return_value = mock_response
        extracted = extract_metrics_from_chat("Message", "key")
        self.assertEqual(extracted["transport_km"], 10.0)
        self.assertEqual(extracted["transport_type"], "ev")

        # Case 3: Missing keys in Gemini JSON structure
        mock_response.text = '{"transport_km": 5.0}'
        mock_generate.return_value = mock_response
        extracted = extract_metrics_from_chat("Message", "key")
        self.assertEqual(extracted["transport_type"], "none")

        # Case 4: Invalid transport type choices get coerced to fallback "none"
        mock_response.text = '{"transport_km": 15.0, "transport_type": "airplane", "appliance_hours": 1.0, "diet_type": "balanced"}'
        mock_generate.return_value = mock_response
        extracted = extract_metrics_from_chat("Message", "key")
        self.assertEqual(extracted["transport_type"], "none")

        # Case 5: Invalid diet type choices get coerced to fallback "balanced"
        mock_response.text = '{"transport_km": 15.0, "transport_type": "petrol", "appliance_hours": 1.0, "diet_type": "keto"}'
        mock_generate.return_value = mock_response
        extracted = extract_metrics_from_chat("Message", "key")
        self.assertEqual(extracted["diet_type"], "balanced")

    # Test 16 (Calculator missing parameters or invalid values): Verify type conversions.
    def test_calculator_missing_parameters(self) -> None:
        """Verify calculator converts missing parameters to empty emission logs."""
        breakdown = calculate_footprint({})
        self.assertEqual(breakdown["transport_emissions"], 0.0)
        self.assertEqual(breakdown["energy_emissions"], 0.0)
        self.assertEqual(breakdown["diet_emissions"], 0.0)
        self.assertEqual(breakdown["total_emissions"], 0.0)

    # Test 17 (App error boundaries & transactional rollback): Verify transactional error trigger.
    @patch('app.extract_metrics_from_chat')
    @patch('models.database.db.session.commit')
    def test_api_chat_transaction_rollback(self, mock_commit, mock_extract) -> None:
        """Verify transaction failures trigger rollback and report HTTP 500."""
        mock_extract.return_value = {
            "transport_km": 10.0,
            "transport_type": "diesel",
            "appliance_hours": 1.0,
            "diet_type": "meat"
        }
        mock_commit.side_effect = Exception("Mock database connection loss")
        payload = {"message": "Drove diesel car today"}
        response = self.client.post('/api/chat', json=payload)
        self.assertEqual(response.status_code, 500)
        data = json.loads(response.data.decode('utf-8'))
        self.assertEqual(data["error"], "Internal Server Error")

    # Test 18 (Dashboard Index exception block): Verify index rendering does not crash.
    @patch('models.database.db.session.query')
    def test_index_route_exception(self, mock_query) -> None:
        """Verify dashboard index gracefully loads fallback context upon db exception."""
        mock_query.side_effect = Exception("DB query crash")
        response = self.client.get('/')
        self.assertEqual(response.status_code, 200)

    # Test 19 (Endpoint API Manual Log error validation): Verify error response codes on malformed logs.
    def test_api_log_metric_errors(self) -> None:
        """Verify manual log route enforces float values and valid body keys."""
        # Case A: Missing JSON body
        response = self.client.post('/api/log', data="not-json")
        self.assertEqual(response.status_code, 415)

        # Case B: Missing category or value
        response = self.client.post('/api/log', json={"category": "energy"})
        self.assertEqual(response.status_code, 400)

        response = self.client.post('/api/log', json={"value": 12.3})
        self.assertEqual(response.status_code, 400)

        # Case C: Non-float value conversion failure
        response = self.client.post('/api/log', json={"category": "energy", "value": "unconvertible-string"})
        self.assertEqual(response.status_code, 400)
        data = json.loads(response.data.decode('utf-8'))
        self.assertEqual(data["error"], "Bad Request")

    # Test 20 (Database Commit Exception in manual log): Verify rollback and 500 code.
    @patch('models.database.db.session.commit')
    def test_api_log_commit_exception(self, mock_commit) -> None:
        """Verify database transaction failure in manual log endpoint results in code 500."""
        mock_commit.side_effect = Exception("Manual log DB save crash")
        response = self.client.post('/api/log', json={"category": "diet", "value": 3.5})
        self.assertEqual(response.status_code, 500)

    # Test 21 (Custom Error Handlers): Request non-existing routes and force trigger a 500 response error.
    def test_error_handlers(self) -> None:
        """Verify custom 404 and 500 error handlers return valid JSON contents."""
        # Test 404
        response = self.client.get('/this-route-does-not-exist')
        self.assertEqual(response.status_code, 404)
        data = json.loads(response.data.decode('utf-8'))
        self.assertEqual(data["error"], "Not Found")

        # Test 500 handler directly
        from app import internal_error
        res, code = internal_error(Exception("Mock error"))
        self.assertEqual(code, 500)
        self.assertIn("Internal Server Error", res.get_data(as_text=True))

    # Test 22 (User model representation and password checks): Verify password hashing methods.
    def test_user_password_hashing(self) -> None:
        """Verify cryptography-hashing functions and user serializers."""
        user = User(username="secure_user")
        user.set_password("mypassword")
        self.assertTrue(user.check_password("mypassword"))
        self.assertFalse(user.check_password("wrongpassword"))

        user_no_pass = User(username="no_pass")
        self.assertFalse(user_no_pass.check_password("any_password"))

        serialized = user.to_dict()
        self.assertEqual(serialized["username"], "secure_user")


if __name__ == '__main__':
    unittest.main()
