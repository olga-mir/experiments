# Spec: data-fetching-tools

## Overview
Refactor the tools in `tools.py` to use parameterized URLs and handle both live and simulated data streams based on the current configuration.

### Requirement: Parameterized Data Fetching

**Context:** Tools currently have hardcoded URLs for AI Engineer Melbourne 2026.

#### Scenario: Fetch live streams with custom base URL
- **Given** the `CONFERENCE_BASE_URL` is set to a custom endpoint
- **When** `get_live_streams()` is called
- **Then** it should make a request to `{CONFERENCE_BASE_URL}/streams.json`.

#### Scenario: Captions with since parameter
- **Given** a `stream_id` and a `since` timestamp
- **When** `get_captions(stream_id, since)` is called
- **Then** it should append the `since` parameter to the URL correctly using URL encoding.

### Requirement: Simulation Stream Compatibility

**Context:** The simulation stream might have the same API structure but a different base URL.

#### Scenario: Fetching from simulation endpoint
- **Given** `SIMULATION_MODE` is enabled
- **When** any data-fetching tool is called
- **Then** it must use the `SIMULATION_BASE_URL` to construct its requests.
