"""
GitHub REST API client with rate limiting and error handling.
"""

import base64
import logging
import os
import time
from typing import Any, Dict, List, Optional

import requests


class GitHubAPIError(Exception):
    """Exception raised for GitHub API errors."""
    pass


class RateLimitExceeded(GitHubAPIError):
    """Exception raised when rate limit is exceeded."""
    pass


class GitHubClient:
    """
    GitHub REST API client with automatic token handling and rate limiting.
    """
    
    BASE_URL = "https://api.github.com"
    
    def __init__(self, token: Optional[str] = None):
        """
        Initialize GitHub client.
        
        Args:
            token: GitHub API token (defaults to GITHUB_TOKEN env var)
        """
        self.token = token or os.environ.get('GITHUB_TOKEN')
        self.logger = logging.getLogger("clone_tracker.github")
        self.session = requests.Session()
        
        # Set default headers
        self.session.headers.update({
            'Accept': 'application/vnd.github+json',
            'X-GitHub-Api-Version': '2022-11-28'
        })
        
        if self.token:
            self.session.headers['Authorization'] = f'Bearer {self.token}'
            self.logger.info("GitHub client initialized with token")
        else:
            self.logger.warning("GitHub client initialized without token (rate limits will be lower)")
    
    def _handle_rate_limit(self, response: requests.Response) -> None:
        """
        Handle rate limiting based on response headers.
        
        Args:
            response: Response object
            
        Raises:
            RateLimitExceeded: If rate limit is exceeded
        """
        remaining = int(response.headers.get('X-RateLimit-Remaining', 1))
        reset_time = int(response.headers.get('X-RateLimit-Reset', 0))
        
        if remaining == 0:
            wait_time = max(reset_time - time.time(), 0) + 1
            self.logger.warning(f"Rate limit exceeded. Waiting {wait_time:.0f} seconds")
            
            if wait_time > 300:  # More than 5 minutes
                raise RateLimitExceeded(f"Rate limit exceeded. Reset in {wait_time:.0f} seconds")
            
            time.sleep(wait_time)
        elif remaining < 10:
            self.logger.warning(f"Rate limit low: {remaining} requests remaining")
    
    def _request(
        self,
        method: str,
        endpoint: str,
        params: Optional[Dict] = None,
        data: Optional[Dict] = None,
        max_retries: int = 3
    ) -> Any:
        """
        Make HTTP request with exponential backoff retry.
        
        Args:
            method: HTTP method
            endpoint: API endpoint
            params: Query parameters
            data: Request body
            max_retries: Maximum retry attempts
            
        Returns:
            Response data
            
        Raises:
            GitHubAPIError: If request fails after retries
        """
        url = f"{self.BASE_URL}/{endpoint.lstrip('/')}"
        
        for attempt in range(max_retries):
            try:
                response = self.session.request(
                    method=method,
                    url=url,
                    params=params,
                    json=data,
                    timeout=30
                )
                
                # Handle rate limiting
                self._handle_rate_limit(response)
                
                # Check for errors
                if response.status_code == 404:
                    raise GitHubAPIError(f"Resource not found: {endpoint}")
                elif response.status_code == 403:
                    if 'rate limit' in response.text.lower():
                        raise RateLimitExceeded("Rate limit exceeded")
                    raise GitHubAPIError(f"Forbidden: {response.text}")
                elif response.status_code >= 400:
                    raise GitHubAPIError(
                        f"HTTP {response.status_code}: {response.text}"
                    )
                
                response.raise_for_status()
                
                # Return JSON response
                if response.content:
                    return response.json()
                return None
                
            except requests.RequestException as e:
                if attempt == max_retries - 1:
                    raise GitHubAPIError(f"Request failed after {max_retries} attempts: {e}")
                
                # Exponential backoff
                wait_time = 2 ** attempt
                self.logger.warning(f"Request failed, retrying in {wait_time}s: {e}")
                time.sleep(wait_time)
        
        raise GitHubAPIError("Request failed after all retries")
    
    def get_repo(self, owner: str, repo: str) -> Dict[str, Any]:
        """
        Get repository information.
        
        Args:
            owner: Repository owner
            repo: Repository name
            
        Returns:
            Repository data
        """
        self.logger.debug(f"Getting repo: {owner}/{repo}")
        return self._request('GET', f'/repos/{owner}/{repo}')
    
    def list_forks(
        self,
        owner: str,
        repo: str,
        per_page: int = 100,
        max_pages: int = 10
    ) -> List[Dict[str, Any]]:
        """
        List repository forks.
        
        Args:
            owner: Repository owner
            repo: Repository name
            per_page: Results per page (max 100)
            max_pages: Maximum pages to fetch
            
        Returns:
            List of fork data
        """
        self.logger.debug(f"Listing forks for: {owner}/{repo}")
        forks = []
        
        for page in range(1, max_pages + 1):
            params = {'per_page': min(per_page, 100), 'page': page}
            result = self._request('GET', f'/repos/{owner}/{repo}/forks', params=params)
            
            if not result:
                break
            
            forks.extend(result)
            
            if len(result) < per_page:
                break
        
        self.logger.info(f"Found {len(forks)} forks for {owner}/{repo}")
        return forks
    
    def search_code(
        self,
        query: str,
        per_page: int = 100,
        max_pages: int = 5
    ) -> List[Dict[str, Any]]:
        """
        Search code across GitHub.
        
        Args:
            query: Search query
            per_page: Results per page (max 100)
            max_pages: Maximum pages to fetch
            
        Returns:
            List of code search results
        """
        self.logger.debug(f"Searching code: {query}")
        results = []
        
        for page in range(1, max_pages + 1):
            params = {'q': query, 'per_page': min(per_page, 100), 'page': page}
            
            try:
                data = self._request('GET', '/search/code', params=params)
                items = data.get('items', [])
                
                if not items:
                    break
                
                results.extend(items)
                
                if len(items) < per_page:
                    break
                    
            except GitHubAPIError as e:
                self.logger.warning(f"Code search failed: {e}")
                break
        
        self.logger.info(f"Found {len(results)} code search results for: {query}")
        return results
    
    def get_file_contents(
        self,
        owner: str,
        repo: str,
        path: str,
        ref: Optional[str] = None
    ) -> Optional[bytes]:
        """
        Get file contents from repository.
        
        Args:
            owner: Repository owner
            repo: Repository name
            path: File path
            ref: Git reference (branch, tag, commit)
            
        Returns:
            File contents as bytes, or None if not found
        """
        self.logger.debug(f"Getting file: {owner}/{repo}/{path}")
        
        params = {}
        if ref:
            params['ref'] = ref
        
        try:
            data = self._request('GET', f'/repos/{owner}/{repo}/contents/{path}', params=params)
            
            if isinstance(data, dict) and 'content' in data:
                # Decode base64 content
                content = data['content']
                return base64.b64decode(content)
            
            return None
            
        except GitHubAPIError as e:
            self.logger.debug(f"Failed to get file {owner}/{repo}/{path}: {e}")
            return None
    
    def get_readme(self, owner: str, repo: str) -> Optional[str]:
        """
        Get repository README content.
        
        Args:
            owner: Repository owner
            repo: Repository name
            
        Returns:
            README content as string, or None if not found
        """
        self.logger.debug(f"Getting README: {owner}/{repo}")
        
        try:
            data = self._request('GET', f'/repos/{owner}/{repo}/readme')
            
            if isinstance(data, dict) and 'content' in data:
                content = base64.b64decode(data['content'])
                return content.decode('utf-8', errors='ignore')
            
            return None
            
        except GitHubAPIError:
            return None
