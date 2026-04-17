import httpx
import asyncio
import random
from typing import Literal
from config import YOUTUBE_API_KEY

async def get_video_description(client: httpx.AsyncClient, video_id: str):
    url = "https://www.googleapis.com/youtube/v3/videos"
    params = {
        "part": "snippet",
        "id": video_id,
        "key": YOUTUBE_API_KEY
    }
    resp = await client.get(url, params=params)
    resp.raise_for_status()
    data = resp.json()

    items = data.get("items", [])
    if not items:
        return None

    description = items[0]["snippet"].get("description", "")
    links = [line.strip() for line in description.splitlines() 
             if "https://link.clashofclans.com" in line]
    return links


async def search_videos(query: Literal['layout', 'strategy'], max_results=30):
    url = "https://www.googleapis.com/youtube/v3/search"
    params = {
        "part": "snippet",
        "type": "video",
        "order": "viewCount",
        "publishedAfter": "2026-01-01T00:00:00Z",
        "maxResults": 20 if query == "strategy" else max_results,
        "key": YOUTUBE_API_KEY
    }

    if query == "strategy":
        params["q"] = "Clash of Clans best TH18 strategy OR attack OR troop mix OR army composition"
    else:  # layout
        params["q"] = "Clash of Clans best TH18 base OR layout OR war base OR farming base"

    async with httpx.AsyncClient(timeout=15.0) as client:
        resp = await client.get(url, params=params)
        resp.raise_for_status()
        data = resp.json()

        videos = []
        tasks = []

        for item in data.get('items', []):
            video_id = item['id']['videoId']
            tasks.append(get_video_description(client, video_id))

        # Параллельно получаем описания для всех видео
        descriptions = await asyncio.gather(*tasks, return_exceptions=True)

        for item, links in zip(data.get('items', []), descriptions):
            if isinstance(links, Exception):
                links = []
            title = item['snippet']['title']
            video = {
                'title': title,
                'url': f"https://www.youtube.com/watch?v={item['id']['videoId']}",
                'links': links
            }
            if ("base" in title.lower() or query == 'strategy') and links:
                videos.append(video)

        cycle = min(3, len(videos))
        return random.sample(videos, cycle) if cycle > 0 else []