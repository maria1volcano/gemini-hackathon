import unittest
from unittest.mock import MagicMock, patch
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Mock google.genai BEFORE importing tools
sys.modules["google"] = MagicMock()
sys.modules["google.genai"] = MagicMock()
sys.modules["google.genai.types"] = MagicMock()

from tools.booking_tools import BookingTools

class TestBookingTools(unittest.TestCase):
    
    def setUp(self):
        self.tools = BookingTools()
        # Ensure we simulate "Connected" state even if env var is missing
        self.tools._connected = True 
        self.tools.api_key = "test_key"

    @patch('requests.get')
    def test_search_hotels_resolution_success(self, mock_get):
        """Test happy path: Resolve Loc -> Fetch properties"""
        
        # Mock Response 1: Location Search
        mock_loc_response = MagicMock()
        mock_loc_response.status_code = 200
        mock_loc_response.json.return_value = {
            "status": True,
            "message": "Success",
            "data": [
                {
                    "dest_id": "-12345",
                    "search_type": "CITY",
                    "name": "Paris"
                }
            ]
        }
        
        # Mock Response 2: Hotel Search
        mock_hotel_response = MagicMock()
        mock_hotel_response.status_code = 200
        mock_hotel_response.json.return_value = {
            "status": True, 
            "message": "Success",
            "data": {
                "hotels": [
                    {
                        "property": {
                            "name": "Test Hotel",
                            "reviewScore": 8.5,
                            "priceBreakdown": {
                                "grossPrice": {
                                    "value": 150.00
                                }
                            },
                            "photoUrls": ["http://test.jpg"]
                        }
                    }
                ]
            }
        }
        
        # Configure side_effect for requests.get
        mock_get.side_effect = [mock_loc_response, mock_hotel_response]
        
        # Execute
        results = self.tools.search_hotels("Paris", "2024-06-01", "2024-06-07")
        
        # Verify
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]['name'], "Test Hotel")
        self.assertIn("150.0", str(results[0]['price'])) # formatting check
        
        # Verify calls
        # Call 1: Resolution
        args, kwargs = mock_get.call_args_list[0]
        self.assertIn("searchDestination", args[0])
        self.assertIn("Paris", kwargs['params']['query'])
        
        # Call 2: Fetch
        args, kwargs = mock_get.call_args_list[1]
        self.assertIn("searchHotels", args[0])
        self.assertEqual(kwargs['params']['dest_id'], "-12345")

    @patch('requests.get')
    def test_fallback_on_api_failure(self, mock_get):
        """Test fallback to mock data if API crashes"""
        
        # Simulate API Error
        mock_get.side_effect = Exception("API Down")
        
        # Execute
        results = self.tools.search_hotels("London", "2024-06-01", "2024-06-07")
        
        # Verify fallback
        self.assertTrue(len(results) > 0)
        self.assertIn("Grand Hotel", results[0]['name']) # Characteristic of mock data
        print(f"Fallback successful: Returned {len(results)} mock hotels.")

if __name__ == '__main__':
    unittest.main()
