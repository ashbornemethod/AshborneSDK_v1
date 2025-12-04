"""
Alert notification system for clone detection.
"""

import json
import logging
import os
from typing import Dict, List, Optional

import requests


class AlertNotifier:
    """
    Send alerts via webhooks when high-similarity repositories are detected.
    """
    
    def __init__(self):
        """Initialize alert notifier."""
        self.slack_webhook = os.environ.get('SLACK_WEBHOOK_URL')
        self.alert_webhook = os.environ.get('ALERT_WEBHOOK_URL')
        self.logger = logging.getLogger("clone_tracker.alerts")
        
        if not self.slack_webhook and not self.alert_webhook:
            self.logger.info("No webhook URLs configured, alerts disabled")
    
    def send_alert(self, repos: List[Dict], alert_type: str = "clone_detected") -> None:
        """
        Send alert for detected repositories.
        
        Args:
            repos: List of repository data
            alert_type: Type of alert
        """
        if not repos:
            return
        
        # Filter for high-severity repos
        high_severity = [r for r in repos if r.get('severity') == 'HIGH']
        
        if not high_severity:
            self.logger.debug("No high-severity repos to alert on")
            return
        
        self.logger.info(f"Sending alert for {len(high_severity)} high-severity repos")
        
        # Send to Slack
        if self.slack_webhook:
            self._send_slack_alert(high_severity, alert_type)
        
        # Send to generic webhook
        if self.alert_webhook:
            self._send_generic_alert(high_severity, alert_type)
    
    def _send_slack_alert(self, repos: List[Dict], alert_type: str) -> None:
        """
        Send alert to Slack webhook.
        
        Args:
            repos: List of repository data
            alert_type: Type of alert
        """
        try:
            # Build Slack message
            text = f"🚨 *Clone Detection Alert: {alert_type}*\n\n"
            text += f"Detected {len(repos)} high-similarity repositories:\n\n"
            
            for repo in repos[:5]:  # Limit to top 5
                text += f"• *{repo['owner']}/{repo['repo']}* "
                text += f"(Score: {repo['score']}%, Severity: {repo['severity']})\n"
                text += f"  URL: {repo['repo_url']}\n"
                text += f"  Matched files: {len(repo.get('matched_files', []))}\n\n"
            
            if len(repos) > 5:
                text += f"\n_...and {len(repos) - 5} more repositories_"
            
            payload = {
                "text": text,
                "username": "Clone Tracker",
                "icon_emoji": ":warning:"
            }
            
            response = requests.post(
                self.slack_webhook,
                json=payload,
                timeout=10
            )
            response.raise_for_status()
            
            self.logger.info("Slack alert sent successfully")
            
        except Exception as e:
            self.logger.warning(f"Failed to send Slack alert: {e}")
    
    def _send_generic_alert(self, repos: List[Dict], alert_type: str) -> None:
        """
        Send alert to generic webhook.
        
        Args:
            repos: List of repository data
            alert_type: Type of alert
        """
        try:
            payload = {
                "alert_type": alert_type,
                "timestamp": repos[0].get('created_at') if repos else None,
                "count": len(repos),
                "repositories": [
                    {
                        "owner": r['owner'],
                        "repo": r['repo'],
                        "url": r['repo_url'],
                        "score": r['score'],
                        "severity": r['severity'],
                        "matched_files": len(r.get('matched_files', []))
                    }
                    for r in repos
                ]
            }
            
            response = requests.post(
                self.alert_webhook,
                json=payload,
                headers={'Content-Type': 'application/json'},
                timeout=10
            )
            response.raise_for_status()
            
            self.logger.info("Generic webhook alert sent successfully")
            
        except Exception as e:
            self.logger.warning(f"Failed to send generic alert: {e}")
    
    def send_new_fork_alert(self, forks: List[Dict]) -> None:
        """
        Send alert for newly detected forks.
        
        Args:
            forks: List of new fork data
        """
        if not forks:
            return
        
        self.logger.info(f"Sending alert for {len(forks)} new forks")
        self.send_alert(forks, alert_type="new_forks_detected")
