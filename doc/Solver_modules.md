# Solver modules and CLI

Modules are organized in two main packages:
1. ```net``` including the classes responsible of importing/exporting/printing the PTPN models
2. ```solver``` including the classes responsible of extracting the relevant information from the
net, generating the LPPs for the bound computation, solving the LPPs and mapping the results
to the PTPN model andupdating the PTPN models with the results.

The modules rely on the following Python external packages:

- ```cplex```: LPP model generation and its solution
- ```scipy```: Use of sparse matrices (dok arrays)
- ```graphviz```: Generation of ```dot``` graphical PTPN models

Beside, ```ptpnbound.py``` is the CLI script and relies on the ```click``` package.

Also, the following Python (internal) packages are used:

- ```xml.dom```: XML parsing of ```pnml``` PTPN models (```minidom``)
- ```math```: use of exponential function
- ```string```: generation of random IDs
- ```os```: operating system functionalities



## Dataflow/workflow overview 
The main workflow and the data loaded/stored are shown in the following
```mermaid
flowchart TB
%%Workflow
s1(Import PTPN) ==> s2(PTPT-to-SPN)
s2 ==> s3(Generate & Solve LP_X problem for transition t)   
%%Dataflow
d1[(PTPN model .pnml)] -.-> s1
s3 -.->d2[(LP_X model .lp/solution .xml)]
s3 ==> s4(Synthesize LP_X solution)
s4 --> s5{Is transition t live?}
s5 ==>|yes| s6[Generate & Solve LP_CT problem for transition t]
s6 ==> s7[Synthesize LP_CT optimal solution]
s6 -.-> d4[(LP_CT model .lp/solution .xml)]
s7 ==> s8
s5 ==>|no| s8[Export PTPN]
s8 -.->d3[(PTPN with performance results .pnml/.dot)]
classDef data  fill:#E5FFCC;
class d1,d2,d3,d4 data;
classDef step fill:#EEFFFF;
class s1,s2,s3,s4,s5,s6,s7,s8 step;
```

## Architecture
The ```net``` package includes the following clases:
```mermaid
classDiagram
	
	direction LR
	class PTPN{
		-net_id
		-page_id
		-name
		-subnet
		+import_pnml()
		+export_pnml()
		+export_dot()
		+print_net()
		+set_critical_subnet()
		+get_critical_subnet()
		+get_name()
		+get_arcs()
		+get_transitions()
		+get_places()
	}
	class Arc{
		-id
		-mult
		-dist_id
		-probability
		+get_id()
		+get_mult()
		+get_dist_id()
		+get_prob()
		+get_source()
		+get_target()
	}
	class Node
	<<abstract>> Node
	class Place{
		-id
		-name
		-initial_marking
		+get_id()
		+get_name()
		+get_initial_marking()
	}

	class Transition{
		-id
		-name
		-time_function
		-params
		-bounds
		+get_delay()
		+set_bounds()
		+get_bounds()
		+get_id()
		+get_name()
		+get_time_function()
		+get_params()
	}

	PTPN *--"1..*" Node
	PTPN *--"1..*" Arc
	Node <|-- Place
	Node <|-- Transition
	Arc "*"--"source" Node
	Arc "*"--"target" Node
```
The ```solver``` package includes the following clases:
```mermaid
classDiagram
	
	direction LR
	class LPsolver{
		populate_lp()
		solve_lp()
		export_lp()
		export_lp_solution()
		print_lp_solution()
	}
	<<interface>> LPsolver

	class CPLEX_LPsolver{
		-tr_name
		-tr_id
		-prob_type
		-prob: cplex.Cplex
		-ct_prob: cplex.Cplex
		+populate_lp()
		+solve_lp()
		+export_lp()
		+export_lp_solution()
		+print_lp_solution()
		+get_LpmaxX()
		+get_LpminCT()
		-check_conflict()
		-compute_ecs()
		-check_normalize()
		-generate_lpX()
		-backward_mapping()
		-check_belong_subnet()
		-get_name()
		-identify_critical_subnet()
		-update_net()
		-print_lp_max_X_solution()
		-print_lp_min_CT_solution()
	}
	class ParamsExtractor{
		-m0: scipy.sparse.dok_array
		-b: scipy.sparse.dok_array
		-f: scipy.sparse.dok_array
		-w: scipy.sparse.dok_array
		-delta: scipy.sparse.dok_array
		-pid_to_dokid
		-tid_to_dokid
		+retrieve_net_structure()
		+print_net_structure()
		+get_m0()
		+get_b()
		+get_f()
		+get_w()
		+get_delta()
		+get_pid_to_dokid()
		+get_tid_to_dokid()
		-identify_arc()
		-update_post_set()
	}

	CPLEX_LPsolver <|.. LPsolver
	CPLEX_LPsolver --"pe" ParamsExtractor
```

## Import/Output PTPN ```pnml``` format
The tool implements the import/export functionalities through XML deserialization/serialization.
An XML schema is defined for PTPN that is compliant with the standard PNML for Place-Transition nets.
Figure, reported below, shows the PTPN interchange format meta-model, where 
white classes are from the PNML meta-model and the colored classes represent the tool-specific
extensions. 
The yellow ones are core concepts of the PTPN formalism, i.e., discrete probability distributions over output places of a transition and continuous probability distributions associated to transition delays.
The blue classes are concepts related to the results obtained from the performance 
bound solver, i.e., the performance bounds and the slowest subnet.

<img src="https://github.com/simber72/PTPNperfbound/blob/main/doc/ptpn_pnml.png" width="1000">
