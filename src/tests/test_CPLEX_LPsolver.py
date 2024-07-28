"""
@Author: Simona Bernardi
@Date: 19/07/2024

It tests the src.perfBoundSolver.LPgenerator module: 
- generation of an LP problem from the net structure
"""

#import io
import unittest
import os
from src.net.PTPN import PTPN
from src.perfBoundSolver.CPLEX_LPsolver import CPLEX_LPsolver

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
	lpgen = CPLEX_LPsolver('maxX','T9')
	#Test generated lp model
	lpgen.populate_lp(ptpn)
	#Test export lp model
	filename = os.getcwd() + path + net + '.lp'
	lpgen.export_lp(filename)
	#Test solving the model and getting the results
	lpgen.solve_lp()
	


if __name__ == '__main__':

	unittest.main()




