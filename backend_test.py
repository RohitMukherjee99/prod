#!/usr/bin/env python3

import requests
import sys
import json
from datetime import datetime

class ConferenceAPITester:
    def __init__(self, base_url="https://implantscience.preview.emergentagent.com"):
        self.base_url = base_url
        self.api_url = f"{base_url}/api"
        self.tests_run = 0
        self.tests_passed = 0
        self.test_results = []

    def log_test(self, name, success, details=""):
        """Log test result"""
        self.tests_run += 1
        if success:
            self.tests_passed += 1
        
        result = {
            "test": name,
            "status": "PASS" if success else "FAIL",
            "details": details,
            "timestamp": datetime.now().isoformat()
        }
        self.test_results.append(result)
        
        status_icon = "✅" if success else "❌"
        print(f"{status_icon} {name}: {details}")

    def test_api_root(self):
        """Test API root endpoint"""
        try:
            response = requests.get(f"{self.api_url}/", timeout=10)
            success = response.status_code == 200
            details = f"Status: {response.status_code}"
            if success:
                data = response.json()
                details += f", Message: {data.get('message', 'N/A')}"
            self.log_test("API Root", success, details)
            return success
        except Exception as e:
            self.log_test("API Root", False, f"Error: {str(e)}")
            return False

    def test_health_check(self):
        """Test health check endpoint"""
        try:
            response = requests.get(f"{self.api_url}/health", timeout=10)
            success = response.status_code == 200
            details = f"Status: {response.status_code}"
            if success:
                data = response.json()
                details += f", Status: {data.get('status', 'N/A')}"
            self.log_test("Health Check", success, details)
            return success
        except Exception as e:
            self.log_test("Health Check", False, f"Error: {str(e)}")
            return False

    def test_pricing_endpoint(self):
        """Test pricing endpoint"""
        try:
            response = requests.get(f"{self.api_url}/pricing", timeout=10)
            success = response.status_code == 200
            details = f"Status: {response.status_code}"
            if success:
                data = response.json()
                has_registration = 'registration' in data
                has_accommodation = 'accommodation' in data
                details += f", Has registration pricing: {has_registration}, Has accommodation: {has_accommodation}"
            self.log_test("Pricing Endpoint", success, details)
            return success, data if success else {}
        except Exception as e:
            self.log_test("Pricing Endpoint", False, f"Error: {str(e)}")
            return False, {}

    def test_contact_submission(self):
        """Test contact form submission"""
        try:
            contact_data = {
                "name": "Test User",
                "email": "test@example.com",
                "phone": "+91 9876543210",
                "subject": "Test Subject",
                "message": "This is a test message from automated testing."
            }
            
            response = requests.post(
                f"{self.api_url}/contact",
                json=contact_data,
                headers={'Content-Type': 'application/json'},
                timeout=10
            )
            
            success = response.status_code == 200
            details = f"Status: {response.status_code}"
            if success:
                data = response.json()
                details += f", Contact ID: {data.get('id', 'N/A')}"
            else:
                details += f", Error: {response.text}"
            
            self.log_test("Contact Submission", success, details)
            return success, response.json() if success else {}
        except Exception as e:
            self.log_test("Contact Submission", False, f"Error: {str(e)}")
            return False, {}

    def test_registration_creation(self):
        """Test registration creation"""
        try:
            registration_data = {
                "full_name": "Dr. Test User",
                "email": "test.doctor@example.com",
                "phone": "+91 9876543210",
                "category": "delegate_early_bird",
                "organization": "Test Hospital",
                "designation": "Consultant",
                "accommodation_required": False
            }
            
            response = requests.post(
                f"{self.api_url}/registration",
                json=registration_data,
                headers={'Content-Type': 'application/json'},
                timeout=10
            )
            
            success = response.status_code == 200
            details = f"Status: {response.status_code}"
            if success:
                data = response.json()
                details += f", Registration ID: {data.get('id', 'N/A')}, Amount: ₹{data.get('amount', 0)/100}"
                return success, data
            else:
                details += f", Error: {response.text}"
                
            self.log_test("Registration Creation", success, details)
            return success, {}
        except Exception as e:
            self.log_test("Registration Creation", False, f"Error: {str(e)}")
            return False, {}

    def test_registration_retrieval(self, registration_id):
        """Test registration retrieval by ID"""
        try:
            response = requests.get(f"{self.api_url}/registration/{registration_id}", timeout=10)
            success = response.status_code == 200
            details = f"Status: {response.status_code}"
            if success:
                data = response.json()
                details += f", Name: {data.get('full_name', 'N/A')}"
            else:
                details += f", Error: {response.text}"
            
            self.log_test("Registration Retrieval", success, details)
            return success
        except Exception as e:
            self.log_test("Registration Retrieval", False, f"Error: {str(e)}")
            return False

    def test_get_contacts(self):
        """Test getting all contacts"""
        try:
            response = requests.get(f"{self.api_url}/contacts", timeout=10)
            success = response.status_code == 200
            details = f"Status: {response.status_code}"
            if success:
                data = response.json()
                details += f", Contact count: {len(data)}"
            else:
                details += f", Error: {response.text}"
            
            self.log_test("Get Contacts", success, details)
            return success
        except Exception as e:
            self.log_test("Get Contacts", False, f"Error: {str(e)}")
            return False

    def test_get_registrations(self):
        """Test getting all registrations"""
        try:
            response = requests.get(f"{self.api_url}/registrations", timeout=10)
            success = response.status_code == 200
            details = f"Status: {response.status_code}"
            if success:
                data = response.json()
                details += f", Registration count: {len(data)}"
            else:
                details += f", Error: {response.text}"
            
            self.log_test("Get Registrations", success, details)
            return success
        except Exception as e:
            self.log_test("Get Registrations", False, f"Error: {str(e)}")
            return False

    def test_payment_endpoints(self):
        """Test payment-related endpoints (will likely fail without Razorpay keys)"""
        try:
            # Test create order endpoint
            order_data = {
                "amount": 1200000,  # ₹12,000 in paise
                "currency": "INR",
                "registration_id": "test-registration-id"
            }
            
            response = requests.post(
                f"{self.api_url}/create-order",
                json=order_data,
                headers={'Content-Type': 'application/json'},
                timeout=10
            )
            
            success = response.status_code == 200
            details = f"Create Order - Status: {response.status_code}"
            if not success:
                details += f", Error: {response.text}"
            
            self.log_test("Payment Create Order", success, details)
            return success
        except Exception as e:
            self.log_test("Payment Create Order", False, f"Error: {str(e)}")
            return False

    def run_all_tests(self):
        """Run all API tests"""
        print("🚀 Starting Conference API Tests...")
        print(f"📍 Testing API at: {self.api_url}")
        print("=" * 60)
        
        # Basic connectivity tests
        api_root_ok = self.test_api_root()
        health_ok = self.test_health_check()
        
        if not (api_root_ok or health_ok):
            print("\n❌ CRITICAL: API is not accessible. Stopping tests.")
            return False
        
        # Core functionality tests
        pricing_ok, pricing_data = self.test_pricing_endpoint()
        contact_ok, contact_data = self.test_contact_submission()
        registration_ok, registration_data = self.test_registration_creation()
        
        # Test registration retrieval if creation succeeded
        if registration_ok and registration_data.get('id'):
            self.test_registration_retrieval(registration_data['id'])
        
        # Test list endpoints
        self.test_get_contacts()
        self.test_get_registrations()
        
        # Test payment endpoints (expected to fail without keys)
        self.test_payment_endpoints()
        
        # Print summary
        print("\n" + "=" * 60)
        print(f"📊 Test Summary: {self.tests_passed}/{self.tests_run} tests passed")
        
        if self.tests_passed == self.tests_run:
            print("🎉 All tests passed!")
        elif self.tests_passed >= self.tests_run * 0.7:
            print("⚠️  Most tests passed - minor issues detected")
        else:
            print("❌ Multiple test failures detected")
        
        return self.tests_passed >= self.tests_run * 0.5

def main():
    tester = ConferenceAPITester()
    success = tester.run_all_tests()
    
    # Save detailed results
    with open('/app/backend_test_results.json', 'w') as f:
        json.dump({
            'summary': {
                'total_tests': tester.tests_run,
                'passed_tests': tester.tests_passed,
                'success_rate': tester.tests_passed / tester.tests_run if tester.tests_run > 0 else 0,
                'timestamp': datetime.now().isoformat()
            },
            'detailed_results': tester.test_results
        }, f, indent=2)
    
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())