import httpx
import asyncio

async def test_endpoints():
    print("Testing backend endpoints with mock PDF payload...")
    
    mock_pdf = {
        "insurer": "Star Health",
        "policy_name": "Family Health Optima",
        "covered_treatments": ["Cardiac Surgery", "Appendectomy"],
        "waiting_period_days": 30,
        "freebies": [
            {"id": "f1", "label": "Free Health Checkup", "total_per_cycle": 1, "used": 0, "status": "available"}
        ]
    }
    
    base_url = "http://127.0.0.1:8000"
    
    async with httpx.AsyncClient() as client:
        try:
            # 1. Test Eligibility Options (POST)
            print("\n1. Testing POST /api/eligibility/policy-options")
            r1 = await client.post(f"{base_url}/api/eligibility/policy-options", json={"pdf_policy": mock_pdf})
            print(f"Status: {r1.status_code}")
            if r1.status_code == 200:
                print(f"Detected Insurer: {r1.json().get('pdf_policy', {}).get('insurer')}")
            
            # 2. Test Eligibility Check (POST)
            print("\n2. Testing POST /api/eligibility")
            payload2 = {
                "treatment": "Cardiac Surgery",
                "policy": "Star Health",
                "age": 30,
                "waiting_period_served_days": 60,
                "pdf_policy": mock_pdf
            }
            r2 = await client.post(f"{base_url}/api/eligibility", json=payload2)
            print(f"Status: {r2.status_code}")
            if r2.status_code == 200:
                print(f"Eligible: {r2.json().get('eligible')}")
                
            # 3. Test Hospitals Search (POST)
            print("\n3. Testing POST /api/hospitals/search")
            r3 = await client.post(f"{base_url}/api/hospitals/search", json={"city": "Mumbai", "treatment": "Cardiac Surgery", "pdf_policy": mock_pdf})
            print(f"Status: {r3.status_code}")
            if r3.status_code == 200:
                print(f"Hospitals found: {r3.json().get('count')}")
                print(f"Context Insurer: {r3.json().get('policy_context', {}).get('user_insurer')}")

            # 4. Test Notifications Freebies (POST)
            print("\n4. Testing POST /api/notifications/freebies")
            r4 = await client.post(f"{base_url}/api/notifications/freebies", json={"pdf_policy": mock_pdf})
            print(f"Status: {r4.status_code}")
            if r4.status_code == 200:
                print(f"Total Benefits: {r4.json().get('summary', {}).get('total_benefits')}")
                
            # 5. Test Notifications Mark Used (POST)
            print("\n5. Testing POST /api/notifications/freebies/mark-used")
            r5 = await client.post(f"{base_url}/api/notifications/freebies/mark-used", json={"freebie_id": "f1", "pdf_policy": mock_pdf})
            print(f"Status: {r5.status_code}")
            if r5.status_code == 200:
                updated_pdf = r5.json().get("updated_pdf_policy", {})
                used = updated_pdf.get("freebies", [{}])[0].get("used")
                print(f"Freebie marked used. Used count: {used}")

            if all(r.status_code == 200 for r in [r1, r2, r3, r4, r5]):
                print("\n✅ All state migration endpoints verified successfully!")
            else:
                print("\n❌ Some endpoints failed.")

        except Exception as e:
            print(f"Connection failed: {e}. Is the server running?")

if __name__ == "__main__":
    asyncio.run(test_endpoints())
