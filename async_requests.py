import asyncio
import aiohttp

class AsyncRequests(object):
    def __init__(self, url, fetchList, rateLimit=1, timeout=10, retrySleep=0.1):
        self.url = url
        self.fetchList = fetchList  # list of dicts with attributes for each request (urlPath, params, headers)
        self.rateLimit = rateLimit
        self.timeout = timeout
        self.retrySleep = retrySleep

        self.session = aiohttp.ClientSession()
        self.resultsList = []

    async def _fetch(self, urlPath, params={}, headers={}, retries=3):
        try:
            async with self.session.get(self.url+urlPath, params=params, headers=headers, timeout=self.timeout) as resp:
                r = await resp.json()
        except Exception:
            if retries > 0:
                await asyncio.sleep(self.retrySleep)
                r = await self._fetch(urlPath, params, headers, retries-1)
            else:
                raise Exception
        self.resultsList.append(r)
        print('Done')
        return
    
    async def close(self):
        await self.session.close()

    async def run(self):
        for fetchDict in self.fetchList:
            asyncio.ensure_future(self._fetch(**fetchDict))
            await asyncio.sleep(self.rateLimit)
        await self.close()