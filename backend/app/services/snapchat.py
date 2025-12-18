"""
Snapchat Spotlight API service
"""

import os
from pathlib import Path
from typing import Dict, Optional

import aiofiles
import httpx
from fastapi import HTTPException, status

from app.core.config import settings


class SnapchatService:
    """Service for interacting with Snapchat Spotlight API via RapidAPI"""

    BASE_URL = "https://snapchat3.p.rapidapi.com"
    MEDIA_DIR = Path("/app/media/spotlight_videos")

    def __init__(self):
        self.api_key = os.getenv("RAPIDAPI_KEY")
        if not self.api_key:
            raise ValueError("RAPIDAPI_KEY environment variable is not set")

        # Ensure media directory exists
        self.MEDIA_DIR.mkdir(parents=True, exist_ok=True)

    async def fetch_spotlight_data(self, spotlight_link: str) -> Dict:
        """
        Fetch Spotlight content metadata from RapidAPI

        Args:
            spotlight_link: Full Snapchat Spotlight URL

        Returns:
            Dict containing the API response data

        Raises:
            HTTPException: If API request fails
        """
        url = f"{self.BASE_URL}/getSpotlightByLink"
        headers = {
            "x-rapidapi-key": self.api_key,
            "x-rapidapi-host": "snapchat3.p.rapidapi.com",
        }
        params = {"spotlight_link": spotlight_link}

        async with httpx.AsyncClient(timeout=30.0) as client:
            try:
                response = await client.get(url, headers=headers, params=params)
                response.raise_for_status()
                data = response.json()

                if not data.get("success"):
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail="Failed to fetch Spotlight content from Snapchat API",
                    )

                return data["data"]
            except httpx.HTTPStatusError as e:
                raise HTTPException(
                    status_code=e.response.status_code,
                    detail=f"Snapchat API error: {e.response.text}",
                )
            except httpx.RequestError as e:
                raise HTTPException(
                    status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                    detail=f"Failed to connect to Snapchat API: {str(e)}",
                )

    async def download_video(self, video_url: str, spotlight_id: str) -> str:
        """
        Download video from URL and save to local storage

        Args:
            video_url: URL of the video to download
            spotlight_id: Unique Spotlight ID for filename

        Returns:
            str: Local file path where video was saved

        Raises:
            HTTPException: If download fails
        """
        # Create filename from spotlight_id
        filename = f"{spotlight_id}.mp4"
        file_path = self.MEDIA_DIR / filename

        async with httpx.AsyncClient(timeout=60.0) as client:
            try:
                # Stream download to handle large files
                async with client.stream("GET", video_url) as response:
                    response.raise_for_status()

                    async with aiofiles.open(file_path, "wb") as f:
                        async for chunk in response.aiter_bytes(chunk_size=8192):
                            await f.write(chunk)

                return str(file_path)

            except httpx.HTTPStatusError as e:
                raise HTTPException(
                    status_code=status.HTTP_502_BAD_GATEWAY,
                    detail=f"Failed to download video: {e.response.status_code}",
                )
            except httpx.RequestError as e:
                raise HTTPException(
                    status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                    detail=f"Failed to connect to video server: {str(e)}",
                )
            except Exception as e:
                # Clean up partial file if exists
                if file_path.exists():
                    file_path.unlink()
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=f"Failed to save video: {str(e)}",
                )

    def parse_spotlight_metadata(self, data: Dict) -> Dict:
        """
        Parse Spotlight API response and extract relevant metadata

        Args:
            data: Raw API response data

        Returns:
            Dict with parsed metadata fields
        """
        story = data.get("story", {})
        metadata = data.get("metadata", {})
        video_metadata = metadata.get("videoMetadata", {})
        engagement_stats = metadata.get("engagementStats", {})

        # Get creator info
        creator = video_metadata.get("creator", {})
        creator_info = creator.get("personCreator", {}) if creator.get("$case") == "personCreator" else {}

        # Get snap list (should have one item for Spotlight)
        snap_list = story.get("snapList", [])
        snap = snap_list[0] if snap_list else {}
        snap_urls = snap.get("snapUrls", {})

        return {
            "spotlight_id": story.get("storyId", {}).get("value", ""),
            "video_url": snap_urls.get("mediaUrl", ""),
            "thumbnail_url": story.get("thumbnailUrl", {}).get("value", ""),
            "duration_ms": int(video_metadata.get("durationMs", 0)) if video_metadata.get("durationMs") else None,
            "width": video_metadata.get("width"),
            "height": video_metadata.get("height"),
            "creator_username": creator_info.get("username"),
            "creator_name": creator_info.get("name"),
            "creator_url": creator_info.get("url"),
            "view_count": int(engagement_stats.get("viewCount", 0)) if engagement_stats.get("viewCount") else None,
            "share_count": int(engagement_stats.get("shareCount", 0)) if engagement_stats.get("shareCount") else None,
            "comment_count": int(engagement_stats.get("commentCount", 0)) if engagement_stats.get("commentCount") else None,
            "boost_count": int(engagement_stats.get("boostCount", 0)) if engagement_stats.get("boostCount") else None,
            "recommend_count": int(engagement_stats.get("recommendCount", 0)) if engagement_stats.get("recommendCount") else None,
            "upload_timestamp": int(snap.get("timestampInSec", {}).get("value", 0)) if snap.get("timestampInSec") else None,
        }


# Singleton instance
snapchat_service = SnapchatService()
