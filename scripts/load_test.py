import asyncio
import httpx
import uuid
import time
from typing import List

async def send_notification(client: httpx.AsyncClient, i: int):
    response = await client.post(
        "http://localhost:8000/v1/notify",
        json={
            "type": "email",
            "recipient": f"test{i}@example.com",
            "payload": {"subject": f"Test {i}", "body": "Hello"},
            "max_retries": 3,
            "idempotency_key": str(uuid.uuid4())
        },
        headers={"X-API-Key": "test-key-123"}
    )
    return response.status_code

async def main():
    async with httpx.AsyncClient() as client:
        start = time.time()
        tasks = [send_notification(client, i) for i in range(100)]
        results = await asyncio.gather(*tasks)
        elapsed = time.time() - start
        
        print(f"Sent 100 notifications in {elapsed:.2f}s")
        print(f"Success rate: {results.count(202)}%")

if __name__ == "__main__":
    asyncio.run(main())