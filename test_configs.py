# test_configs.py
from virtual_asic_miner import VirtualASICMiner
import time

configs = [
    {"name": "Small", "chips": 1, "cores": 32},
    {"name": "Medium", "chips": 2, "cores": 64},
    {"name": "Large", "chips": 4, "cores": 128},
    {"name": "Enterprise", "chips": 8, "cores": 256}
]

for config in configs:
    print(f"\nTesting {config['name']} configuration...")
    miner = VirtualASICMiner(
        config['name'], 
        num_chips=config['chips'],
        cores_per_chip=config['cores']
    )
    miner.start_mining()
    time.sleep(20)  # Run for 20 seconds
    miner.stop_mining()
    print(miner.get_performance_report())
