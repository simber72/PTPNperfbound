#@Author: Simona Bernardi
#@Date: 29/07/2024
#!/usr/bin/python3
# -*- coding: UTF-8 -*-
#from typing import List
from abc import ABC, abstractmethod


class LPsolver(ABC):
	"""@Interface Solver API"""
	
	@abstractmethod
	def populate_lp(self, aPTPN):
		pass
	
	@abstractmethod
	def solve_lp(self):
		pass

