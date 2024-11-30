"""
@Author: Simona Bernardi
@Date: 01/08/2024

It tests the src.perfBoundSolver.LPgenerator module: 
- generation of an LP problem from the net structure
"""

#import io
import unittest
import os
from src.net.PTPN import PTPN
from src.solver.CPLEX_LPsolver import CPLEX_LPsolver

path = "/examples/"
net = "example1"


class TestLPgenerator(unittest.TestCase):


	#PTPN instantiation
	ptpn = PTPN(net)

	#Import PTPN pnml model
	filename = os.getcwd() + path + net + '.pnml'
	ptpn.import_pnml(filename)
	print("PTPN ", net, "loaded")

	#Test LPgenerator instantiation
	lpgen = CPLEX_LPsolver('T9','T9','max')
	#Test generated lp model
	lpgen.populate_lp(ptpn)
	#Test export lp model
	filename = os.getcwd() + path + net + '.lp'
	lpgen.export_lp(lpgen.get_LpmaxX(), filename)
	#Test solving the model and getting the results
	lpgen.solve_lp(ptpn)
	#Test printing solution at the original PTPN level
	lpgen.print_lp_solution(ptpn,'max')
	#Test exporting lp and lp solutions (CPLEX format - internal model)
	filename = os.getcwd() + path + net + '.lpX_sol'
	lpgen.export_lp_solution(lpgen.get_LpmaxX(), filename)
	
	if lpgen.get_LpminCT() != None:
		lpgen.print_lp_solution(ptpn,'min')
		filename = os.getcwd() + path + net + '.lpCT_sol'
		lpgen.export_lp_solution(lpgen.get_LpminCT(), filename)
	

if __name__ == '__main__':

	unittest.main()




