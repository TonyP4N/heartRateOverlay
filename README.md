# Heart Rate Overlay

A lightweight, transparent heart rate overlay for streamers and gamers. This application fetches heart rate data from [Stromno](https://stromno.com) via a hidden browser window and displays it in a customizable floating widget.

## Features

- **Real-time Monitoring**: Fetches heart rate data from Stromno.
- **Transparent Overlay**: Minimalist design that floats over your game or application.
- **Always on Top**: Stays visible during gameplay.
- **Customizable**: Change font and color via the system tray icon.
- **Draggable**: Easily move the overlay anywhere on the screen.

## Prerequisites

- [Python 3.8+](https://www.python.org/downloads/)
- [Google Chrome](https://www.google.com/chrome/) installed (for Selenium/Chromedriver).

## Installation

1.  Clone the repository:
    ```bash
    git clone https://github.com/yourusername/heart_rate_overlay.git
    cd heart_rate_overlay
    ```

2.  Install dependencies:
    ```bash
    pip install -r requirements.txt
    ```

3.  Configure environment variables:
    - Rename `.example.env` (if provided) or create a `.env` file in the root directory.
    - Add your Stromno Widget URL (get this from your Stromno dashboard):
      ```ini
      STROMNO_URL=https://stromno.com/widget/your_widget_id
      ```
    - (Optional) Set default font and color in `.env` if supported, though the UI settings take precedence.

## Usage

1.  Run the application:
    ```bash
    python src/heart_rate_app.py
    ```

2.  The overlay will appear.
    - **Click and Drag** to move it.
    - **Right-click** the system tray icon (heart icon) to change settings or quit.

## Build from Source

If you want to create a standalone executable (`.exe`):

1.  Install PyInstaller:
    ```bash
    pip install pyinstaller
    ```

2.  Run the build command:
    ```bash
    pyinstaller --noconsole --name "HeartRateMonitor" src/heart_rate_app.py
    ```

3.  The executable will be located in the `dist/HeartRateMonitor/` folder.

## Structure

- `src/`: Main source code.
  - `heart_rate_app.py`: Main entry point and overlay logic.
  - `color_config.py`: Configuration UI logic.
  - `config.py`: Environment variable loading.
- `legacy/`: Older versions of the application.

## Troubleshooting

- **Browser Window**: The application uses a headless Chrome browser. If you see a browser window pop up, it might be due to configuration, but it should stay hidden.
- **Heart Rate Not Updating**: Ensure your Stromno widget URL is correct and your heart rate monitor is broadcasting to Stromno.

## License

[MIT](LICENSE)
