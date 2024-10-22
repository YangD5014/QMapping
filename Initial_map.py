import random
from collections import Counter

def evaluate_physical_qubit(qubit_params, single_qubit_count, multi_qubit_count):
    T1, T2, readout_fidelity = qubit_params["T1"], qubit_params["T2"], qubit_params["Fedility"]
    
    if single_qubit_count > 0:
        score = T1 * 0.6 + T2 * 0.2 + readout_fidelity * 0.2  # 更看重 T1
    elif multi_qubit_count > 0:
        score = T1 * 0.2 + T2 * 0.6 + readout_fidelity * 0.2  # 更看重 T2
    else:
        score = T1 * 0.5 + T2 * 0.5 + readout_fidelity * 0.0  # 如果没有门使用，则平分

    return score

def is_chain(qubit1, qubit2, coupling_map):
    # 检查两个量子比特是否在 coupling map 中相连
    return (qubit1, qubit2) in coupling_map or (qubit2, qubit1) in coupling_map

def generate_mappings(logical_qubits, physical_qubits, coupling_map):
    all_mappings = []
    
    while len(all_mappings) < 20:
        mapping = {}
        used_physical_qubits = set()
        
        for logical_qubit in logical_qubits:
            available_physical = [pq for pq in physical_qubits if pq not in used_physical_qubits]
            if available_physical:
                selected_physical = random.choice(available_physical)
                mapping[logical_qubit] = selected_physical
                used_physical_qubits.add(selected_physical)

        all_mappings.append(mapping)

    return all_mappings

def score_mapping(mapping, physical_qubits, logical_qubits_usage, coupling_map):
    score = 0
    penalty = 0
    
    single_qubit_usage = logical_qubits_usage['单比特门']
    multi_qubit_usage = logical_qubits_usage['双比特门']

    for logical_qubit, physical_qubit in mapping.items():
        single_count = single_qubit_usage[logical_qubit] if logical_qubit in single_qubit_usage else 0
        multi_count = multi_qubit_usage[logical_qubit] if logical_qubit in multi_qubit_usage else 0
        
        score += evaluate_physical_qubit(physical_qubits[physical_qubit], single_count, multi_count)

    mapped_keys = list(mapping.keys())
    for i in range(len(mapped_keys) - 1):
        if is_chain(mapping[mapped_keys[i]], mapping[mapped_keys[i + 1]], coupling_map):
            penalty += 1

    return score - penalty

def find_best_mapping(logical_connectivity, logical_qubits_usage, physical_qubits, coupling_map):
    logical_qubits = set()  # 直接使用集合存储逻辑量子比特
    for logical_qubit_pair in logical_connectivity:
        logical_qubits.update(logical_qubit_pair)  # 添加每对逻辑量子比特

    mappings = generate_mappings(logical_qubits, physical_qubits, coupling_map)

    best_mapping = None
    best_score = float('-inf')

    for mapping in mappings:
        score = score_mapping(mapping, physical_qubits, logical_qubits_usage, coupling_map)
        if score > best_score:
            best_score = score
            best_mapping = mapping

    return best_mapping, best_score
