import httpx
import asyncio
import sys

async def check_endpoints():
    base_url = "http://localhost:8000"
    endpoints = [
        "/api/health",
        "/api/notifications/freebies",
    ]
    
    print(f"Testing endpoints on {base_url}...")
    
    async with httpx.AsyncClient(base_url=base_url, timeout=5.0) as client:
        all_passed = True
        for endpoint in endpoints:
            try:
                response = await client.get(endpoint)
                # Some endpoints might require auth or return 4xx, but 404 means the route doesn't exist.
                if response.status_code == 404:
                    print(f"❌ {endpoint} returned 404 Not Found (Routing Issue!)")
                    all_passed = False
                else:
                    print(f"✅ {endpoint} responded with status {response.status_code}")
            except Exception as e:
                print(f"❌ {endpoint} failed to connect: {e}")
                all_passed = False
                
        if all_passed:
            print("\n✅ All tested API routes exist and are accessible!")
            sys.exit(0)
        else:
            print("\n❌ Verification failed. Check your routing configuration.")
            sys.exit(1)

if __name__ == "__main__":
    print("Please make sure the backend is running on port 8000 before executing this script.")
    print("Run `uvicorn main:app --reload` in another terminal.")
    asyncio.run(check_endpoints())
