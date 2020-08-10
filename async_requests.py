import asyncio
import aiohttp

class AsyncRequests(object):
    def __init__(self, url, timeout=10, retrySleep=0.1):
        self.url = url
        self.timeout = timeout
        self.retrySleep = retrySleep

        self.session = aiohttp.ClientSession()

    async def fetch(self, callClass, urlPath, params={}, headers={}, retries=3):
        try:
            async with self.session.get(self.url+urlPath, params=params, headers=headers, timeout=self.timeout) as resp:
                r = await resp.json()
        except Exception:
            if retries > 0:
                await asyncio.sleep(self.retrySleep)
                r = await self.fetch(urlPath, params, headers, retries-1)
            else:
                raise Exception
        callClass.result = r
        print('Done')
        return
    
    async def close(self):
        await self.session.close()