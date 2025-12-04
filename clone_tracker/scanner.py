"""
Repository scanning logic for clone detection.
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Set

from .github_client import GitHubClient, GitHubAPIError
from .similarity import (
    check_name_similarity,
    compute_sha256,
    compute_similarity_score,
    extract_filenames_from_signatures,
    readme_fingerprint_similarity
)


class RepositoryScanner:
    """
    Scans GitHub for potential clones of a canonical repository.
    """
    
    def __init__(
        self,
        github_client: GitHubClient,
        canonical_repo_name: str = "AshborneSDK_v1"
    ):
        """
        Initialize scanner.
        
        Args:
            github_client: GitHub API client
            canonical_repo_name: Name of canonical repository
        """
        self.client = github_client
        self.canonical_repo_name = canonical_repo_name
        self.logger = logging.getLogger("clone_tracker.scanner")
    
    def scan_for_clones(
        self,
        canonical_signatures: Dict[str, Dict],
        canonical_owner: str = "ashbornemethod",
        max_search_results: int = 100
    ) -> Dict[str, List[Dict]]:
        """
        Scan GitHub for potential clones.
        
        Args:
            canonical_signatures: Canonical file signatures
            canonical_owner: Owner of canonical repository
            max_search_results: Maximum search results to process
            
        Returns:
            Dictionary with 'forks' and 'suspicious_repos' lists
        """
        self.logger.info("Starting clone scan")
        
        results = {
            'forks': [],
            'suspicious_repos': [],
            'scan_timestamp': datetime.now().isoformat()
        }
        
        # 1. Find and analyze forks
        try:
            forks = self._find_forks(canonical_owner, self.canonical_repo_name)
            results['forks'] = self._analyze_repositories(
                forks, canonical_signatures, canonical_owner
            )
            self.logger.info(f"Analyzed {len(results['forks'])} forks")
        except Exception as e:
            self.logger.error(f"Failed to analyze forks: {e}")
        
        # 2. Search for potential clones via code search
        try:
            candidates = self._search_for_candidates(
                canonical_signatures, canonical_owner, max_search_results
            )
            results['suspicious_repos'] = self._analyze_repositories(
                candidates, canonical_signatures, canonical_owner
            )
            self.logger.info(f"Analyzed {len(results['suspicious_repos'])} suspicious repos")
        except Exception as e:
            self.logger.error(f"Failed to search for candidates: {e}")
        
        # Filter and sort suspicious repos
        results['suspicious_repos'] = [
            repo for repo in results['suspicious_repos']
            if repo.get('score', 0) > 30  # Minimum threshold
        ]
        results['suspicious_repos'].sort(key=lambda x: x.get('score', 0), reverse=True)
        
        return results
    
    def _find_forks(self, owner: str, repo: str) -> List[Dict]:
        """
        Find official forks of the repository.
        
        Args:
            owner: Repository owner
            repo: Repository name
            
        Returns:
            List of fork metadata
        """
        self.logger.info(f"Finding forks of {owner}/{repo}")
        
        try:
            forks = self.client.list_forks(owner, repo, per_page=100, max_pages=5)
            return [
                {
                    'owner': fork['owner']['login'],
                    'repo': fork['name'],
                    'full_name': fork['full_name'],
                    'url': fork['html_url'],
                    'created_at': fork.get('created_at'),
                    'forks_count': fork.get('forks_count', 0),
                    'stargazers_count': fork.get('stargazers_count', 0),
                    'watchers_count': fork.get('watchers_count', 0)
                }
                for fork in forks
            ]
        except GitHubAPIError as e:
            self.logger.warning(f"Failed to fetch forks: {e}")
            return []
    
    def _search_for_candidates(
        self,
        canonical_signatures: Dict[str, Dict],
        exclude_owner: str,
        max_results: int = 100
    ) -> List[Dict]:
        """
        Search for potential clone repositories via code search.
        
        Args:
            canonical_signatures: Canonical signatures
            exclude_owner: Owner to exclude from results
            max_results: Maximum results to return
            
        Returns:
            List of candidate repository metadata
        """
        self.logger.info("Searching for clone candidates")
        
        candidates = {}
        filenames = extract_filenames_from_signatures(canonical_signatures)
        
        # Search for unique filenames
        unique_files = [f for f in filenames if f not in ['__init__.py', 'setup.py', 'README.md']]
        search_files = unique_files[:5]  # Limit searches to avoid rate limits
        
        for filename in search_files:
            try:
                # Search for filename
                query = f'filename:{filename}'
                results = self.client.search_code(query, per_page=30, max_pages=2)
                
                for item in results:
                    repo_data = item.get('repository', {})
                    repo_owner = repo_data.get('owner', {}).get('login')
                    repo_name = repo_data.get('name')
                    
                    # Skip canonical repo
                    if repo_owner == exclude_owner and repo_name == self.canonical_repo_name:
                        continue
                    
                    # Add to candidates
                    repo_key = f"{repo_owner}/{repo_name}"
                    if repo_key not in candidates:
                        candidates[repo_key] = {
                            'owner': repo_owner,
                            'repo': repo_name,
                            'full_name': repo_data.get('full_name'),
                            'url': repo_data.get('html_url'),
                            'created_at': repo_data.get('created_at'),
                            'forks_count': repo_data.get('forks_count', 0),
                            'stargazers_count': repo_data.get('stargazers_count', 0),
                            'watchers_count': repo_data.get('watchers_count', 0)
                        }
                
                if len(candidates) >= max_results:
                    break
                    
            except Exception as e:
                self.logger.warning(f"Search failed for {filename}: {e}")
                continue
        
        self.logger.info(f"Found {len(candidates)} candidate repositories")
        return list(candidates.values())
    
    def _analyze_repositories(
        self,
        repos: List[Dict],
        canonical_signatures: Dict[str, Dict],
        canonical_owner: str
    ) -> List[Dict]:
        """
        Analyze repositories for similarity to canonical repo.
        
        Args:
            repos: List of repository metadata
            canonical_signatures: Canonical signatures
            canonical_owner: Owner of canonical repository
            
        Returns:
            List of analyzed repository data with scores
        """
        analyzed = []
        
        for repo_data in repos:
            try:
                analysis = self._analyze_single_repo(
                    repo_data, canonical_signatures, canonical_owner
                )
                analyzed.append(analysis)
            except Exception as e:
                self.logger.warning(
                    f"Failed to analyze {repo_data.get('full_name')}: {e}"
                )
                continue
        
        return analyzed
    
    def _analyze_single_repo(
        self,
        repo_data: Dict,
        canonical_signatures: Dict[str, Dict],
        canonical_owner: str
    ) -> Dict:
        """
        Analyze a single repository.
        
        Args:
            repo_data: Repository metadata
            canonical_signatures: Canonical signatures
            canonical_owner: Owner of canonical repository
            
        Returns:
            Analysis results with score and matched files
        """
        owner = repo_data['owner']
        repo = repo_data['repo']
        
        self.logger.debug(f"Analyzing repository: {owner}/{repo}")
        
        matched_files = []
        
        # Check files from canonical signatures
        for canonical_path, sig_data in list(canonical_signatures.items())[:20]:  # Limit to avoid rate limits
            try:
                # Try to get file content
                content = self.client.get_file_contents(owner, repo, canonical_path)
                
                if content:
                    # Compute hash and compare
                    file_hash = compute_sha256(content)
                    sha_match = file_hash == sig_data['sha256']
                    
                    matched_files.append({
                        'path': canonical_path,
                        'canonical_path': canonical_path,
                        'sha_match': sha_match,
                        'hash': file_hash
                    })
                    
            except Exception as e:
                self.logger.debug(f"Failed to check file {canonical_path} in {owner}/{repo}: {e}")
                continue
        
        # Compute similarity score
        score = compute_similarity_score(canonical_signatures, matched_files)
        
        # Check heuristics
        heuristics = self._check_heuristics(repo_data, canonical_owner)
        
        return {
            'owner': owner,
            'repo': repo,
            'repo_url': repo_data.get('url', f"https://github.com/{owner}/{repo}"),
            'created_at': repo_data.get('created_at'),
            'forks_count': repo_data.get('forks_count', 0),
            'stargazers_count': repo_data.get('stargazers_count', 0),
            'watchers_count': repo_data.get('watchers_count', 0),
            'score': round(score, 2),
            'severity': 'HIGH' if score > 70 else 'MEDIUM' if score > 50 else 'LOW',
            'matched_files': matched_files,
            'heuristics': heuristics
        }
    
    def _check_heuristics(self, repo_data: Dict, canonical_owner: str) -> Dict:
        """
        Check heuristic flags for suspicious patterns.
        
        Args:
            repo_data: Repository metadata
            canonical_owner: Owner of canonical repository
            
        Returns:
            Dictionary of heuristic flags
        """
        heuristics = {}
        
        # Check if recently created (within last 60 days)
        try:
            created_at = repo_data.get('created_at')
            if created_at:
                created_date = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
                age_days = (datetime.now().astimezone() - created_date).days
                heuristics['recent_creation'] = age_days < 60
            else:
                heuristics['recent_creation'] = False
        except Exception:
            heuristics['recent_creation'] = False
        
        # Check name similarity
        repo_name = repo_data.get('repo', '')
        heuristics['suspicious_name_similarity'] = check_name_similarity(
            self.canonical_repo_name, repo_name, threshold=0.6
        )
        
        return heuristics
