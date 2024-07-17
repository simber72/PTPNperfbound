#@Author: Simona Bernardi
#@Date: 18/07/2024
#!/usr/bin/python3
# -*- coding: UTF-8 -*-
#from typing import List


import cplex
from cplex.exceptions import CplexError

from src.perfBoundSolver.LPsolver import LPsolver
from src.perfBoundSolver.ParamsExtractor import ParamsExtractor
from src.net.PTPN import PTPN

class CPLEX_LPsolver(LPsolver):
	"""Uses CPLEX API"""

	def __init__(self,type_of_prob):
		#Type of LP problem: 'min' / 'max'
		self.__prob_type = type_of_prob

	def get_prob(self):
		return self.__prob_type

	def generate_lp(self, ptpn: PTPN):
		print("LP generation of a ", self.__prob_type, " problem.")
		
		#retrieve_net_structure(self, ptpn : PTPN)
		pe = ParamsExtractor()
		pe.retrieve_net_structure(ptpn)
		
		try:
			#create a new CPLEX_LP problem
			new_prob = cplex.Cplex()
			print("new CPLEX problem instance created")

			#set type of problem

			#set variables

			#set objective function

			#set constraints


		except CplexError as exc:
			raise

	def solve_lp(self, aProb):
		pass

	def identify_critical_subnet(self, aPtpn_solution):
		pass

	def export_lp(self, aFilename):
		print("Export generated LP ...TODO")
		pass


