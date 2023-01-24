# Journey

A simple command line utility for daily journalling

## Installation

1. Run the following commands. Skip the first one if you have `pyinstaller` already installed on your system.

    ```json
    pip install -U pyinstaller
    pyinstaller src/journey.py
    ```

2. Create a config file (see below)

3. Copy the folder inside `dist` folder to a location of your choice

4. Add the folder to your path / start menu

## Config example

Create a `journey_config.json` file with the following structure in the root directory of the executable to start using the application.

```json
{
    "log_dir": "C:/Users/aditya/diary",
    "editor": "nvim"
}
```
