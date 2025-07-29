# Foxtrot Trading Platform

Foxtrot is an event-driven trading platform framework built with Python. It provides a modular architecture for connecting to different brokers and exchanges, managing orders, and handling market data.

## Features

- Event-driven architecture with central event engine
- Modular adapter system for different brokers/exchanges
- Order Management System (OMS)
- Real-time market data handling
- Position and account management
- Email notifications support
- Interactive Brokers integration

## Installation

Install dependencies using Poetry:

```bash
poetry install --no-root
```

## Project Structure

- `foxtrot/adapter/` - Broker/exchange adapters
- `foxtrot/app/` - Application modules
- `foxtrot/core/` - Core event system
- `foxtrot/server/` - Main engine and server components
- `foxtrot/util/` - Utilities and data structures
- `foxtrot/testing/` - Testing utilities and tools
  - `foxtrot/testing/ibrokers/` - Interactive Brokers testing tools
- `tests/` - Unit and integration tests
- `examples/` - Example scripts and usage demonstrations

## Configuration

Create a `vt_setting.json` file in your working directory with necessary settings for database, email, and datafeed configurations.

## Usage

See the documentation for detailed usage instructions and API reference.