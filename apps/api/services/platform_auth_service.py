from typing import Dict, Any, Optional
import os
import time
import logging
import aiohttp
from fastapi import HTTPException

logger = logging.getLogger(__name__)

class AuthProvider:
    def __init__(self, client_id: str, client_secret: str, scopes: list = None):
        self.client_id = client_id
        self.client_secret = client_secret
        self.scopes = scopes or []

    def get_auth_url(self, redirect_uri: str, state: str) -> str:
        """Get authorization URL for the provider."""
        raise NotImplementedError()

    async def exchange_code(self, code: str, redirect_uri: str) -> Dict[str, Any]:
        """Exchange authorization code for tokens."""
        raise NotImplementedError()

    async def refresh_token(self, refresh_token: str) -> Dict[str, Any]:
        """Refresh an expired access token."""
        raise NotImplementedError()

    async def get_basic_profile(self, access_token: str) -> Dict[str, Any]:
        """Get basic profile information."""
        raise NotImplementedError()

class LinkedInAuthProvider(AuthProvider):
    def get_auth_url(self, redirect_uri: str, state: str) -> str:
        scope_str = "%20".join(self.scopes)
        return (
            f"https://www.linkedin.com/oauth/v2/authorization"
            f"?response_type=code"
            f"&client_id={self.client_id}"
            f"&redirect_uri={redirect_uri}"
            f"&state={state}"
            f"&scope={scope_str}"
        )

    async def exchange_code(self, code: str, redirect_uri: str) -> Dict[str, Any]:
        async with aiohttp.ClientSession() as session:
            async with session.post(
                "https://www.linkedin.com/oauth/v2/accessToken",
                data={
                    "grant_type": "authorization_code",
                    "code": code,
                    "redirect_uri": redirect_uri,
                    "client_id": self.client_id,
                    "client_secret": self.client_secret
                }
            ) as response:
                if response.status != 200:
                    error_text = await response.text()
                    raise HTTPException(status_code=400, detail=f"LinkedIn token exchange failed: {error_text}")

                data = await response.json()
                return {
                    "access_token": data["access_token"],
                    "expires_in": data["expires_in"],
                    "refresh_token": data.get("refresh_token"),
                    "created_at": int(time.time())
                }

    async def refresh_token(self, refresh_token: str) -> Dict[str, Any]:
        async with aiohttp.ClientSession() as session:
            async with session.post(
                "https://www.linkedin.com/oauth/v2/accessToken",
                data={
                    "grant_type": "refresh_token",
                    "refresh_token": refresh_token,
                    "client_id": self.client_id,
                    "client_secret": self.client_secret
                }
            ) as response:
                if response.status != 200:
                    error_text = await response.text()
                    raise HTTPException(status_code=400, detail=f"LinkedIn token refresh failed: {error_text}")

                data = await response.json()
                return {
                    "access_token": data["access_token"],
                    "expires_in": data["expires_in"],
                    "refresh_token": data.get("refresh_token", refresh_token),
                    "created_at": int(time.time())
                }

    async def get_basic_profile(self, access_token: str) -> Dict[str, Any]:
        async with aiohttp.ClientSession() as session:
            async with session.get(
                "https://api.linkedin.com/v2/me",
                headers={"Authorization": f"Bearer {access_token}"}
            ) as response:
                if response.status != 200:
                    error_text = await response.text()
                    raise HTTPException(status_code=400, detail=f"LinkedIn profile retrieval failed: {error_text}")

                data = await response.json()
                return {
                    "id": data["id"],
                    "first_name": data.get("localizedFirstName", ""),
                    "last_name": data.get("localizedLastName", ""),
                    "profile_url": f"https://www.linkedin.com/in/{data.get('vanityName', '')}"
                }

class TwitterAuthProvider(AuthProvider):
    def get_auth_url(self, redirect_uri: str, state: str) -> str:
        scope_str = "%20".join(self.scopes)
        return (
            f"https://twitter.com/i/oauth2/authorize"
            f"?response_type=code"
            f"&client_id={self.client_id}"
            f"&redirect_uri={redirect_uri}"
            f"&state={state}"
            f"&scope={scope_str}"
            f"&code_challenge=challenge"
            f"&code_challenge_method=plain"
        )

    async def exchange_code(self, code: str, redirect_uri: str) -> Dict[str, Any]:
        async with aiohttp.ClientSession() as session:
            async with session.post(
                "https://api.twitter.com/2/oauth2/token",
                data={
                    "grant_type": "authorization_code",
                    "code": code,
                    "redirect_uri": redirect_uri,
                    "client_id": self.client_id,
                    "client_secret": self.client_secret,
                    "code_verifier": "challenge"
                }
            ) as response:
                if response.status != 200:
                    error_text = await response.text()
                    raise HTTPException(status_code=400, detail=f"Twitter token exchange failed: {error_text}")

                data = await response.json()
                return {
                    "access_token": data["access_token"],
                    "expires_in": data["expires_in"],
                    "refresh_token": data.get("refresh_token"),
                    "created_at": int(time.time())
                }

    async def refresh_token(self, refresh_token: str) -> Dict[str, Any]:
        async with aiohttp.ClientSession() as session:
            async with session.post(
                "https://api.twitter.com/2/oauth2/token",
                data={
                    "grant_type": "refresh_token",
                    "refresh_token": refresh_token,
                    "client_id": self.client_id,
                    "client_secret": self.client_secret
                }
            ) as response:
                if response.status != 200:
                    error_text = await response.text()
                    raise HTTPException(status_code=400, detail=f"Twitter token refresh failed: {error_text}")

                data = await response.json()
                return {
                    "access_token": data["access_token"],
                    "expires_in": data["expires_in"],
                    "refresh_token": data.get("refresh_token", refresh_token),
                    "created_at": int(time.time())
                }

    async def get_basic_profile(self, access_token: str) -> Dict[str, Any]:
        async with aiohttp.ClientSession() as session:
            async with session.get(
                "https://api.twitter.com/2/users/me",
                headers={"Authorization": f"Bearer {access_token}"}
            ) as response:
                if response.status != 200:
                    error_text = await response.text()
                    raise HTTPException(status_code=400, detail=f"Twitter profile retrieval failed: {error_text}")

                data = await response.json()
                return {
                    "id": data["data"]["id"],
                    "username": data["data"]["username"],
                    "name": data["data"]["name"],
                    "profile_url": f"https://twitter.com/{data['data']['username']}"
                }

class GoogleAuthProvider(AuthProvider):
    def get_auth_url(self, redirect_uri: str, state: str) -> str:
        scope_str = "%20".join(self.scopes)
        return (
            f"https://accounts.google.com/o/oauth2/v2/auth"
            f"?response_type=code"
            f"&client_id={self.client_id}"
            f"&redirect_uri={redirect_uri}"
            f"&state={state}"
            f"&scope={scope_str}"
            f"&access_type=offline"
            f"&prompt=consent"
        )

    async def exchange_code(self, code: str, redirect_uri: str) -> Dict[str, Any]:
        async with aiohttp.ClientSession() as session:
            async with session.post(
                "https://oauth2.googleapis.com/token",
                data={
                    "grant_type": "authorization_code",
                    "code": code,
                    "redirect_uri": redirect_uri,
                    "client_id": self.client_id,
                    "client_secret": self.client_secret
                }
            ) as response:
                if response.status != 200:
                    error_text = await response.text()
                    raise HTTPException(status_code=400, detail=f"Google token exchange failed: {error_text}")

                data = await response.json()
                return {
                    "access_token": data["access_token"],
                    "expires_in": data["expires_in"],
                    "refresh_token": data.get("refresh_token"),
                    "created_at": int(time.time())
                }

    async def refresh_token(self, refresh_token: str) -> Dict[str, Any]:
        async with aiohttp.ClientSession() as session:
            async with session.post(
                "https://oauth2.googleapis.com/token",
                data={
                    "grant_type": "refresh_token",
                    "refresh_token": refresh_token,
                    "client_id": self.client_id,
                    "client_secret": self.client_secret
                }
            ) as response:
                if response.status != 200:
                    error_text = await response.text()
                    raise HTTPException(status_code=400, detail=f"Google token refresh failed: {error_text}")

                data = await response.json()
                return {
                    "access_token": data["access_token"],
                    "expires_in": data["expires_in"],
                    "refresh_token": refresh_token,  # Google doesn't return a new refresh token
                    "created_at": int(time.time())
                }

    async def get_basic_profile(self, access_token: str) -> Dict[str, Any]:
        async with aiohttp.ClientSession() as session:
            async with session.get(
                "https://www.googleapis.com/oauth2/v2/userinfo",
                headers={"Authorization": f"Bearer {access_token}"}
            ) as response:
                if response.status != 200:
                    error_text = await response.text()
                    raise HTTPException(status_code=400, detail=f"Google profile retrieval failed: {error_text}")

                data = await response.json()
                return {
                    "id": data["id"],
                    "email": data["email"],
                    "name": data["name"],
                    "picture": data.get("picture")
                }

class MicrosoftAuthProvider(AuthProvider):
    def get_auth_url(self, redirect_uri: str, state: str) -> str:
        scope_str = "%20".join(self.scopes)
        return (
            f"https://login.microsoftonline.com/common/oauth2/v2.0/authorize"
            f"?response_type=code"
            f"&client_id={self.client_id}"
            f"&redirect_uri={redirect_uri}"
            f"&state={state}"
            f"&scope={scope_str}"
        )

    async def exchange_code(self, code: str, redirect_uri: str) -> Dict[str, Any]:
        async with aiohttp.ClientSession() as session:
            async with session.post(
                "https://login.microsoftonline.com/common/oauth2/v2.0/token",
                data={
                    "grant_type": "authorization_code",
                    "code": code,
                    "redirect_uri": redirect_uri,
                    "client_id": self.client_id,
                    "client_secret": self.client_secret
                }
            ) as response:
                if response.status != 200:
                    error_text = await response.text()
                    raise HTTPException(status_code=400, detail=f"Microsoft token exchange failed: {error_text}")

                data = await response.json()
                return {
                    "access_token": data["access_token"],
                    "expires_in": data["expires_in"],
                    "refresh_token": data.get("refresh_token"),
                    "created_at": int(time.time())
                }

    async def refresh_token(self, refresh_token: str) -> Dict[str, Any]:
        async with aiohttp.ClientSession() as session:
            async with session.post(
                "https://login.microsoftonline.com/common/oauth2/v2.0/token",
                data={
                    "grant_type": "refresh_token",
                    "refresh_token": refresh_token,
                    "client_id": self.client_id,
                    "client_secret": self.client_secret
                }
            ) as response:
                if response.status != 200:
                    error_text = await response.text()
                    raise HTTPException(status_code=400, detail=f"Microsoft token refresh failed: {error_text}")

                data = await response.json()
                return {
                    "access_token": data["access_token"],
                    "expires_in": data["expires_in"],
                    "refresh_token": data.get("refresh_token", refresh_token),
                    "created_at": int(time.time())
                }

    async def get_basic_profile(self, access_token: str) -> Dict[str, Any]:
        async with aiohttp.ClientSession() as session:
            async with session.get(
                "https://graph.microsoft.com/v1.0/me",
                headers={"Authorization": f"Bearer {access_token}"}
            ) as response:
                if response.status != 200:
                    error_text = await response.text()
                    raise HTTPException(status_code=400, detail=f"Microsoft profile retrieval failed: {error_text}")

                data = await response.json()
                return {
                    "id": data["id"],
                    "email": data["mail"] or data["userPrincipalName"],
                    "name": data["displayName"],
                    "first_name": data.get("givenName", ""),
                    "last_name": data.get("surname", "")
                }

class PlatformAuthService:
    def __init__(self):
        # Initialize auth providers with credentials from environment variables
        self.supported_platforms = {
            "linkedin": LinkedInAuthProvider(
                client_id=os.environ.get("LINKEDIN_CLIENT_ID", ""),
                client_secret=os.environ.get("LINKEDIN_CLIENT_SECRET", ""),
                scopes=["r_liteprofile", "r_emailaddress", "w_member_social"]
            ),
            "twitter": TwitterAuthProvider(
                client_id=os.environ.get("TWITTER_CLIENT_ID", ""),
                client_secret=os.environ.get("TWITTER_CLIENT_SECRET", ""),
                scopes=["tweet.read", "users.read", "dm.read"]
            ),
            "gmail": GoogleAuthProvider(
                client_id=os.environ.get("GOOGLE_CLIENT_ID", ""),
                client_secret=os.environ.get("GOOGLE_CLIENT_SECRET", ""),
                scopes=["https://www.googleapis.com/auth/gmail.readonly"]
            ),
            "outlook": MicrosoftAuthProvider(
                client_id=os.environ.get("MICROSOFT_CLIENT_ID", ""),
                client_secret=os.environ.get("MICROSOFT_CLIENT_SECRET", ""),
                scopes=["Mail.Read"]
            )
        }

    def get_auth_url(self, platform: str, user_id: str) -> str:
        """Generate authorization URL for the specified platform."""
        if platform not in self.supported_platforms:
            raise ValueError(f"Unsupported platform: {platform}")

        return self.supported_platforms[platform].get_auth_url(
            redirect_uri=f"{os.environ.get('API_BASE_URL', '')}/api/platforms/callback/{platform}",
            state=self._generate_state_token(platform, user_id)
        )

    async def handle_auth_callback(self, platform: str, code: str, state: str) -> Dict[str, Any]:
        """Process authorization callback from platform."""
        # Verify state token
        user_id = self._verify_state_token(state)
        if not user_id:
            raise HTTPException(status_code=400, detail="Invalid state token")

        # Exchange code for access token
        tokens = await self.supported_platforms[platform].exchange_code(
            code,
            redirect_uri=f"{os.environ.get('API_BASE_URL', '')}/api/platforms/callback/{platform}"
        )

        # Store tokens securely
        await self._store_user_tokens(user_id, platform, tokens)

        # Fetch basic profile information
        profile = await self.supported_platforms[platform].get_basic_profile(tokens["access_token"])

        return {
            "user_id": user_id,
            "platform": platform,
            "profile": profile,
            "status": "connected"
        }

    async def get_access_token(self, user_id: str, platform: str) -> str:
        """Get a valid access token for the specified platform."""
        # Retrieve stored tokens
        tokens = await self._get_user_tokens(user_id, platform)
        if not tokens:
            raise HTTPException(status_code=404, detail=f"No tokens found for platform: {platform}")

        # Check if token is expired
        expires_at = tokens["created_at"] + tokens["expires_in"]
        if time.time() > expires_at - 300:  # 5 minutes buffer
            # Refresh token
            if not tokens.get("refresh_token"):
                raise HTTPException(status_code=400, detail=f"No refresh token available for platform: {platform}")

            new_tokens = await self.supported_platforms[platform].refresh_token(tokens["refresh_token"])
            await self._store_user_tokens(user_id, platform, new_tokens)
            return new_tokens["access_token"]

        return tokens["access_token"]

    def _generate_state_token(self, platform: str, user_id: str) -> str:
        """Generate a secure state token for OAuth flow."""
        import hashlib
        import base64

        # In a real implementation, use a more secure method with encryption
        data = f"{platform}:{user_id}:{time.time()}"
        hashed = hashlib.sha256(data.encode()).digest()
        return base64.urlsafe_b64encode(hashed).decode()

    def _verify_state_token(self, state: str) -> Optional[str]:
        """Verify state token and extract user_id."""
        # In a real implementation, decrypt and validate the token
        # For now, we'll just simulate a fixed user ID
        return "user123"

    async def _store_user_tokens(self, user_id: str, platform: str, tokens: Dict[str, Any]):
        """Store user tokens securely."""
        # In a real implementation, store in a secure database with encryption
        logger.info(f"Stored tokens for user {user_id} and platform {platform}")

    async def _get_user_tokens(self, user_id: str, platform: str) -> Optional[Dict[str, Any]]:
        """Retrieve user tokens."""
        # In a real implementation, retrieve from a secure database
        # For now, we'll just simulate tokens
        return {
            "access_token": "mock_access_token",
            "refresh_token": "mock_refresh_token",
            "expires_in": 3600,
            "created_at": int(time.time()) - 1800  # Created 30 minutes ago
        }

# Singleton instance
platform_auth_service = PlatformAuthService()
