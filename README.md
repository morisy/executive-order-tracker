# White House Executive Orders Monitor

This DocumentCloud Add-On automatically monitors the White House Presidential Actions page for new Executive Orders, converts them to PDFs with metadata, and backs them up to Internet Archive with optional IPFS/Filecoin storage.

## Features

- **Automatic Monitoring**: Regularly checks whitehouse.gov for new Executive Orders
- **PDF Generation**: Creates well-formatted PDFs with embedded metadata
- **State Tracking**: Remembers which orders have been processed to avoid duplicates
- **DocumentCloud Integration**: Uploads PDFs with proper metadata and searchable text
- **Internet Archive Backup**: Optionally triggers archival to Internet Archive
- **IPFS/Filecoin Storage**: Optionally pushes documents to decentralized storage via IPFS and Filecoin
- **Bluesky Integration**: Posts announcements about new Executive Orders to Bluesky
- **Configurable Intervals**: Set how often to check for new orders

## Configuration

The add-on supports the following configuration options:

- **Check Interval** (default: 24 hours): How often to check for new orders
- **Include Proclamations** (default: false): Also monitor Presidential Proclamations
- **Bluesky Handle**: Your Bluesky account handle for posting updates
- **Bluesky Password**: Your Bluesky account password (stored securely)
- **Archive to Internet Archive** (default: true): Automatically archive PDFs to Internet Archive
- **Upload to IPFS/Filecoin** (default: true): Push documents to decentralized storage (WARNING: This is permanent and cannot be undone)

## Usage

1. Install the add-on in your DocumentCloud account
2. Configure the settings according to your needs
3. The add-on will run on your chosen schedule (hourly, daily, or weekly)
4. New Executive Orders will appear in your DocumentCloud account
5. If configured, announcements will be posted to Bluesky

## How It Works

1. **Scraping**: The add-on visits the White House Presidential Actions page
2. **Change Detection**: Compares current orders against previously processed ones
3. **PDF Creation**: Generates PDFs with metadata for new orders
4. **Upload**: Uploads PDFs to DocumentCloud with full text and metadata
5. **Archival**: Optionally triggers Internet Archive Export Add-On for backup
   - If enabled, documents are uploaded to Internet Archive
   - If IPFS/Filecoin is enabled, documents are also pushed to decentralized storage
6. **Social Media**: Posts to Bluesky if credentials are provided

## Metadata Included

Each PDF includes:
- Original URL from whitehouse.gov
- Scrape timestamp
- Executive Order number and title
- Publication date
- Full text content
- Source attribution

## Bluesky Posts

When configured, the add-on posts to Bluesky with:
- Executive Order title and number
- Link to DocumentCloud PDF
- Link to original White House page
- Relevant hashtags (#ExecutiveOrder #WhiteHouse #GovDocs #Transparency)

## Development

To modify or test this add-on locally:

```bash
# Install dependencies
pip install -r requirements.txt

# Run locally
python main.py
```

## Error Handling

The add-on includes robust error handling for:
- Network timeouts and failures
- Changes to White House website structure
- DocumentCloud API errors
- Bluesky posting failures

All errors are logged and the add-on continues processing remaining orders.

## Privacy and Security

- Bluesky credentials are stored securely in DocumentCloud's system
- The add-on respects rate limits and robots.txt
- No personal data is collected or stored

## Contributing

This add-on is open source. Contributions are welcome!

## License

This add-on is released under the MIT License.