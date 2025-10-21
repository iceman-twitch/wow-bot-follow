# WoW Bot Follow

A simple bot that helps automate following and mimicking actions in World of Warcraft.

## Requirements

- Python 3.9 or higher
- Required Python packages (see requirements.txt)
- Windows OS

## Features

- Follows target player movements
- Copies target's actions
- Handles quest automation
- Multi-window support
- Custom key bindings

## Usage

### Basic Macro For Client
```wow
/targetexact PLAYER
/follow PLAYER
/script SetRaidTarget("target", 7)
/assist PLAYER
/script SetRaidTarget("target", 8)
/startattack
/cast SPELL
```

### Quest Automation
```wow
/run C_GossipInfo.SelectAvailableQuest(C_GossipInfo.GetAvailableQuests()[1]["questID"])
/run SelectAvailableQuest(1)
/run AcceptQuest()
/run CompleteQuest(1)
/run GetQuestReward(1)
```

## Setup

1. Clone the repository
2. Install Python 3.9 or higher if not already installed
3. Create and activate virtual environment (recommended):
   ```batch
   python -m venv env
   env\Scripts\activate
   ```
4. Install required dependencies:
   ```batch
   pip install -r requirements.txt
   ```
5. Configure windows.json if using multi-window mode
6. Run the server and client

## Configuration

The bot can be configured to:
- Work with single or multiple WoW windows
- Custom key bindings
- Specific follow targets
- Quest automation sequences

## Legal Notice

This tool is for educational purposes only. Use at your own risk and ensure compliance with World of Warcraft's Terms of Service.
