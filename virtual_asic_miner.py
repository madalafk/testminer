#!/usr/bin/env python3
"""
Educational Virtual ASIC Miner for Bitcoin SHA-256d
This is for LEARNING PURPOSES only - does NOT mine real Bitcoin
"""

import hashlib
import struct
import time
import threading
import numpy as np
from dataclasses import dataclass
from typing import Optional, Tuple, List
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation
import random
import json
from datetime import datetime

# ============================================
# PART 1: VIRTUAL ASIC CORE
# ============================================

class VirtualASICCore:
    """Simulates a single ASIC core with pipeline stages"""
    
    def __init__(self, core_id: int):
        self.core_id = core_id
        self.nonce = 0
        self.hash_count = 0
        self.pipeline_stages = [0] * 8  # 8-stage pipeline
        self.active = False
        self.temperature = 35.0  # Starting temperature in Celsius
        
    def process_hash(self, nonce: int, data: bytes) -> Optional[bytes]:
        """Process a single hash through the pipeline"""
        self.nonce = nonce
        self.hash_count += 1
        
        # Simulate pipeline stages
        for stage in range(8):
            self.pipeline_stages[stage] = nonce + stage
            # Small delay to simulate pipeline latency
            if stage == 7:  # Last stage produces result
                # Simulate double SHA-256
                header_with_nonce = data[:76] + struct.pack('<I', nonce) + data[80:]
                hash1 = hashlib.sha256(header_with_nonce).digest()
                hash2 = hashlib.sha256(hash1).digest()
                
                # Update temperature (heat generation)
                self.temperature += 0.001
                return hash2
        return None
    
    def get_stats(self):
        """Get core statistics"""
        return {
            'core_id': self.core_id,
            'hash_count': self.hash_count,
            'temperature': self.temperature,
            'active': self.active
        }

# ============================================
# PART 2: VIRTUAL ASIC CHIP
# ============================================

class VirtualASIC:
    """Simulates a complete ASIC chip with multiple cores"""
    
    def __init__(self, chip_id: int, num_cores: int = 128):
        self.chip_id = chip_id
        self.cores = [VirtualASICCore(i) for i in range(num_cores)]
        self.total_hashes = 0
        self.start_time = time.time()
        self.hashrate_history = []
        self.found_nonces = []
        
    def mine_range(self, header: bytes, target: int, start_nonce: int, end_nonce: int):
        """Mine a range of nonces"""
        batch_size = len(self.cores) * 10  # Process in batches
        
        for nonce in range(start_nonce, end_nonce, batch_size):
            # Distribute work across cores
            for i, core in enumerate(self.cores):
                current_nonce = nonce + i
                if current_nonce < end_nonce:
                    result = core.process_hash(current_nonce, header)
                    self.total_hashes += 1
                    
                    # Check if found valid hash
                    if result and int.from_bytes(result, 'big') < target:
                        self.found_nonces.append(current_nonce)
                        return current_nonce
            
            # Update hashrate every 1000 hashes
            if self.total_hashes % 1000 == 0:
                elapsed = time.time() - self.start_time
                hashrate = self.total_hashes / elapsed if elapsed > 0 else 0
                self.hashrate_history.append((elapsed, hashrate))
    
    def get_hashrate(self):
        """Calculate current hashrate"""
        elapsed = time.time() - self.start_time
        return self.total_hashes / elapsed if elapsed > 0 else 0
    
    def get_stats(self):
        """Get chip statistics"""
        return {
            'chip_id': self.chip_id,
            'total_hashes': self.total_hashes,
            'hashrate': self.get_hashrate(),
            'cores_active': sum(1 for c in self.cores if c.active),
            'avg_temp': np.mean([c.temperature for c in self.cores]),
            'found_nonces': len(self.found_nonces)
        }

# ============================================
# PART 3: MINING POOL SIMULATOR
# ============================================

@dataclass
class BitcoinBlock:
    """Bitcoin block structure"""
    version: int = 1
    prev_block: bytes = bytes(32)
    merkle_root: bytes = bytes(32)
    timestamp: int = 0
    bits: int = 0x1d00ffff  # Difficulty 1
    nonce: int = 0
    
    def header(self) -> bytes:
        """Create 80-byte block header"""
        header = struct.pack('<I', self.version)
        header += self.prev_block[::-1]
        header += self.merkle_root[::-1]
        header += struct.pack('<I', self.timestamp)
        header += struct.pack('<I', self.bits)
        header += struct.pack('<I', self.nonce)
        return header
    
    def target_from_bits(self) -> int:
        """Convert bits to target value"""
        exponent = self.bits >> 24
        mantissa = self.bits & 0xffffff
        return mantissa * (2 ** (8 * (exponent - 3)))

class MiningPool:
    """Simulated mining pool for educational purposes"""
    
    def __init__(self, difficulty: float = 1.0):
        self.difficulty = difficulty
        self.blocks_found = 0
        self.shares_found = 0
        self.miners = []
        self.block_template = None
        
    def create_block_template(self) -> BitcoinBlock:
        """Create a new block template for miners"""
        self.block_template = BitcoinBlock(
            version=1,
            prev_block=random.getrandbits(256).to_bytes(32, 'big'),
            merkle_root=random.getrandbits(256).to_bytes(32, 'big'),
            timestamp=int(time.time()),
            bits=0x1d00ffff  # Difficulty 1
        )
        return self.block_template
    
    def submit_share(self, miner_id: str, nonce: int, block: BitcoinBlock) -> bool:
        """Submit a found share from a miner"""
        # Verify the share
        header = block.header()[:76] + struct.pack('<I', nonce) + block.header()[80:]
        hash1 = hashlib.sha256(header).digest()
        hash2 = hashlib.sha256(hash1).digest()
        hash_int = int.from_bytes(hash2, 'big')
        
        target = block.target_from_bits() / self.difficulty
        
        if hash_int < target:
            self.shares_found += 1
            
            # Check if it's a full block (meets network difficulty)
            if hash_int < block.target_from_bits():
                self.blocks_found += 1
                print(f"\n🎉 BLOCK FOUND by {miner_id}! Hash: {hash2.hex()[:16]}...")
            
            return True
        return False

# ============================================
# PART 4: MINER MANAGEMENT
# ============================================

class VirtualASICMiner:
    """Manages multiple ASIC chips for mining"""
    
    def __init__(self, name: str, num_chips: int = 4, cores_per_chip: int = 128):
        self.name = name
        self.chips = [VirtualASIC(i, cores_per_chip) for i in range(num_chips)]
        self.pool = MiningPool()
        self.running = False
        self.mining_thread = None
        self.stats_history = []
        
        print(f"\n🔧 Initialized {name}:")
        print(f"   Chips: {num_chips}")
        print(f"   Cores per chip: {cores_per_chip}")
        print(f"   Total cores: {num_chips * cores_per_chip}")
        print(f"   Estimated hashrate: {num_chips * cores_per_chip * 1000:.2e} H/s")
    
    def start_mining(self):
        """Start the mining process"""
        self.running = True
        self.mining_thread = threading.Thread(target=self._mining_loop)
        self.mining_thread.daemon = True
        self.mining_thread.start()
        print(f"\n⛏️  {self.name} started mining...")
    
    def stop_mining(self):
        """Stop the mining process"""
        self.running = False
        if self.mining_thread:
            self.mining_thread.join(timeout=2)
        print(f"\n⏹️  {self.name} stopped mining")
    
    def _mining_loop(self):
        """Main mining loop"""
        while self.running:
            # Get new block template
            block = self.pool.create_block_template()
            target = block.target_from_bits()
            
            print(f"\n📦 New block template:")
            print(f"   Target: {target:016x}")
            print(f"   Difficulty: {self.pool.difficulty:.2f}")
            
            # Distribute work across chips
            nonce_range = 2**32 // len(self.chips)
            
            for i, chip in enumerate(self.chips):
                start_nonce = i * nonce_range
                end_nonce = (i + 1) * nonce_range
                
                # Mine with this chip
                found = chip.mine_range(block.header(), target, start_nonce, end_nonce)
                
                if found:
                    # Submit found nonce to pool
                    self.pool.submit_share(f"{self.name}-Chip{i}", found, block)
            
            # Collect statistics
            self._collect_stats()
    
    def _collect_stats(self):
        """Collect mining statistics"""
        stats = {
            'timestamp': time.time(),
            'total_hashes': sum(c.total_hashes for c in self.chips),
            'hashrate': np.mean([c.get_hashrate() for c in self.chips]),
            'avg_temp': np.mean([c.get_stats()['avg_temp'] for c in self.chips]),
            'blocks_found': self.pool.blocks_found,
            'shares_found': self.pool.shares_found
        }
        self.stats_history.append(stats)
    
    def get_performance_report(self) -> str:
        """Generate performance report"""
        if not self.stats_history:
            return "No data available"
        
        latest = self.stats_history[-1]
        total_time = latest['timestamp'] - self.stats_history[0]['timestamp']
        
        report = f"""
{'='*50}
📊 PERFORMANCE REPORT - {self.name}
{'='*50}
Runtime:         {total_time:.1f} seconds
Total Hashes:    {latest['total_hashes']:,}
Average Hashrate: {latest['hashrate']/1e6:.2f} MH/s
Peak Hashrate:    {max(s['hashrate'] for s in self.stats_history)/1e6:.2f} MH/s
Average Temp:     {latest['avg_temp']:.1f}°C
Blocks Found:     {latest['blocks_found']}
Shares Found:     {latest['shares_found']}
Efficiency:       {latest['hashrate']/1e12:.2f} TH/s per chip
{'='*50}
"""
        return report

# ============================================
# PART 5: VISUALIZATION
# ============================================

class MiningVisualizer:
    """Real-time visualization of mining activity"""
    
    def __init__(self, miner: VirtualASICMiner):
        self.miner = miner
        self.fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(14, 10))
        self.setup_plots()
        
    def setup_plots(self):
        """Setup the visualization plots"""
        # Hashrate plot
        self.ax1 = plt.subplot(2, 2, 1)
        self.ax1.set_title('Hashrate Over Time')
        self.ax1.set_xlabel('Time (s)')
        self.ax1.set_ylabel('Hashrate (MH/s)')
        self.ax1.grid(True, alpha=0.3)
        
        # Temperature plot
        self.ax2 = plt.subplot(2, 2, 2)
        self.ax2.set_title('Chip Temperature')
        self.ax2.set_xlabel('Time (s)')
        self.ax2.set_ylabel('Temperature (°C)')
        self.ax2.grid(True, alpha=0.3)
        
        # Core activity heatmap
        self.ax3 = plt.subplot(2, 2, 3)
        self.ax3.set_title('Core Activity Heatmap')
        self.ax3.set_xlabel('Core Index')
        self.ax3.set_ylabel('Chip')
        
        # Statistics text
        self.ax4 = plt.subplot(2, 2, 4)
        self.ax4.axis('off')
        self.ax4.set_title('Live Statistics')
        
        plt.tight_layout()
    
    def update(self, frame):
        """Update visualization"""
        if not self.miner.stats_history:
            return
        
        # Clear axes
        self.ax1.clear()
        self.ax2.clear()
        self.ax3.clear()
        self.ax4.clear()
        
        # Get data
        times = [s['timestamp'] - self.miner.stats_history[0]['timestamp'] 
                 for s in self.miner.stats_history]
        hashrates = [s['hashrate']/1e6 for s in self.miner.stats_history]
        temps = [s['avg_temp'] for s in self.miner.stats_history]
        
        # Plot hashrate
        self.ax1.plot(times, hashrates, 'b-', linewidth=2)
        self.ax1.set_title('Hashrate Over Time')
        self.ax1.set_xlabel('Time (s)')
        self.ax1.set_ylabel('Hashrate (MH/s)')
        self.ax1.grid(True, alpha=0.3)
        
        # Plot temperature
        self.ax2.plot(times, temps, 'r-', linewidth=2)
        self.ax2.set_title('Chip Temperature')
        self.ax2.set_xlabel('Time (s)')
        self.ax2.set_ylabel('Temperature (°C)')
        self.ax2.grid(True, alpha=0.3)
        
        # Create core activity heatmap
        if self.miner.chips:
            activity = np.array([[c.hash_count % 100 for c in chip.cores] 
                                for chip in self.miner.chips])
            self.ax3.imshow(activity, aspect='auto', cmap='hot', interpolation='nearest')
            self.ax3.set_title('Core Activity Heatmap')
            self.ax3.set_xlabel('Core Index')
            self.ax3.set_ylabel('Chip')
        
        # Show statistics
        if self.miner.stats_history:
            latest = self.miner.stats_history[-1]
            stats_text = f"""
Live Statistics:
{'-'*20}
Runtime: {times[-1]:.1f}s
Hashrate: {latest['hashrate']/1e6:.2f} MH/s
Total Hashes: {latest['total_hashes']:,}
Temperature: {latest['avg_temp']:.1f}°C
Blocks Found: {latest['blocks_found']}
Shares Found: {latest['shares_found']}

Network Stats:
{'-'*20}
Difficulty: {self.miner.pool.difficulty:.2f}
Blocks: {self.miner.pool.blocks_found}
Shares: {self.miner.pool.shares_found}
            """
            self.ax4.text(0.1, 0.9, stats_text, transform=self.ax4.transAxes,
                         fontsize=10, verticalalignment='top',
                         bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5))
        
        self.ax4.axis('off')
        
        plt.tight_layout()
    
    def show(self):
        """Show the visualization"""
        ani = FuncAnimation(self.fig, self.update, interval=1000, cache_frame_data=False)
        plt.show()

# ============================================
# PART 6: MAIN EXECUTION
# ============================================

def run_simulation():
    """Run the complete virtual ASIC mining simulation"""
    
    print("="*60)
    print("🎓 EDUCATIONAL VIRTUAL ASIC MINER SIMULATION")
    print("   Bitcoin SHA-256d Demonstration")
    print("="*60)
    print("\n⚠️  DISCLAIMER: This is for EDUCATIONAL PURPOSES only")
    print("   It does NOT mine real Bitcoin")
    print("   Real Bitcoin mining requires specialized ASIC hardware")
    print("="*60)
    
    # Configuration
    config = {
        'miner_name': 'VirtualASIC-1',
        'num_chips': 2,  # Start with 2 chips for demo
        'cores_per_chip': 64,  # 64 cores per chip
        'simulation_time': 30  # Run for 30 seconds
    }
    
    print(f"\n📋 Simulation Configuration:")
    for key, value in config.items():
        print(f"   {key}: {value}")
    
    # Create miner
    miner = VirtualASICMiner(
        name=config['miner_name'],
        num_chips=config['num_chips'],
        cores_per_chip=config['cores_per_chip']
    )
    
    # Create visualizer
    visualizer = MiningVisualizer(miner)
    
    # Start mining in background
    miner.start_mining()
    
    # Run visualization for specified time
    print(f"\n⏱️  Running simulation for {config['simulation_time']} seconds...")
    
    # Schedule stop after simulation_time
    timer = threading.Timer(config['simulation_time'], miner.stop_mining)
    timer.start()
    
    # Show visualization (this blocks until window is closed)
    try:
        visualizer.show()
    except KeyboardInterrupt:
        print("\n\n⚠️  Simulation interrupted by user")
    finally:
        miner.stop_mining()
        timer.cancel()
    
    # Print final report
    print(miner.get_performance_report())
    
    # Save results to file
    save_results(miner)

def save_results(miner: VirtualASICMiner):
    """Save simulation results to file"""
    results = {
        'miner_name': miner.name,
        'timestamp': datetime.now().isoformat(),
        'stats_history': miner.stats_history,
        'final_stats': miner.get_performance_report()
    }
    
    filename = f"mining_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(filename, 'w') as f:
        # Convert numpy types to Python types for JSON
        def convert(obj):
            if isinstance(obj, np.integer):
                return int(obj)
            elif isinstance(obj, np.floating):
                return float(obj)
            elif isinstance(obj, np.ndarray):
                return obj.tolist()
            else:
                return obj
        
        json.dump(results, f, default=convert, indent=2)
    
    print(f"\n💾 Results saved to {filename}")

def quick_demo():
    """Run a quick demo without visualization"""
    print("\n🚀 Running quick demo (10 seconds)...")
    
    # Small-scale demo
    miner = VirtualASICMiner("QuickDemo", num_chips=1, cores_per_chip=32)
    miner.start_mining()
    
    time.sleep(10)
    miner.stop_mining()
    
    print(miner.get_performance_report())

# ============================================
# MAIN ENTRY POINT
# ============================================

if __name__ == "__main__":
    print("""
    ╔══════════════════════════════════════════════════════════╗
    ║     VIRTUAL ASIC MINER - EDUCATIONAL SIMULATION         ║
    ╚══════════════════════════════════════════════════════════╝
    
    Select simulation mode:
    1. Full simulation with visualization (recommended)
    2. Quick demo (no visualization)
    3. Benchmark mode
    4. Exit
    """)
    
    choice = input("Enter your choice (1-4): ").strip()
    
    if choice == '1':
        run_simulation()
    elif choice == '2':
        quick_demo()
    elif choice == '3':
        print("\n📊 Running benchmark...")
        # Run multiple tests with different configurations
        configs = [
            (1, 32, "Low-end"),
            (2, 64, "Mid-range"),
            (4, 128, "High-end")
        ]
        
        for chips, cores, name in configs:
            print(f"\nTesting {name} configuration...")
            miner = VirtualASICMiner(name, num_chips=chips, cores_per_chip=cores)
            miner.start_mining()
            time.sleep(15)
            miner.stop_mining()
            print(miner.get_performance_report())
    else:
        print("Goodbye!")
