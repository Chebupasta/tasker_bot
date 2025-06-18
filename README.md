# Telegram Bot for Equipment Purchase Requests

This bot helps manage equipment purchase requests within an organization through Telegram.

## Features

- Create new equipment purchase requests (administrators only)
- View list of requests (all users can see their requests, admins can see all)
- Update request status (administrators only)
- **NEW**: Users can complete and cancel their own requests
- **NEW**: Administrators can see who completed or rejected requests
- **NEW**: Only administrators can delete requests
- Simple and intuitive interface
- Role-based access control (administrators and regular users)

## Setup Instructions

1. Clone this repository
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Run the database migration (if updating from older version):
   ```bash
   python migrate_db.py
   ```
4. Create a `.env` file in the project root with your Telegram bot token:
   ```
   TELEGRAM_BOT_TOKEN=<your token>
   ```
5. Run the bot:
   ```bash
   python bot.py
   ```

## Administrator Management

To manage administrators, use the `manage_admins.py` script:

```bash
python manage_admins.py
```

This script provides the following options:
1. Add administrator - Add a new administrator by Telegram ID and username
2. Remove administrator - Remove administrator privileges from a user
3. List administrators - Show all current administrators
4. Exit

## Available Commands

### For Administrators
- `/start` - Start the bot and get welcome message
- `/help` - Show help information
- `/new` - Create a new equipment request
- `/list` - View all requests
- `/status <id> <status>` - Update request status
- **NEW**: Can see who completed or rejected requests
- **NEW**: Can delete requests permanently

### For Regular Users
- `/start` - Start the bot and get welcome message
- `/help` - Show help information
- `/list` - View your requests
- **NEW**: Can complete their own requests
- **NEW**: Can cancel their own requests (if not in progress)

## New Features (v2.0)

### User Permissions
- **Complete Requests**: Users can mark their own requests as completed
- **Cancel Requests**: Users can cancel their own requests if they haven't been taken into work yet

### Administrator Features
- **Action Tracking**: Administrators can see who completed or rejected each request
- **Delete Permissions**: Only administrators can permanently delete requests
- **Enhanced Visibility**: Full audit trail of who performed what actions

### Database Improvements
- Added `completed_by_id` field to track who completed requests
- Added `cancelled_by_id` field to track who rejected/cancelled requests
- Improved performance with database indexes

## Requirements

- Python 3.8 or higher
- Telegram account
- Bot token from @BotFather 
