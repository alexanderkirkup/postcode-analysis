import asyncio
import time

import aiohttp

class AsyncRequests(object):
    def __init__(self, rateLimit, timeout=10):
        self.rateLimit = rateLimit
        self.timeout = timeout

        self.session = aiohttp.ClientSession()
        self.lastRequest = 0

    async def rate_limiter(self):
        now = time.monotonic()
        sleep = max(self.rateLimit - now + self.lastRequest, 0)
        self.lastRequest = now + sleep
        return await asyncio.sleep(sleep)

    async def fetch_json(self, url, params={}, headers={}, retries=3):
        await self.rate_limiter()

        try:
            async with self.session.get(url, params=params, headers=headers, timeout=self.timeout) as resp:
                r = await resp.json()
                assert r is not None
        except Exception:
            if retries > 0:
                r = await self.fetch_json(url, params, headers, retries-1)
            else:
                raise Exception
        print('AsyncRequests: Fetch successful', resp.status, time.monotonic())
        return r

    async def fetch(self, url, params={}, headers={}, retries=3):
        await self.rate_limiter()

        try:
            # print(time.monotonic())
            async with self.session.get(url, params=params, headers=headers, timeout=self.timeout) as resp:
                r = await resp.json()
                status = resp.status
        except Exception:
            if retries > 0:
                return await self.fetch(url, params, headers, retries-1)
            else:
                raise Exception
        print('AsyncRequests: Fetch successful', resp.status, time.monotonic())
        return r, status
    
    async def close(self):
        await self.session.close()