"""
Core orchestration for clone detection scanning.
"""

import logging
import os
from typing import Dict, List, Optional

from .alerts import AlertNotifier
from .github_client import GitHubClient
from .scanner import RepositoryScanner
from .signatures import generate_signatures, load_signatures
from .utils import load_json, safe_write_json, setup_logger


class CloneTrackerCore:
    """
    Core orchestration for clone detection and tracking.
    """
    
    def __init__(
        self,
        output_dir: str = "data",
        canonical_owner: str = "ashbornemethod",
        canonical_repo: str = "AshborneSDK_v1"
    ):
        """
        Initialize clone tracker core.
        
        Args:
            output_dir: Directory for output files
            canonical_owner: Owner of canonical repository
            canonical_repo: Name of canonical repository
        """
        self.output_dir = output_dir
        self.canonical_owner = canonical_owner
        self.canonical_repo = canonical_repo
        
        # Set up logging
        self.logger = setup_logger("clone_tracker")
        
        # Initialize components
        self.github_client = GitHubClient()
        self.scanner = RepositoryScanner(self.github_client, canonical_repo)
        self.notifier = AlertNotifier()
        
        self.logger.info("Clone Tracker initialized")
    
    def run_scan(
        self,
        force_regenerate_signatures: bool = False,
        max_search_results: int = 100
    ) -> Dict:
        """
        Run complete clone detection scan.
        
        Args:
            force_regenerate_signatures: Force regeneration of signatures
            max_search_results: Maximum search results to process
            
        Returns:
            Scan results dictionary
        """
        self.logger.info("Starting clone detection scan")
        
        try:
            # Step 1: Load or generate signatures
            signatures = self._get_signatures(force_regenerate_signatures)
            
            if not signatures:
                raise ValueError("No signatures available. Cannot proceed with scan.")
            
            # Step 2: Run scan
            results = self.scanner.scan_for_clones(
                signatures,
                canonical_owner=self.canonical_owner,
                max_search_results=max_search_results
            )
            
            # Step 3: Save results
            self._save_results(results)
            
            # Step 4: Send alerts for high-severity findings
            self._send_alerts(results)
            
            self.logger.info("Clone detection scan completed successfully")
            return results
            
        except Exception as e:
            self.logger.error(f"Scan failed: {e}", exc_info=True)
            raise
    
    def _get_signatures(self, force_regenerate: bool = False) -> Dict[str, Dict]:
        """
        Load or generate canonical signatures.
        
        Args:
            force_regenerate: Force regeneration of signatures
            
        Returns:
            Dictionary of signatures
        """
        signatures_file = os.path.join(self.output_dir, "signatures.json")
        
        # Try to load existing signatures
        if not force_regenerate and os.path.exists(signatures_file):
            try:
                self.logger.info("Loading existing signatures")
                return load_signatures(signatures_file)
            except Exception as e:
                self.logger.warning(f"Failed to load signatures: {e}")
        
        # Generate new signatures
        self.logger.info("Generating new signatures")
        return generate_signatures(
            root_dir="sdk",
            output_file=signatures_file,
            skip_binary=True
        )
    
    def _save_results(self, results: Dict) -> None:
        """
        Save scan results to data files.
        
        Args:
            results: Scan results dictionary
        """
        # Save complete scan results
        scan_results_file = os.path.join(self.output_dir, "scan_results.json")
        safe_write_json(results, scan_results_file, create_backup_flag=True)
        self.logger.info(f"Scan results saved to {scan_results_file}")
        
        # Save forks separately
        if results.get('forks'):
            forks_file = os.path.join(self.output_dir, "forks.json")
            forks_data = {
                'timestamp': results.get('scan_timestamp'),
                'count': len(results['forks']),
                'forks': results['forks']
            }
            safe_write_json(forks_data, forks_file, create_backup_flag=True)
            self.logger.info(f"Forks saved to {forks_file}")
        
        # Save suspicious repos separately
        if results.get('suspicious_repos'):
            suspicious_file = os.path.join(self.output_dir, "suspicious_repos.json")
            suspicious_data = {
                'timestamp': results.get('scan_timestamp'),
                'count': len(results['suspicious_repos']),
                'repositories': results['suspicious_repos']
            }
            safe_write_json(suspicious_data, suspicious_file, create_backup_flag=True)
            self.logger.info(f"Suspicious repos saved to {suspicious_file}")
    
    def _send_alerts(self, results: Dict) -> None:
        """
        Send alerts for high-severity findings.
        
        Args:
            results: Scan results dictionary
        """
        try:
            # Alert on suspicious repos
            if results.get('suspicious_repos'):
                self.notifier.send_alert(
                    results['suspicious_repos'],
                    alert_type="clone_detected"
                )
            
            # Alert on new forks
            if results.get('forks'):
                high_score_forks = [
                    f for f in results['forks']
                    if f.get('severity') == 'HIGH'
                ]
                if high_score_forks:
                    self.notifier.send_new_fork_alert(high_score_forks)
                    
        except Exception as e:
            self.logger.warning(f"Failed to send alerts: {e}")
    
    def generate_report(self) -> str:
        """
        Generate a summary report from scan results.
        
        Returns:
            Report text
        """
        scan_results_file = os.path.join(self.output_dir, "scan_results.json")
        
        if not os.path.exists(scan_results_file):
            return "No scan results found. Run a scan first with: python -m clone_tracker scan"
        
        results = load_json(scan_results_file, default={})
        
        report = []
        report.append("=" * 60)
        report.append("CLONE DETECTION REPORT")
        report.append("=" * 60)
        report.append(f"Scan timestamp: {results.get('scan_timestamp', 'N/A')}")
        report.append("")
        
        # Forks summary
        forks = results.get('forks', [])
        report.append(f"Total forks found: {len(forks)}")
        
        if forks:
            high_score_forks = [f for f in forks if f.get('severity') == 'HIGH']
            report.append(f"  High-severity forks: {len(high_score_forks)}")
            report.append("")
        
        # Suspicious repos summary
        suspicious = results.get('suspicious_repos', [])
        report.append(f"Total suspicious repositories: {len(suspicious)}")
        
        if suspicious:
            high_severity = [r for r in suspicious if r.get('severity') == 'HIGH']
            medium_severity = [r for r in suspicious if r.get('severity') == 'MEDIUM']
            
            report.append(f"  High-severity: {len(high_severity)}")
            report.append(f"  Medium-severity: {len(medium_severity)}")
            report.append("")
            
            # Top suspicious repos
            if suspicious:
                report.append("Top suspicious repositories:")
                report.append("-" * 60)
                
                for repo in suspicious[:10]:
                    report.append(f"\n{repo['owner']}/{repo['repo']}")
                    report.append(f"  Score: {repo['score']}% | Severity: {repo['severity']}")
                    report.append(f"  URL: {repo['repo_url']}")
                    report.append(f"  Matched files: {len(repo.get('matched_files', []))}")
                    
                    heuristics = repo.get('heuristics', {})
                    flags = []
                    if heuristics.get('recent_creation'):
                        flags.append("Recently created")
                    if heuristics.get('suspicious_name_similarity'):
                        flags.append("Similar name")
                    
                    if flags:
                        report.append(f"  Flags: {', '.join(flags)}")
        
        report.append("")
        report.append("=" * 60)
        
        return "\n".join(report)
    
    def compare_scans(self, previous_results: Dict, current_results: Dict) -> Dict:
        """
        Compare two scan results to find differences.
        
        Args:
            previous_results: Previous scan results
            current_results: Current scan results
            
        Returns:
            Dictionary of differences
        """
        differences = {
            'new_forks': [],
            'new_suspicious_repos': [],
            'increased_severity': []
        }
        
        # Get previous repo identifiers
        prev_forks = {f"{r['owner']}/{r['repo']}" for r in previous_results.get('forks', [])}
        prev_suspicious = {f"{r['owner']}/{r['repo']}" for r in previous_results.get('suspicious_repos', [])}
        
        # Check for new forks
        for fork in current_results.get('forks', []):
            fork_id = f"{fork['owner']}/{fork['repo']}"
            if fork_id not in prev_forks:
                differences['new_forks'].append(fork)
        
        # Check for new suspicious repos
        for repo in current_results.get('suspicious_repos', []):
            repo_id = f"{repo['owner']}/{repo['repo']}"
            if repo_id not in prev_suspicious:
                differences['new_suspicious_repos'].append(repo)
        
        self.logger.info(
            f"Scan comparison: {len(differences['new_forks'])} new forks, "
            f"{len(differences['new_suspicious_repos'])} new suspicious repos"
        )
        
        return differences
