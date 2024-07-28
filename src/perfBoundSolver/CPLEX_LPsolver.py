#@Author: Simona Bernardi
#@Date: 28/07/2024
#!/usr/bin/python3
# -*- coding: UTF-8 -*-
#from typing import List


import cplex
from cplex.exceptions import CplexError
from scipy.sparse import dok_array #sparse array
from src.perfBoundSolver.LPsolver import LPsolver
from src.perfBoundSolver.ParamsExtractor import ParamsExtractor
from src.net.PTPN import PTPN

class CPLEX_LPsolver(LPsolver):
	"""Uses CPLEX API"""

	def __init__(self,type_of_prob,tr_name):
		#Type of LP problem: 'minCT' / 'maxX' and net transition name
		self.__prob_type = type_of_prob
		self.__tr_name = tr_name
		self.__prob = cplex.Cplex() #create a new CPLEX instance
		print("new CPLEX problem instance created")
		self.__pe = ParamsExtractor()

	def __check_conflict(self, tr, ecs, B):
		np = B.shape[0]
		i=0
		input_tr = set() #input set of tr
		input_ecs = set() #input set of ecs
		while i < np:
			if B[i,tr] > 0:
				input_tr.add(i)
			for t in ecs:
				if B[i,t] > 0:
					input_ecs.add(i)
			i += 1
			#Equal conflic sets condition
		return input_tr == input_ecs
		#Extended conflic sets condition
		#intersection = input_tr.intersection(input_ecs)
		#return True if len(intersection) > 0 else False 

	def __compute_ecs(self):
		B = self.__pe.get_b()
		nt = B.shape[1]
		tr_set = {t for t in range(1,nt)}
		ecs = dict({0:{0}})
		while len(tr_set)>0: #over the set of transitions
			t1 = tr_set.pop()
			found = False
			k = 0
			while not found and k<len(ecs.keys()):
				if self.__check_conflict(t1,ecs[k],B):
					ecs[k].add(t1)
					found = True
				else:
					k += 1
			if not found:
				ecs.update({k: {t1}})
		return ecs

	def __check_normalize(self, ecs, w):
		sum_of_weights = 0.0
		for t in ecs:
			sum_of_weights += w[t,0]
		if sum_of_weights != 1.0:
			for t in ecs:
				w[t,0] = w[t,0] / sum_of_weights #normalize
			print("The sum of weights in the ecs ", ecs, " has been normalized")

	def __generate_lpminCT(self):
		pass

	def __generate_lpmaxX(self):

		try:
			##############################################################
			#Set variables and coeff. of the objective function
			pid2dokid = self.__pe.get_pid_to_dokid()
			tid2dokid = self.__pe.get_tid_to_dokid()

			coef = []			
			v_names = []
			for k in pid2dokid.keys(): #marking variables
				v_names.append('M' + str(pid2dokid[k])) 
				coef.append(0.0)

			for k in tid2dokid.keys(): #number of firings variables
				v_names.append('s' + str(tid2dokid[k]))
				coef.append(0.0)

			for k in tid2dokid.keys(): #throughput variables
				v_names.append('x' + str(tid2dokid[k]))
				if k == self.__tr_name:
					coef.append(1.0)
				else:
					coef.append(0.0)

			#Set objective function
			self.__prob.variables.add(obj=coef, names=v_names)
			#print("All the variables: ", self.__prob.variables.get_names())
			
			n_constr = 0 #constraints counter
			##############################################################
			#Set reachability constraints: M - C s^T = M_0
			C =  self.__pe.get_f() - self.__pe.get_b()
			M0 = self.__pe.get_m0()
			np = C.shape[0]
			nt = C.shape[1]
			for p in range(np):
				ind =[p]
				val =[1.0]
				for t in range(nt):
					if C[p,t] != 0:
						ind.append(int(np+t))
						val.append(float(-C[p,t]))
				#print(ind,val)
				self.__prob.linear_constraints.add(lin_expr=[cplex.SparsePair(ind,val)], rhs=[float(M0[0,p])], senses=["E"], names=['reach'+str(n_constr)])
				n_constr +=1

			##############################################################
			#Set conservative flow constraints: C x^T = 0			
			for i in range(np):
				ind = []
				val = []
				for j in range(nt):
					if C[i,j] != 0:
						ind.append(int(np+nt+j))
						val.append(float(C[i,j]))
				self.__prob.linear_constraints.add(lin_expr=[cplex.SparsePair(ind, val)], rhs=[0.0], senses=["E"], names=['flow'+str(n_constr)])
				n_constr += 1
			
			##############################################################
			#Set Little's law constraints: M - delay * B x^T >= 0
			delta = self.__pe.get_delta()
			B = self.__pe.get_b()
			for t in range(nt):
				for p in range(np):
					if B[p,t] != 0 and delta[t,0] > 0:
						ind = [p, int(np+nt+t)]
						val = [1.0, -delta[t,0]*B[p,t]]
						self.__prob.linear_constraints.add(lin_expr=[cplex.SparsePair(ind,val)], rhs=[0.0], senses=["G"], names=['little'+str(n_constr)])
						n_constr +=1

			##############################################################
			#Set routing constraints: 
			ecs=self.__compute_ecs() #compute equal conflict sets 
			w = self.__pe.get_w()
			for k in ecs.keys():
				if len(ecs[k]) > 1: #conflicting transitions
					self.__check_normalize(ecs[k],w)
					#print("Checked and possibly normalized w: ", w)
					ecs_list = list(ecs[k])
					for t in ecs[k]:		
						ind = [int(t+np+nt)]
						val = [1.0-w[t,0]]
						for t1 in ecs_list:
							if t1 != t:
								ind.append(int(t1+np+nt))
								val.append(-w[t,0])
						self.__prob.linear_constraints.add(lin_expr=[cplex.SparsePair(ind,val)],rhs=[0.0],senses=["E"],names=['routing'+str(n_constr)])
						n_constr += 1
			
		except CplexError as exc:
			raise


	def populate_lp(self, ptpn: PTPN):
		print("LP population of a ", self.__prob_type, " problem.")		
		
		#retrieve_net_structure(self, ptpn : PTPN)
		self.__pe.retrieve_net_structure(ptpn)

		#set problem name
		self.__prob.objective.set_name("obj" + self.__tr_name)
		#Debug
		print("Problem name:", self.__prob.objective.get_name())

		#set type of problem
		if self.__prob_type == "minCT":
			self.__prob.objective.set_sense(self.__prob.objective.sense.minimize)
			self.__generate_lpminCT()
		else:
			self.__prob.objective.set_sense(self.__prob.objective.sense.maximize)
			self.__generate_lpmaxX()
			#Debug
			print("Problem objective sense: ", self.__prob.objective.sense[self.__prob.objective.get_sense()])					

	def solve_lp(self):

		#Solve the model
		print("Solving the model...")

		try:
			self.__prob.solve()
			#Debug: display solutions
			print("Solution status: ", self.__prob.solution.get_status()) # 1=optimal solution found
			if self.__prob_type == "minCT":
				print("Minimum cycle time of", self.__tr_name)
			else:
				print("Maximum throughput of ", self.__tr_name, ":" ,self.__prob.solution.get_objective_value())			
			
			print("Solution values:")
			var = self.__prob.variables.get_names()
			values = self.__prob.solution.get_values()

		except CplexError as exc:
			raise

		#Backward mapping of dok ids (ParamsExtractor) to place/transitions ids (PTPN).
		pid2dokid = self.__pe.get_pid_to_dokid()
		tid2dokid = self.__pe.get_tid_to_dokid()
		np = len(pid2dokid)
		nt = len(tid2dokid)
		dokid2pid = dict()
		for k in pid2dokid.keys():
			dokid2pid.update({pid2dokid[k]: k})
		dokid2tid = dict()	
		for k in tid2dokid.keys():
			dokid2tid.update({tid2dokid[k]: k})
		
		for k in dokid2pid.keys():
			print("M(", dokid2pid[k], "):",values[k])
		for k in dokid2tid.keys():
			print("s(", dokid2tid[k],")",values[np+int(k)])
			print("x(", dokid2tid[k],")",values[np+nt+int(k)])

	def identify_critical_subnet(self, aPtpn_solution):
		pass

	def export_lp(self, aFilename):
		print("Export generated LP")
		self.__prob.write(aFilename)


