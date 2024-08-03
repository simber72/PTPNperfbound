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
```mermaid
flowchart TB
%%Workflow
s1(Load the PTPN) ==> s2(Generate LPP models)
s2 ==> s3(Solve the problem)   
%%Dataflow
PNsource[(PTPN model .pnml)] -.-> s1
s2 -.->Opt[(LPP models .lp)]
Opt -.-> s3
s3 -.-> OptSol[(CPLEX model results .xmi)]
s3 ==> s4(Save PTPN results)
s4 -.->BoundRes(PTPN results .pnml/.dot)
classDef data  fill:#E5FFCC;
class PNsource,Opt,OptSol,BoundRes data;
classDef step fill:#00CCCC
class s1,s2,s3,s4 step;
```

## Architecture
==WIP==

