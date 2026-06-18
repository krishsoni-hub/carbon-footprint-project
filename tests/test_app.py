import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import unittest
import json
from unittest.mock import patch, MagicMock
from app import app
from models.database import db, User, CarbonLog, UserGoal, CarbonMetric
from controllers.calculator import calculate_footprint
from controllers.ai_assistant import extract_metrics_from_chat

class CarbonAppTestCase(unittest.TestCase):
    def setUp(self):
        """Set up dynamic database environment configurations before each test execution."""
        app.config['TESTING'] = True
        app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
        app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
        app.config['GEMINI_API_KEY'] = 'mock-api-key'
        
        # Setup application context and schema structures
        self.app_context = app.app_context()
        self.app_context.push()
        
        # Clear any dynamic session mappings from import execution inside context
        db.session.remove()
        db.create_all()
        
        # Setup application client
        self.client = app.test_client()
        
        # Seed dummy user safely checking query maps first
        self.user = db.session.get(User, 1)
        if not self.user:
            self.user = User(id=1, username="test_user")
            db.session.add(self.user)
            db.session.commit()

    def tearDown(self):
        """Tear down database session mapping states after test executions."""
        db.session.remove()
        db.drop_all()
        self.app_context.pop()

    # Test 1 (Route Access): Verify HTTP GET on '/' returns a 200 status code.
    def test_index_route_access(self):
        response = self.client.get('/')
        self.assertEqual(response.status_code, 200)

    # Test 2 (Route Access): Verify HTTP GET on '/chat' returns a 200 status code.
    def test_chat_view_route_access(self):
        response = self.client.get('/chat')
        self.assertEqual(response.status_code, 200)

    # Test 3 (API Edge Case): Verify HTTP POST on '/api/chat' handles a missing or empty message payload safely by returning a 400 bad request JSON response.
    def test_api_chat_empty_payload(self):
        # Case A: Missing message key completely
        response = self.client.post('/api/chat', json={})
        self.assertEqual(response.status_code, 400)
        data = json.loads(response.data.decode('utf-8'))
        self.assertEqual(data["error"], "Bad Request")
        self.assertIn("Missing or empty 'message'", data["message"])

        # Case B: Empty string message
        response = self.client.post('/api/chat', json={"message": ""})
        self.assertEqual(response.status_code, 400)
        data = json.loads(response.data.decode('utf-8'))
        self.assertEqual(data["error"], "Bad Request")

        # Case C: Whitespace message
        response = self.client.post('/api/chat', json={"message": "   "})
        self.assertEqual(response.status_code, 400)

    # Test 4 (Calculator Math Logic): Pass explicit mock dictionary data to calculate_footprint() for a Petrol Car (10km) and an Appliance (2 hours). Assert with 100% mathematical precision that the exact float output matches global conversion coefficients.
    def test_calculator_math_logic(self):
        input_data = {
            "transport_km": 10.0,
            "transport_type": "petrol",
            "appliance_hours": 2.0,
            "diet_type": "none"
        }
        # Calculation values:
        # Petrol emissions = 10.0 * 0.192 = 1.92
        # Energy emissions = 2.0 * 0.45 = 0.90
        # Diet emissions = 0.0
        # Total emissions = 1.92 + 0.90 = 2.82
        breakdown = calculate_footprint(input_data)
        self.assertEqual(breakdown["transport_emissions"], 1.92)
        self.assertEqual(breakdown["energy_emissions"], 0.90)
        self.assertEqual(breakdown["diet_emissions"], 0.0)
        self.assertEqual(breakdown["total_emissions"], 2.82)

    # Test 5 (Calculator Edge Case): Test calculate_footprint() with negative or unexpected text characters in string parameters to verify structural type-casting handles it gracefully.
    def test_calculator_edge_case(self):
        # Case A: Negative inputs (should coerce to 0.0)
        input_data = {
            "transport_km": -15.0,
            "transport_type": "petrol",
            "appliance_hours": -4.0,
            "diet_type": "vegetarian"
        }
        # Calculation values:
        # Transport = 0.0 * 0.192 = 0.0
        # Energy = 0.0 * 0.45 = 0.0
        # Diet (vegetarian) = 1.7
        # Total = 1.7
        breakdown = calculate_footprint(input_data)
        self.assertEqual(breakdown["transport_emissions"], 0.0)
        self.assertEqual(breakdown["energy_emissions"], 0.0)
        self.assertEqual(breakdown["diet_emissions"], 1.7)
        self.assertEqual(breakdown["total_emissions"], 1.7)

        # Case B: Unexpected characters in float conversions (should fallback to 0.0)
        input_data_invalid = {
            "transport_km": "invalid_number_string",
            "transport_type": "diesel",
            "appliance_hours": "unexpected_text_chars",
            "diet_type": "high_meat"
        }
        # Calculation values:
        # Invalid strings fall back to 0.0 emissions
        # Diet (high_meat) = 3.3
        # Total = 3.3
        breakdown_invalid = calculate_footprint(input_data_invalid)
        self.assertEqual(breakdown_invalid["transport_emissions"], 0.0)
        self.assertEqual(breakdown_invalid["energy_emissions"], 0.0)
        self.assertEqual(breakdown_invalid["diet_emissions"], 3.3)
        self.assertEqual(breakdown_invalid["total_emissions"], 3.3)

    # Test 6 (AI Extraction Parsing Success): Mock the google.generativeai response. Simulate a valid JSON string returned from Gemini and assert that extract_metrics_from_chat() maps the dictionary structure flawlessly.
    @patch('google.generativeai.GenerativeModel.generate_content')
    def test_ai_extraction_parsing_success(self, mock_generate):
        # Set up mock response
        mock_response = MagicMock()
        mock_response.text = '{"transport_km": 12.5, "transport_type": "diesel", "appliance_hours": 5.0, "diet_type": "vegetarian"}'
        mock_generate.return_value = mock_response

        extracted = extract_metrics_from_chat("Drove 12.5km diesel, active for 5 hours", "mock-key")
        self.assertEqual(extracted["transport_km"], 12.5)
        self.assertEqual(extracted["transport_type"], "diesel")
        self.assertEqual(extracted["appliance_hours"], 5.0)
        self.assertEqual(extracted["diet_type"], "vegetarian")

    # Test 7 (AI Extraction Parsing Failure): Mock a broken/corrupted unstructured string text response from Gemini API to ensure the try-except block captures it and falls back exactly to the default safe JSON object.
    @patch('google.generativeai.GenerativeModel.generate_content')
    def test_ai_extraction_parsing_failure(self, mock_generate):
        # Set up mock corrupted response
        mock_response = MagicMock()
        mock_response.text = 'Some unstructured chat error text from Gemini server.'
        mock_generate.return_value = mock_response

        # Call extractor
        extracted = extract_metrics_from_chat("Drove my car", "mock-key")
        # Assert fallback defaults
        self.assertEqual(extracted["transport_km"], 0.0)
        self.assertEqual(extracted["transport_type"], "none")
        self.assertEqual(extracted["appliance_hours"], 0.0)
        self.assertEqual(extracted["diet_type"], "balanced")

    # Test 8 (Database Integration Workflow): Simulate adding a CarbonLog entry via mock API call, commit it to the session, and assert using db.session.get() or a query that the data exists properly.
    @patch('app.extract_metrics_from_chat')
    def test_database_integration_workflow(self, mock_extract):
        # Setup mock behavior
        mock_extract.return_value = {
            "transport_km": 50.0,
            "transport_type": "ev",
            "appliance_hours": 3.0,
            "diet_type": "meat"
        }

        # Post chat entry
        response = self.client.post('/api/chat', json={"message": "Commuted in EV today"})
        self.assertEqual(response.status_code, 200)

        # Query the database
        db_log = db.session.query(CarbonLog).filter_by(user_id=1).order_by(CarbonLog.id.desc()).first()
        self.assertIsNotNone(db_log)
        
        # Verify calculation correctness inside database log fields:
        # EV emissions = 50.0 * 0.047 = 2.35
        # Appliance emissions = 3.0 * 0.45 = 1.35
        # Diet emissions = 3.3 (meat)
        # Total emissions = 2.35 + 1.35 + 3.3 = 7.0
        self.assertEqual(db_log.transport_emissions, 2.35)
        self.assertEqual(db_log.energy_emissions, 1.35)
        self.assertEqual(db_log.diet_emissions, 3.3)
        self.assertEqual(db_log.total_emissions, 7.0)
        self.assertEqual(db_log.source_text, "Commuted in EV today")

if __name__ == '__main__':
    unittest.main()
