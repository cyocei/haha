# Keser Username Search

A powerful username search tool that helps you find username availability across multiple platforms.

## Features

- Fast and efficient username searching
- Beautiful dark mode interface
- Real-time progress tracking
- Parallel request processing
- Rate limiting to prevent API abuse
- Cross-platform compatibility

## Project Structure

- `server.py` - Flask backend API
- `requirements.txt` - Python dependencies
- `keser.html` - Frontend interface
- `sites.json` - (Required) List of sites to check

## Setup

1. Install Python dependencies:
```bash
pip install -r requirements.txt
```

2. Create a `sites.json` file with the following structure:
```json
{
  "sites": [
    {
      "name": "Site Name",
      "uri_check": "https://example.com/{account}",
      "e_string": "Error string that indicates username exists",
      "m_string": "String that must be present for valid response",
      "cat": "Category"
    }
  ]
}
```

3. Run the server:
```bash
python server.py
```

4. Open `keser.html` in a web browser

## Deployment

The API is designed to be deployed on Render.com. The frontend can be hosted on any static hosting service.

## License

MIT License 