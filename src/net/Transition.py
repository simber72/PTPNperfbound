#@Author: Simona Bernardi
#@Date: 02/08/2024
#!/usr/bin/python3
# -*- coding: UTF-8 -*-
#from typing import List

import math #expo. computation

class Transition:
	"""Transition of probabilistic time Petri net"""
	def __init__(self,tid,name,time_function,params):
		self.__id = tid
		self.__name = name
		self.__time_function = time_function
		self.__params = params #dict()
		self.__bounds = dict()

	def set_bounds(self,bounds):
		 self.__bounds.update(bounds)

	def get_bounds(self):
		return self.__bounds

	def get_id(self):
		return self.__id
		
	def get_name(self):
		return self.__name

	def get_time_function(self):
		return self.__time_function

	def get_params(self):
		return self.__params

	def get_delay(self):
		"""
		Returns the firing <mean> delay depending on the time function.
		In case of just "interval" (not distribution), returns the earliest firing time 
		"""
		if self.__time_function == "exponential":
			#Expected one param: lambda
			return 1 / self.__params['lambda']
		elif self.__time_function == "gamma":
			#Expected three params: k (shape), theta (scale), gamma_k(?) 
			return self.__params['k'] * self.__params['theta']
		elif self.__time_function == "normal":
			#Expected two params: mu (mean), sigma (std deviation)
			return self.__params['mu']
		elif self.__time_function == "lognormal":
			#Expected two params: mu (mean), sigma (std deviation)
			return math.exp(self.__params['sigma'] ** 2 / 2 + self.__params['mu'])
		elif self.__time_function == "uniform":
			#Expected two params: min, max (uniform distribution)
			return (self.__params['max'] + self.__params['min']) / 2
		elif self.__time_function == "interval":
			#Expected two params: min, max (just interval)
			return (self.__params)['min']
		elif self.__time_function == "constant":
			#Expected one param: k (constant time)
			return self.__params['k']
		else:
			return 0


