import numpy as np
from qiskit import QuantumCircuit, transpile
from qiskit_aer import AerSimulator
from numba import njit, prange
import time

# Use Aer's high-performance statevector simulator
simulator = AerSimulator(method='statevector', device='CPU')

@njit(fastmath=True, parallel=True)
def classical_post_process(results, n_qubits):
    """Fast classical post-processing using Numba."""
    max_count = 0
    best_state = 0
    for i in prange(len(results)):
        if results[i] > max_count:
            max_count = results[i]
            best_state = i
    return best_state, max_count

def grover_oracle(n_qubits, target_state):
    """Create a Grover oracle for a specific target state."""
    qc = QuantumCircuit(n_qubits)
    # Flip the target state using Z gate controlled on all bits being correct
    # For simplicity, we'll use a phase oracle via X and multi-controlled Z
    binary = format(target_state, f'0{n_qubits}b')
    for i, bit in enumerate(binary):
        if bit == '0':
            qc.x(i)
    qc.h(n_qubits - 1)
    qc.mcx(list(range(n_qubits - 1)), n_qubits - 1)  # Multi-controlled Z (via H-MCX-H)
    qc.h(n_qubits - 1)
    for i, bit in enumerate(binary):
        if bit == '0':
            qc.x(i)
    return qc

def diffusion_operator(n_qubits):
    """Grover diffusion operator (inversion about average)."""
    qc = QuantumCircuit(n_qubits)
    qc.h(range(n_qubits))
    qc.x(range(n_qubits))
    qc.h(n_qubits - 1)
    qc.mcx(list(range(n_qubits - 1)), n_qubits - 1)
    qc.h(n_qubits - 1)
    qc.x(range(n_qubits))
    qc.h(range(n_qubits))
    return qc

def run_grover(n_qubits, target_state, iterations=1):
    """Run Grover's algorithm with optimized execution."""
    qc = QuantumCircuit(n_qubits)
    qc.h(range(n_qubits))  # Uniform superposition

    oracle = grover_oracle(n_qubits, target_state)
    diffuser = diffusion_operator(n_qubits)

    for _ in range(iterations):
        qc.append(oracle, range(n_qubits))
        qc.append(diffuser, range(n_qubits))

    # Transpile for simulator optimization
    qc = transpile(qc, simulator, optimization_level=3)

    # Run simulation (high-speed backend)
    job = simulator.run(qc, shots=1024)
    result = job.result()
    counts = result.get_counts()

    # Convert counts to array for fast processing
    count_array = np.zeros(2**n_qubits, dtype=np.int32)
    for state, count in counts.items():
        idx = int(state, 2)
        count_array[idx] = count

    # Fast classical post-processing
    best_state, best_count = classical_post_process(count_array, n_qubits)

    return best_state, best_count, counts

# --- Main Execution ---
if _name_ == "_main_":
    n_qubits = 5
    target = 19  # Binary: 10011
    optimal_iterations = int(np.pi / 4 * np.sqrt(2**n_qubits))  # ~7 for n=5

    print(f"Searching for state |{target}⟩ ({format(target, f'0{n_qubits}b')})...")
    start = time.time()

    found_state, count, counts = run_grover(n_qubits, target, iterations=optimal_iterations)

    elapsed = time.time() - start

    print(f"Found state: |{found_state}⟩ with {count} counts")
    print(f"Correct? {'✅' if found_state == target else '❌'}")
    print(f"Top 5 results: {sorted(counts.items(), key=lambda x: x[1], reverse=True)[:5]}")
    print(f"Execution time: {elapsed:.4f} seconds")
