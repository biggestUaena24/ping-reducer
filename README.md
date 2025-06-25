# Ping Monitor & QoS Policy Maker

A comprehensive network monitoring and Quality of Service (QoS) policy management tool for Windows systems. This tool provides real-time ping monitoring capabilities combined with intelligent QoS policy creation and management. Currently it is only for Windows use.

## Features

- 🔍 **Real-time Ping Monitoring**: Monitor network latency and packet loss across multiple targets
- ⚡ **QoS Policy Management**: Create, modify, and manage Windows QoS policies
- 📊 **Performance Analytics**: Track network performance trends and statistics
- 🚨 **Intelligent Alerting**: Get notified when network issues are detected
- 🎯 **Multi-target Support**: Monitor multiple hosts simultaneously
- 📈 **Visual Reporting**: Generate comprehensive network health reports

## Prerequisites

- Windows 10/11 or Windows Server 2016+
- Python 3.7 or higher
- Administrative privileges (required for QoS policy management)

## Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/yourusername/ping-monitor-qos.git
   cd ping-reducer
   ```

## Usage

### Running the Application

To start the ping monitor and QoS policy maker, run:

```bash
python .\main.py
```

**Note**: Run Command Prompt or PowerShell as Administrator for full QoS policy management functionality.

### Ping Monitoring

- Real-time latency tracking
- Packet loss detection
- Historical data storage
- Performance trend analysis

### QoS Policy Management

- Automatic policy creation based on network conditions
- Application-specific traffic prioritization
- Bandwidth allocation management
- Policy backup and restore

## Permissions

This tool requires administrative privileges to:

- Modify Windows QoS policies
- Access low-level network statistics
- Configure network adapter settings

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request. For major changes, please open an issue first to discuss what you would like to change.

### Development Setup

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/new-feature`
3. Make your changes and test thoroughly
4. Submit a pull request
