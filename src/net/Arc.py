#@Author: Simona Bernardi
#@Date: 18/07/2024
#!/usr/bin/python3
# -*- coding: UTF-8 -*-
#from typing import List

class Arc:
	def __init__(self,aid,mult,dist_id,probability,source,target):
		"""Arc of probabilistic time Petri net:
			P/T net arcs: __dist_id = None, __probability= None
		"""
		self.__id = aid
		self.__mult = mult
		self.__dist_id = dist_id
		self.__probability = probability
		self.__source =  source
		self.__target =  target

	def get_id(self):
		return self.__id
		
	def get_mult(self):
		return self.__mult

	def get_dist_id(self):
		return self.__dist_id

	def get_prob(self):
		return self.__probability

	def get_source(self):
		return self.__source

	def get_target(self):
		return self.__target



