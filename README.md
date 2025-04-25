# Employee Attendance System

A Python-based employee attendance system with face recognition and Discord bot integration for managing employee check-ins and generating attendance reports.

## Features
- **Face Recognition**: Register and recognize employees using facial recognition powered by the `face_recognition` library.
- **Attendance Logging**: Track employee check-ins and export logs to Excel or CSV formats.
- **Admin Interface**: Secure admin login with password encryption (`bcrypt`) and a lockout mechanism for failed login attempts.
- **Employee Management**: Add, delete, rename employees, and update their date of birth via a Tkinter-based GUI.
- **Discord Bot**: Provides slash commands to view employee lists, attendance reports, and birthday notifications.
- **Data Security**: Encrypts sensitive data (employee data, logs, and face images) using the `cryptography` library.

## Requirements
- Python 3.8 or higher
- A webcam for face recognition
- A Discord bot token and channel ID for bot functionality
- Install dependencies listed in `requirements.txt`:
  ```bash
  pip install -r requirements.txt
  ```

## Installation
1. **Clone the repository**:
   ```bash
   git clone https://github.com/your-username/employee-attendance-system.git
   cd employee-attendance-system
   ```
   Replace `your-username` with your GitHub username.

2. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Set up environment variables**:
   Create a `.env` file in the project root with the following content:
   ```plaintext
   CHANNEL_ID=your_discord_channel_id
   TOKEN=your_discord_bot_token
   ```
   - Obtain `CHANNEL_ID` from your Discord server.
   - Create a bot and get `TOKEN` from the [Discord Developer Portal](https://discord.com/developers/applications).

4. **Create necessary directories**:
   The application automatically creates `config/` and `database/` directories for storing encrypted data and logs.

## Usage
1. **Run the main application**:
   Launch the Tkinter GUI for attendance and admin tasks:
   ```bash
   python main.py
   ```
   - Default admin password: `admin123` (change it after the first login).
   - Use the GUI to:
     - Check in employees via face recognition.
     - Register new employees with face images.
     - Manage employee data (rename, update DOB, delete).
     - Export attendance logs and employee lists.

2. **Run the Discord bot**:
   Start the bot to enable Discord commands:
   ```bash
   python bot.py
   ```
   Available slash commands:
   - `/employees`: List all registered employees.
   - `/list_dob`: List employees with their dates of birth.
   - `/attendance`: Show today's attendance report.
   - `/check <ID | name> [date]`: Check attendance for an employee by ID or name.
   - `/attendance_table <days | dd/mm>`: Display an attendance table for a specific period.
   - `/helppls`: Show the list of available commands.

3. **View employee and attendance data**:
   Run the data reader script to display employee details and attendance logs:
   ```bash
   python read_data.py
   ```

## Folder Structure
- `config/`: Stores encryption keys and admin configuration (excluded from Git via `.gitignore`).
- `database/`: Stores employee data, attendance logs, and face images (excluded from Git via `.gitignore`).
- `*.py`: Core application scripts for GUI, face recognition, and Discord bot.
- `requirements.txt`: Lists Python dependencies.
- `.gitignore`: Excludes sensitive files from version control.
- `.env`: Stores Discord bot credentials (not tracked by Git).

## Security Notes
- **Sensitive Data**: Files in `config/` (e.g., `secret.key`, `admin_config.enc`) and `database/` (e.g., `employees.pkl`, `logs.csv`, face images) are encrypted and excluded from Git to protect sensitive information.
- **Discord Bot Token**: Store the bot token in the `.env` file, which is excluded via `.gitignore`. Never hardcode sensitive credentials in source code.
- **Admin Password**: Change the default admin password (`admin123`) immediately after setup to secure the application.
- **File Permissions**: The application sets restrictive permissions (`0o600`) on sensitive files to prevent unauthorized access.

## Troubleshooting
- **Camera Issues**: Ensure a webcam is connected and accessible for face recognition.
- **Discord Bot Errors**: Verify the `CHANNEL_ID` and `TOKEN` in the `.env` file are correct and the bot has permission to access the specified channel.
- **Dependency Issues**: Ensure all dependencies in `requirements.txt` are installed correctly. Use a virtual environment to avoid conflicts:
  ```bash
  python -m venv venv
  source venv/bin/activate  # On Windows: venv\Scripts\activate
  pip install -r requirements.txt
  ```

## Contributing
Contributions are welcome! Please:
1. Fork the repository.
2. Create a feature branch (`git checkout -b feature/your-feature`).
3. Commit your changes (`git commit -m "Add your feature"`).
4. Push to the branch (`git push origin feature/your-feature`).
5. Open a pull request.

## License
MIT License
