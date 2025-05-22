# IPv6 DNS Auto Update Script

This script is used to automatically obtain the native IPv6 address and update the domain name resolution record through the Alibaba Cloud DNS API.

## Environmental requirements

- Python 3.x
- Conda environment (using daily environment)
- Installed dependency packages (see requirements.txt)

## Features

- Automatically obtain the public IPv6 address of the machine:
    - Prioritizes fetching from `https://api6.ipify.org` for accuracy.
    - Falls back to local network interfaces if the external API is unavailable.
- Use Alibaba Cloud DNS API to update domain name resolution
- Automatically query domain name resolution record ID
- Support environment variable configuration
- Comprehensive logging:
    - Records events to `update_dns.log` with timestamps and severity.
    - Outputs logs to the console simultaneously.
- Support custom TTL and resolution line
- Support automatic startup at boot

## Install dependencies

1. Make sure the daily environment is activated:
```bash
conda activate daily
```

2. Install dependency packages:
```bash
pip install -r requirements.txt
```

## Configuration instructions

1. Copy the sample environment variable file:
```bash
cp .env.example .env
```

2. Edit the `.env` file and fill in the following information:

Required parameters:
- `ALIYUN_ACCESS_KEY_ID`: Alibaba Cloud Access Key ID
- `ALIYUN_ACCESS_KEY_SECRET`: Alibaba Cloud Access Key Secret
- `DOMAIN_NAME`: Your domain name (e.g. example.com)
- `RR`: Subdomain (e.g. www)

Optional parameters:
- `TTL`: Resolution effective time, in seconds, default is 600 seconds (10 minutes)
- `LINE`: Resolution line, default is default
- `LANG`: Language type for requesting and receiving messages, default is zh

## How to use

### Manual operation
1. Activate the conda environment:
```bash
conda activate daily
```

2. Run the script:
```bash
python update_dns.py
```

### Set auto-start at boot (Windows)

1. Make sure Conda is installed and configured
2. Run PowerShell as administrator
3. Execute the following command:
```powershell
Set-ExecutionPolicy RemoteSigned -Scope Process
.\setup_autostart.ps1
```

This will create a scheduled task named "UpdateDNSIPv6" that automatically runs the script when the system starts. The script will automatically use the conda daily environment.

### Cancel auto-start at boot

Method 1: Use script (recommended)
1. Run PowerShell as administrator
2. Execute the following command:
```powershell
Set-ExecutionPolicy RemoteSigned -Scope Process
.\remove_autostart.ps1
```

Method 2: Manual deletion
1. Press Win + R, enter `taskschd.msc` to open Task Scheduler
2. Expand "Task Scheduler Library" in the left panel
3. Find the task named "UpdateDNSIPv6"
4. Right-click the task and select "Delete"

### Set scheduled tasks

#### Windows
Use Task Scheduler to create a scheduled task to run this script periodically.

#### Linux
Use crontab to add a scheduled task, for example, run it every hour:
```bash
0 * * * * /path/to/conda/envs/daily/bin/python /path/to/update_dns.py
```

## Logging Details

The script implements a comprehensive logging system to help monitor its operations and troubleshoot issues:

- **Log File:** All operational logs are saved to a file named `update_dns.log`, located in the same directory as the script.
- **Console Output:** Logs are simultaneously displayed on the console where the script is executed.
- **Log Format:** Each log entry includes a timestamp, the severity level (e.g., INFO, ERROR, WARNING), and a descriptive message. This structured format aids in understanding the script's execution flow and identifying any problems.
- **Usage:** Check `update_dns.log` for detailed information after running the script, especially if you encounter issues or want to verify its actions.

## Precautions

1. Make sure your network supports IPv6
2. Make sure the Alibaba Cloud access key has DNS management permissions
3. It is recommended to set the script to run regularly to keep the DNS records updated in time
4. It is recommended that the TTL value should not be set too small, so as not to affect the DNS resolution performance
5. The resolution line (LINE) parameter needs to be set according to your actual needs. Common values include:
   - default: default line
   - telecom: Telecom line
   - unicom: Unicom line
   - mobile: Mobile line
   - oversea: Oversea line
6. If the auto-start task at boot cannot run, please check:
   - Whether Conda is correctly installed and added to the system environment variables
   - Whether the daily environment exists and contains the required dependencies
   - Whether to run the setup script with administrator privileges
   - Whether the scheduled task is correctly created in the Task Scheduler
7. If the script cannot find the domain name resolution record, please check:
   - Whether the domain name is configured correctly
   - Whether an AAAA type resolution record has been created
   - Whether the subdomain (RR) is correct
