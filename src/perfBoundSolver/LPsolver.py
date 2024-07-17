#@Author: Simona Bernardi
#@Date: 18/07/2024
#!/usr/bin/python3
# -*- coding: UTF-8 -*-
#from typing import List
from abc import ABC, abstractmethod


class LPsolver(ABC):
	"""@Interface Solver API"""
	
	@abstractmethod
	def generate_lp(self, aPTPN):
		pass
	
	@abstractmethod
	def solve_lp(self, aProb):
		pass

	@abstractmethod
	def identify_critical_subnet(self, aPtpn_solution):
		pass

