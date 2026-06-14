import os
from app.config import AgentConfiguration

def test_base_url():
    # Test Live Mode
    os.environ["SIMULATION_MODE"] = "false"
    os.environ["CONFERENCE_BASE_URL"] = "https://live.com"
    config = AgentConfiguration()
    print(f"Live Base URL: {config.base_url}")
    assert config.base_url == "https://live.com"

    # Test Simulation Mode (enabled but no simulation URL)
    os.environ["SIMULATION_MODE"] = "true"
    os.environ["SIMULATION_BASE_URL"] = ""
    config = AgentConfiguration()
    print(f"Simulation Mode (no URL) Base URL: {config.base_url}")
    assert config.base_url == "https://live.com"

    # Test Simulation Mode (enabled with URL)
    os.environ["SIMULATION_BASE_URL"] = "https://sim.com"
    config = AgentConfiguration()
    print(f"Simulation Base URL: {config.base_url}")
    assert config.base_url == "https://sim.com"

if __name__ == "__main__":
    test_base_url()
    print("✅ Base URL routing test passed")
