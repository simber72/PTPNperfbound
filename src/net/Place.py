#@Author: Simona Bernardi
#@Date: 18/07/2024
#!/usr/bin/python3
# -*- coding: UTF-8 -*-
#from typing import List

class Place:
	"""Place of probabilistic time Petri net"""

	def __init__(self,pid,name,m0):
		self.__id = pid
		self.__name = name
		self.__initial_marking = m0

	def get_id(self):
		return self.__id
		
	def get_name(self):
		return self.__name

	def get_initial_marking(self):
		return self.__initial_marking

