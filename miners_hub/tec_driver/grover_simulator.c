#include <stdio.h>
#include <stdlib.h>
#include <complex.h> // For complex numbers (e.g., double complex)
#include <math.h>     // For sqrt, M_PI
#include <time.h>     // For timing
#include <omp.h>      // For OpenMP parallelization

// Define constants
#define N_QUBITS 22   // <--- Increase this to see the power of C! (e.g., 22-26)
#define TARGET_STATE 19861121 // A random target state for a 25-qubit system

// Helper to get a bit
#define GET_BIT(n, k) (((n) >> (k)) & 1)

// =================================================================
// QUANTUM GATE IMPLEMENTATIONS
// =================================================================

// Apply a single-qubit Hadamard gate to a specific qubit
// This operation is highly parallelizable.
void apply_H(double complex *sv, int qubit, long long num_states) {
    long long stride = 1LL << qubit;
    #pragma omp parallel for
    for (long long i = 0; i < num_states; i += 2 * stride) {
        for (long long j = 0; j < stride; ++j) {
            long long idx0 = i + j;
            long long idx1 = i + j + stride;
            double complex temp0 = sv[idx0];
            double complex temp1 = sv[idx1];
            sv[idx0] = (temp0 + temp1) / sqrt(2.0);
            sv[idx1] = (temp0 - temp1) / sqrt(2.0);
        }
    }
}

// Apply a single-qubit X gate (NOT gate)
void apply_X(double complex *sv, int qubit, long long num_states) {
    long long stride = 1LL << qubit;
    #pragma omp parallel for
    for (long long i = 0; i < num_states; i += 2 * stride) {
        for (long long j = 0; j < stride; ++j) {
            long long idx0 = i + j;
            long long idx1 = i + j + stride;
            double complex temp = sv[idx0];
            sv[idx0] = sv[idx1];
            sv[idx1] = temp;
        }
    }
}

// Apply a multi-controlled Z gate. This is the core of oracles and diffusers.
// It flips the phase of the single state where all control qubits are |1>.
void apply_MCZ(double complex *sv, int *controls, int num_controls, int n_qubits) {
    long long target_idx = 0;
    for(int i = 0; i < num_controls; ++i) {
        target_idx |= (1LL << controls[i]);
    }
    sv[target_idx] *= -1.0;
}


// =================================================================
// GROVER ALGORITHM COMPONENTS
// =================================================================

// Applies the Oracle for the TARGET_STATE
void apply_grover_oracle(double complex *sv, int n_qubits, long long num_states) {
    // 1. Apply X to qubits that are '0' in the target state
    for (int i = 0; i < n_qubits; ++i) {
        if (!GET_BIT(TARGET_STATE, i)) {
            apply_X(sv, i, num_states);
        }
    }

    // 2. Apply multi-controlled Z gate on all qubits
    // (This is equivalent to H-MCX-H on a helper qubit, but much faster to simulate)
    int all_qubits[n_qubits];
    for(int i=0; i<n_qubits; ++i) all_qubits[i] = i;
    apply_MCZ(sv, all_qubits, n_qubits, n_qubits);

    // 3. Uncompute the X gates
    for (int i = 0; i < n_qubits; ++i) {
        if (!GET_BIT(TARGET_STATE, i)) {
            apply_X(sv, i, num_states);
        }
    }
}

// Applies the Grover Diffusion Operator
void apply_diffusion_operator(double complex *sv, int n_qubits, long long num_states) {
    for (int i = 0; i < n_qubits; ++i) apply_H(sv, i, num_states);
    for (int i = 0; i < n_qubits; ++i) apply_X(sv, i, num_states);

    int all_qubits[n_qubits];
    for(int i=0; i<n_qubits; ++i) all_qubits[i] = i;
    apply_MCZ(sv, all_qubits, n_qubits, n_qubits);

    for (int i = 0; i < n_qubits; ++i) apply_X(sv, i, num_states);
    for (int i = 0; i < n_qubits; ++i) apply_H(sv, i, num_states);
}

// Finds the state with the highest probability amplitude
long long find_best_state(double complex *sv, long long num_states) {
    long long best_idx = 0;
    double max_prob = 0.0;
    #pragma omp parallel
    {
        long long local_best_idx = 0;
        double local_max_prob = 0.0;
        #pragma omp for
        for (long long i = 0; i < num_states; ++i) {
            double prob = cabs(sv[i]) * cabs(sv[i]); // Probability = |amplitude|^2
            if (prob > local_max_prob) {
                local_max_prob = prob;
                local_best_idx = i;
            }
        }
        #pragma omp critical
        {
            if (local_max_prob > max_prob) {
                max_prob = local_max_prob;
                best_idx = local_best_idx;
            }
        }
    }
    printf("Found state with probability: %.4f\n", max_prob);
    return best_idx;
}

// =================================================================
// MAIN DRIVER
// =================================================================
int main() {
    printf("--- High-Speed Quantum Simulator in C ---\n");
    printf("Simulating Grover's search for %d qubits.\n", N_QUBITS);
    printf("Target state: %d\n", TARGET_STATE);

    long long num_states = 1LL << N_QUBITS;
    double mem_gb = (double)num_states * sizeof(double complex) / (1024*1024*1024);
    printf("Statevector size: %lld states (%.2f GB of RAM required)\n", num_states, mem_gb);

    // Allocate statevector
    double complex *statevector = (double complex *)malloc(num_states * sizeof(double complex));
    if (statevector == NULL) {
        fprintf(stderr, "Error: Failed to allocate memory.\n");
        return 1;
    }

    // Start timer
    double start_time = omp_get_wtime();

    // 1. Initialize statevector to |0...0>
    #pragma omp parallel for
    for (long long i = 1; i < num_states; ++i) statevector[i] = 0.0 + 0.0 * I;
    statevector[0] = 1.0 + 0.0 * I;

    // 2. Apply Hadamard to all qubits to create uniform superposition
    printf("Creating superposition...\n");
    for (int i = 0; i < N_QUBITS; ++i) {
        apply_H(statevector, i, num_states);
    }

    // 3. Run Grover iterations
    int iterations = (int)(M_PI / 4.0 * sqrt(num_states));
    printf("Running %d Grover iterations...\n", iterations);
    for (int i = 0; i < iterations; ++i) {
        apply_grover_oracle(statevector, N_QUBITS, num_states);
        apply_diffusion_operator(statevector, N_QUBITS, num_states);
        // printf("Iteration %d/%d complete\n", i + 1, iterations);
    }

    // 4. Find the result by measuring
    printf("Measuring final state...\n");
    long long found_state = find_best_state(statevector, num_states);

    // End timer and print results
    double end_time = omp_get_wtime();

    printf("\n--- Results ---\n");
    printf("Found state:  |%lld⟩\n", found_state);
    printf("Target state: |%d⟩\n", TARGET_STATE);
    printf("Correct? %s\n", (found_state == TARGET_STATE) ? "✅ Yes" : "❌ No");
    printf("Total execution time: %.4f seconds\n", end_time - start_time);

    // Cleanup
    free(statevector);
    return 0;
}
