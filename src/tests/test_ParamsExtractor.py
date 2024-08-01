"""
@Author: Simona Bernardi
@Date: 19/07/2024

It tests the src.perfBoundSolver.ParamsExtractor module: 
it retrieves information of the PTPN by transforming it to a GenSPN
"""

#import io
import unittest
import os
from src.net.PTPN import PTPN
from src.solver.ParamsExtractor import ParamsExtractor

path = "/examples/"
net = "example1.pnml"


class TestPTPN2GenSPN(unittest.TestCase):


	#Test if PTPN can be instantiated
	ptpn = PTPN(net)

	#Test import_pnml functionality
	filename = os.getcwd() + path + net
	ptpn.import_pnml(filename)
	#ptpn.print_net()

	#Text ParamesExtractor methods
	pe = ParamsExtractor()
	pe.retrieve_net_structure(ptpn)
	pe.print_net_structure()



if __name__ == '__main__':

	unittest.main()




