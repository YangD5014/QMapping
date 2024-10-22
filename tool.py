from cqlib.utils import QcisToQasm,QasmToQcis
from qiskit.circuit import QuantumCircuit
from cqlib.utils import QCIS_Simplify
from qiskit import qasm2
import json
from qiskit.converters import circuit_to_dag, dag_to_circuit
from collections import OrderedDict
from qiskit.circuit.classicalregister import  Clbit
from qiskit.dagcircuit import DAGCircuit
from collections import Counter
import pandas as pd
from Initial_map import find_best_mapping
from qiskit.transpiler.passes import VF2Layout,VF2PostLayout 
from qiskit.providers import BackendV2
from qiskit.transpiler import CouplingMap,CouplingError
from qiskit.providers.models import BackendProperties,BackendConfiguration
import pandas as pd
from qiskit.transpiler.passes.layout.vf2_utils import ErrorMap
from qiskit.transpiler.preset_passmanagers import generate_preset_pass_manager
from qiskit.providers.fake_provider import GenericBackendV2
from qiskit import QuantumCircuit, transpile
from qiskit.visualization import plot_circuit_layout
from qiskit.converters import dag_to_circuit,circuit_to_dag
from qiskit.transpiler import  Layout
from qiskit.visualization import plot_gate_map
from qiskit.circuit import QuantumRegister


coupling_map = pd.read_csv('./芯片参数/coupling_maps_overload.csv',index_col=False).values.tolist()
sub_map = [tuple(i) for i in coupling_map]
coupling_map = set(sub_map)

with open('./比特性能.csv','r') as f:
    qubit_properties = json.load(f)





    


def process_dict(input_dict):
    result_set = set()
    for key, value in input_dict.items():
        # 提取值中的数字部分并转换为整数
        value_num = int(value[1:])
        # 将键和值组成元组并添加到集合中
        result_set.add((key, value_num))
    return result_set
    








def remove_idle_qwires(circ):
    dag = circuit_to_dag(circ)
    idle_wires = list(dag.idle_wires())
    for w in idle_wires:
        # dag._remove_idle_wire(w)
        if type(w) is Clbit:
            dag.remove_clbits(w)
        else:
            dag.qubits.remove(w)

    dag.qregs = OrderedDict()

    return dag_to_circuit(dag)


def QSIC2QCircuit(QCIS:str)->QuantumCircuit:
    '''
    将QCIS代码转换为Qiskit 的QuantumCircuit对象
    '''
    new_qcis = QCIS_Simplify().simplify(QCIS)
    qasm = QcisToQasm.convert_qcis_to_qasm(new_qcis)
    QCircuit = qasm2.loads(qasm,
    custom_instructions=qasm2.LEGACY_CUSTOM_INSTRUCTIONS,
    custom_classical=qasm2.LEGACY_CUSTOM_CLASSICAL)
    QCircuit = remove_idle_qwires(QCircuit)
    clean_cir = QuantumCircuit(QCircuit.num_qubits, QCircuit.num_clbits)
    clean_cir.append(QCircuit, range(QCircuit.num_qubits), range(QCircuit.num_clbits))
    clean_cir = clean_cir.decompose()
    
    return clean_cir 




def summary_dag_circuit(dag_cir:DAGCircuit)->dict:
    single_qbits=[]
    two_qbits=[]
    for i in dag_cir.topological_op_nodes():
        if len(i.qargs) == 1:
            single_qbits.append(i.qargs[0]._index)
        else:
            for j in i.qargs:
                two_qbits.append(j._index)
    
    single_dict = Counter(single_qbits)
    double_dict = Counter(two_qbits)
    summary_dict = {'单比特门':single_dict, '双比特门':double_dict}
    return summary_dict
    
def qbits_connective_map(dag_circuit:DAGCircuit)->dict:
    '''
    返回dag_circuit的连接图
    '''
    connectivity_edges = set()  # 使用集合避免重复边

    for node in dag_circuit.op_nodes():
        qargs = [qubit._index for qubit in node.qargs]  # 获取涉及的量子比特
        if len(qargs) > 1:  # 如果是多比特门
            for i in range(len(qargs)):
                for j in range(i + 1, len(qargs)):
                    # 添加量子比特之间的连边，使用 set 避免重复
                    connectivity_edges.add(tuple(sorted([qargs[i], qargs[j]])))
    return connectivity_edges


def create_layout(mapping, num_qubits):
    """
    Create a layout mapping for Qiskit.

    Args:
        mapping (dict): A dictionary where keys are logical qubits (int)
                        and values are physical qubits (int).
        num_qubits (int): The number of logical qubits.

    Returns:
        dict: A layout mapping in the format {(QuantumRegister(n, 'qr'), i): j}.
    """
    qr = QuantumRegister(num_qubits, 'qr')
    layout = {}
    
    for logical_qubit, physical_qubit in mapping.items():
        layout[(qr, logical_qubit)] = physical_qubit

    return layout


def solve(QCIS:str):
    quamtum_cir = QSIC2QCircuit(QCIS)
    summary_dict = summary_dag_circuit(circuit_to_dag(quamtum_cir))
    qbits_connective_dict = qbits_connective_map(circuit_to_dag(quamtum_cir))
    my_map,score = find_best_mapping(logical_connectivity=qbits_connective_dict,logical_qubits_usage=summary_dict,physical_qubits=qubit_properties,coupling_map=coupling_map)
    print(f'初始化布局生效|score={score}|map={my_map}')
    basic_set = ['ry','rx','sx','cz','sxdg','cx','measure']
    cmap = CouplingMap(couplinglist=coupling_map)
    backend =GenericBackendV2(num_qubits=66,coupling_map=cmap)
    new_circ_lv0 = transpile(circuits=quamtum_cir,backend=backend,layout_method='sabre',optimization_level=2)
    qcis = QasmToQcis().convert_to_qcis(qasm2.dumps(new_circ_lv0))
    return new_circ_lv0, qcis