# Solver modules

WIP


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
s3 -.-> OptSol[(PTPN internal results .xmi)]
classDef data  fill:#E5FFCC;
class PNsource,Opt,OptSol data;
classDef step fill:#00CCCC
class s1,s2,s3 step;
``
