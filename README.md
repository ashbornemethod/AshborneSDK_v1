# AshborneSDK_v1
The AshborneSDK_v1 is a modular, production-grade AI Governance and Licensing SDK. It includes licensing enforcement, persona routing, output modulation, watermark verification, and AWS-native infrastructure hooks. Designed for integration into AI applications and creator platforms.

## Clone Tracker

The Clone Tracker is a comprehensive repository clone detection system that monitors GitHub for forks, clones, mirrors, and derivative repositories. It uses multiple detection methods including:

- **GitHub REST API**: Official fork tracking and repository metadata
- **Global Code Search**: Filename and content-based detection across all public repositories
- **File Signature Hashing**: SHA-256 hash comparison for exact file matching
- **Pattern Matching**: README fingerprinting and filename similarity detection
- **Heuristics**: Detection of suspicious patterns like recent creation or similar naming

### Installation

Install the required dependencies:

```bash
pip install -r requirements.txt
```

### Configuration

The Clone Tracker can be configured using environment variables:

- `GITHUB_TOKEN` (recommended): GitHub personal access token for higher API rate limits
- `SLACK_WEBHOOK_URL` (optional): Slack webhook URL for alert notifications
- `ALERT_WEBHOOK_URL` (optional): Generic webhook URL for custom alert integrations

Create a `.env` file from the example:

```bash
cp .env.example .env
# Edit .env and add your tokens
```

### Usage

#### Running a Scan

Perform a complete clone detection scan:

```bash
python -m clone_tracker scan
```

Options:
- `--output-dir, -o`: Output directory for results (default: `data`)
- `--force, -f`: Force regeneration of file signatures
- `--max-results, -m`: Maximum search results to process (default: 100)

#### Viewing Reports

Generate and display a summary report from scan results:

```bash
python -m clone_tracker report
```

Options:
- `--output-dir, -o`: Directory containing scan results (default: `data`)

#### Watching for Changes

Monitor for new clones continuously:

```bash
python -m clone_tracker watch --interval 10
```

Options:
- `--interval, -i`: Scan interval in minutes (default: 10)
- `--output-dir, -o`: Output directory for results (default: `data`)
- `--once`: Run a single scan and exit (no continuous monitoring)

#### Exporting Results

Export scan results to different formats:

```bash
# Export to JSON
python -m clone_tracker export --format json

# Export to CSV
python -m clone_tracker export --format csv --export-dir exports
```

Options:
- `--output-dir, -o`: Directory containing scan results (default: `data`)
- `--format, -f`: Export format - `json` or `csv` (default: `json`)
- `--export-dir, -e`: Directory to export to (default: same as output-dir)

### Output Files

The Clone Tracker generates several output files in the `data/` directory:

- `signatures.json`: Canonical file signatures from the SDK
- `scan_results.json`: Complete scan results with all findings
- `forks.json`: Official forks detected via GitHub API
- `suspicious_repos.json`: Repositories with high similarity scores

Log files are stored in `logs/clone_tracker.log` with automatic rotation (5MB max, 3 backups).

### GitHub Actions Workflow

The repository includes a nightly GitHub Actions workflow that automatically runs clone detection scans. Results are uploaded as artifacts for review.

The workflow runs at 2 AM UTC daily and can also be triggered manually from the Actions tab.

### Alert Notifications

When high-similarity repositories are detected (score > 70%), the Clone Tracker can send notifications via:

1. **Slack**: Set `SLACK_WEBHOOK_URL` environment variable
2. **Generic Webhook**: Set `ALERT_WEBHOOK_URL` environment variable

Alerts include repository details, similarity scores, and matched files.

### Local Development

To test the Clone Tracker locally with authentication:

```bash
# Set your GitHub token
export GITHUB_TOKEN="your_github_token_here"

# Run a scan
python -m clone_tracker scan

# View the report
python -m clone_tracker report
```

For testing webhooks:

```bash
# Set webhook URLs
export SLACK_WEBHOOK_URL="https://hooks.slack.com/services/YOUR/WEBHOOK/URL"
export ALERT_WEBHOOK_URL="https://your-webhook-url.com/alert"

# Run scan with alerts enabled
python -m clone_tracker scan
```
