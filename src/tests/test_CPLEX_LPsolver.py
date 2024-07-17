"""
@Author: Simona Bernardi
@Date: 18/07/2024

It tests the src.perfBoundSolver.LPgenerator module: 
- generation of an LP problem from the net structure
"""

#import io
import unittest
import os
from src.net.PTPN import PTPN
from src.perfBoundSolver.CPLEX_LPsolver import CPLEX_LPsolver

path = "/examples/"
net = "example1.pnml"


class TestLPgenerator(unittest.TestCase):


	#PTPN instantiation
	ptpn = PTPN(net)

	#Import PTPN pnml model
	filename = os.getcwd() + path + net
	ptpn.import_pnml(filename)
	print("PTPN ", net, "loaded")

	#Test LPgenerator instantiation
	lpgen = CPLEX_LPsolver('min')
	lpgen.generate_lp(ptpn)
	


if __name__ == '__main__':

	unittest.main()




