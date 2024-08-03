"""
@Author: Simona Bernardi
@Date: 03/08/2024

It tests the src/net module: 
- import/export/print functionalities of PTPN class
- Place, Transition and Arcs classes are tested also with this test
"""

#import io
import unittest
import os
from src.net.PTPN import PTPN

path = "/examples/"
net = "example1.pnml"

class TestPTPN(unittest.TestCase):


	#Test if PTPN can be instantiated
	ptpn = PTPN(net)

	#Test import_pnml functionality
	filename = os.getcwd() + path + net
	ptpn.import_pnml(filename)

	#Test print_net functionality
	ptpn.print_net() 

	#Test export_pnml functionality
	filename = filename + ".pnml"
	ptpn.export_pnml(filename)


if __name__ == '__main__':

	unittest.main()




