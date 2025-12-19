# Deezer Playlist Converter 🎵

A powerful, user-friendly web application that converts textual tracklists (like YouTube descriptions) into Deezer playlists automatically.

![License](https://img.shields.io/badge/license-MIT-blue.svg)
![Python](https://img.shields.io/badge/python-3.8+-blue.svg)
![FastAPI](https://img.shields.io/badge/backend-FastAPI-green.svg)

## ✨ Features

- **Smart Parsing**: Automatically extracts `Artist - Title` from text, handling timestamps (`02:30`), numbered lists (`1.`), and missing artists.
- **Intelligent Search**:
    - **Strict Match**: Finds the exact song.
    - **Fuzzy Fallback**: Tries broader searches if exact match fails.
    - **Interactive Resolution**: If a song is ambiguous (or Artist is missing/wrong), it flags it in **Yellow** and lets you choose from a dropdown list.
    - **Refine Search**: Built-in search bar to manually find specific tracks if the auto-detection fails.
- **Large Playlist Support**: Automatically handles large playlists by chunking uploads to avoid API limits.
- **Modern UI**: sleek "Glassmorphism" design with dark mode aesthetics.
- **Multi-User Safe**: Your Deezer `ARL` cookie is stored locally in your browser, not on the server.

## 🚀 Installation & Local Run

1.  **Clone the repository**
    ```bash
    git clone https://github.com/Lizantros/Deezer_API.git
    cd Deezer_API
    ```

2.  **Install Dependencies**
    ```bash
    pip install -r requirements.txt
    ```

3.  **Run the Server**
    ```bash
    python server.py
    ```
    The app will start at `http://localhost:8000`.

## 🔑 How to use

1.  **Get your Deezer ARL Cookie**:
    - Log in to [Deezer.com](https://www.deezer.com) in your browser.
    - Open Developer Tools (F12) -> Application -> Cookies -> `www.deezer.com`.
    - Find the cookie named `arl` and copy its value (it's a long string of ~192 chars).
2.  **Paste text**: Copy a tracklist from a YouTube video description.
3.  **Parse**: Click "1. Parse Songs".
4.  **Match**: Click "2. Find Matches".
    - **Green**: Perfect match found.
    - **Yellow**: Ambiguous. Use the dropdown to pick the right song.
    - **Red**: Not found. use the "search" input to find it manually.
5.  **Create**: Enter a name and click "Create Playlist".

## ☁️ Deployment (Vercel)

This project is configured for easy deployment on Vercel.

1.  Push this code to your own GitHub repository.
2.  Import the project in Vercel.
3.  Vercel should automatically detect the Python configuration via `vercel.json`.
4.  Deploy!

*Note: Deezer's internal API (`gw-light.php`) is sensitive to IP addresses. Cloud deployments *may* occasionally face stricter rate limits or CAPTCHAs compared to running locally on your residential IP.*

## ⚠️ Disclaimer

This tool uses an unofficial method (Deezer's internal `gw-light.php` API) to bypass the need for an official App ID, which makes it easier for personal use. It acts as a browser automation tool. Use responsibly.
