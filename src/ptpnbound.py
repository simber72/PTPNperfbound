"""
@Author: Simona Bernardi
@Date: 02/08/2024
Entry point of PTPN performance bound solver
"""

import os
import click #CLI

from src.net.PTPN import PTPN
from src.solver.CPLEX_LPsolver import CPLEX_LPsolver

def transition_exist(ptpn,tname):
    #Check existence of transition with name "tname" in "ptpn"
    tr_list = ptpn.get_transitions()
    for tr in tr_list:
        if tr.get_name() == tname:
            return True
    return False

def get_transition_id(ptpn,tname):
    tr_list = ptpn.get_transitions()
    for tr in tr_list:
        if tr.get_name() == tname:
            return tr.get_id()
    return -1


@click.command()
@click.argument('name')
@click.argument('tname')
@click.option('-lp','--lpmodel', type=str, help="LP model files (CPLEX  models - lp format)")
@click.option('-lpo','--lpoutput', type=str, help="Result files (CPLEX model results - xml format)")
@click.option('-o','--output', type=(str,str), help="Result file: name format (available formats: pnml, dot)")
@click.option('-v','--verbose', is_flag=True, show_default=True, default=False, help="Print results to stdin")
def ptpnbound(name, tname, lpmodel, lpoutput, output, verbose):

    #Load net 
    filename = os.path.join(os.getcwd(), name + ".pnml")
    if not os.path.isfile(filename):
        click.echo(f"Oops!  The file {filename} does not exists. Terminate.")
    else:
        click.echo(f"Loading PTPN net: {filename}")
        ptpn = PTPN(name)
        ptpn.import_pnml(filename)
        if not transition_exist(ptpn,tname):
            click.echo(f"Oops!  The transition {tname} does not exists. Terminate.")
        else:
            tid = get_transition_id(ptpn,tname)
            click.echo(f"Computing max throughput/min cycle time of transition: {tname}")
            #Generate LP-max problem
            lpgen = CPLEX_LPsolver(tname,tid,'max')
            lpgen.populate_lp(ptpn)
            #Solve LP
            click.echo("===============================================================")
            lpgen.solve_lp(ptpn)

            #Save lp models (CPLEX .lp format)
            if lpmodel:
                filename = os.path.join(os.getcwd(), name + "_lp_max_X.lp")
                lpgen.export_lp(lpgen.get_LpmaxX(), filename)
                if lpgen.get_LpminCT() != None:
                    filename = os.path.join(os.getcwd(), name + "_lp_CT.lp")
                    lpgen.export_lp(lpgen.get_LpminCT(), filename)

            #Save CPLEX model results (xml format)
            if lpoutput:
                filename = os.path.join(os.getcwd(), name + "_lp_max_X_sol.xml")
                lpgen.export_lp_solution(lpgen.get_LpmaxX(), filename)
                if lpgen.get_LpminCT() != None:
                    filename = os.path.join(os.getcwd(), name + "_lp_CT_sol.xml")
                    lpgen.export_lp_solution(lpgen.get_LpminCT(), filename)

            #Save the results in the PTPN model (pnml/dot)
            if output:
                if output[1] == 'pnml':
                    filename = os.path.join(os.getcwd(), output[0] + ".pnml")
                    #PTPN model to be enriched with solution results 
                    ptpn.export_pnml(filename)
                    print("The PTPN model with the results have been exported: ", filename)
                elif output[1] == 'dot':
                    print("Export to graphiz .dot WIP")
                    filename = os.path.join(os.getcwd(), output[0] + ".dot")
                    ptpn.export_dot(filename)
                else:
                    click.echo(f"{output[1]} is not a valid format")

            #Print solutions on stdin
            if verbose:
                lpgen.print_lp_max_X_solution(ptpn)
                if lpgen.get_LpminCT() != None:
                    lpgen.print_lp_min_CT_solution(ptpn)



if __name__ == '__main__':
    ptpnbound()