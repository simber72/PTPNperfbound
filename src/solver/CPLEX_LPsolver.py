#@Author: Simona Bernardi
#@Date: 02/08/2024
#!/usr/bin/python3
# -*- coding: UTF-8 -*-
#from typing import List


import cplex
from cplex.exceptions import CplexError
from scipy.sparse import dok_array #sparse array
from src.solver.LPsolver import LPsolver
from src.solver.ParamsExtractor import ParamsExtractor
from src.net.PTPN import PTPN

class CPLEX_LPsolver(LPsolver):
	"""Uses CPLEX API"""

	def __init__(self, tr_name, tr_id, type_of_prob):
		self.__tr_name = tr_name
		self.__tr_id = tr_id
		#Type of problem: min/max
		self.__prob_type = type_of_prob
		self.__prob = cplex.Cplex() #LP max X
		self.__ct_prob = None #LP min CT
		self.__pe = ParamsExtractor()
		##############################################################

	def populate_lp(self, ptpn: PTPN):
		#print("LP population of a ", self.__prob_type, " problem.")		
		
		#retrieve_net_structure(self, ptpn : PTPN)
		self.__pe.retrieve_net_structure(ptpn)

		#set problem name
		self.__prob.objective.set_name("obj" + self.__tr_name)
		#Debug
		print("Problem name:", self.__prob.objective.get_name())

		#set type of problem
		if self.__prob_type == "min":
			self.__prob.objective.set_sense(self.__prob.objective.sense.minimize)
			
		else:
			self.__prob.objective.set_sense(self.__prob.objective.sense.maximize)

		#Debug
		#print("Problem objective sense: ", self.__prob.objective.sense[self.__prob.objective.get_sense()])					

		self.__generate_lpX()
		##############################################################

	def solve_lp(self, ptpn: PTPN):
		#Solve the model
		print("Solving the LP problem...")

		try:
			self.__prob.solve()
			#Debug: display solutions
			print("====================================================")
			print("Solution status: ", self.__prob.solution.get_status()) # 1=optimal solution found
			print("Throughput of ", self.__tr_name, ":" ,self.__prob.solution.get_objective_value())				
			#Update PTPN
			self.__update_net(ptpn,"X")
			
		except CplexError as exc:
			raise

		if self.__prob.solution.get_objective_value() > 0: 
			#Identification of the reference transitions (from tr_name->tr_id->tr_dokid)
			tid2dokid = self.__pe.get_tid_to_dokid()
			trans = ptpn.get_transitions()
			values = self.__prob.solution.get_values()
			for k in tid2dokid.keys():
				tr_name = self.__get_name(trans,k)
				if tr_name == self.__tr_name:
					t_ref=tid2dokid[k] 
			#Identification of the slowest subnet		
			self.__identify_critical_subnet(values, t_ref, ptpn)
		else:
			print("The net is not live.")
		##############################################################

	def export_lp(self, pb, aFilename):
		#print("Export generated LP")
		pb.write(aFilename)
		##############################################################

	def export_lp_solution(self, pb, aFilename):
		pb.solution.write(aFilename)
		##############################################################

	def print_lp_solution(self, ptpn: PTPN, type_of_prob):
		if type_of_prob == 'max':
			self.__print_lp_max_X_solution(ptpn)
		else:
			self.__print_lp_min_CT_solution(ptpn)
		##############################################################

	def get_LpmaxX(self):
		return self.__prob 
		##############################################################

	def get_LpminCT(self):
		return self.__ct_prob
		##############################################################

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
		##############################################################

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
		##############################################################

	def __check_normalize(self, ecs, w):
		sum_of_weights = 0.0
		for t in ecs:
			sum_of_weights += w[t,0]
		if sum_of_weights != 1.0:
			for t in ecs:
				w[t,0] = w[t,0] / sum_of_weights #normalize
			print("The sum of weights in the ecs ", ecs, " has been normalized")
		##############################################################

	def __generate_lpX(self):

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
				#get the id of the tr_name!!
				if k == self.__tr_id:
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
		##############################################################
	
	def __backward_mapping(self):
		#Backward mapping of dok ids (ParamsExtractor) to place/transition ids (PTPN).
		pid2dokid = self.__pe.get_pid_to_dokid()
		tid2dokid = self.__pe.get_tid_to_dokid()
		dokid2pid = dict()
		for k in pid2dokid.keys():
			dokid2pid.update({pid2dokid[k]: k})
		dokid2tid = dict()	
		for k in tid2dokid.keys():
			dokid2tid.update({tid2dokid[k]: k})
		return dokid2pid,dokid2tid
		##############################################################

	def __check_belong_subnet(self,t,subnet_places,C):
		pre_t = 0
		post_t = 0
		for p in subnet_places:
			if C[p,t] < 0:
				pre_t += 1
			elif C[p,t] > 0:
				post_t += 1 
		return pre_t > 0 and post_t > 0 
		##############################################################

	def __get_name(self, obj_list, id):

		for obj in obj_list:
			if obj.get_id() == id:
				return obj.get_name()
		return None

	def __identify_critical_subnet(self, opt_sol, ref, ptpn):
		print("Critical subnet identification...")
		print("====================================================")
		pid_mapping = self.__pe.get_pid_to_dokid()
		tid_mapping = self.__pe.get_tid_to_dokid()
		np = len(pid_mapping)
		nt = len(tid_mapping)
		##############################################################
		#Compute visit vector from the solution of the primal LP
		v = []
		#print("Pid mapping", pid_mapping)
		#print("Tid mapping", tid_mapping)
		for k in tid_mapping.keys():
			v.append(opt_sol[np+nt+tid_mapping[k]]/opt_sol[np+nt+ref])
		#print("Visit ratios", v)
		#Solve max CT problem with v=v_0: y_0
		self.__ct_prob = cplex.Cplex() #create a new CPLEX instance
		self.__ct_prob.objective.set_sense(self.__ct_prob.objective.sense.maximize)

		##############################################################
		#Set objective function
		B = self.__pe.get_b()
		delta = self.__pe.get_delta()
		coef = []			
		y_names = []
		for p in pid_mapping.keys(): #pinv variables
			y_names.append('y' + str(pid_mapping[p])) 
			tot = 0
			for t in tid_mapping.keys():
				tot += B[pid_mapping[p],tid_mapping[t]]*delta[tid_mapping[t],0] * v[tid_mapping[t]]
			coef.append(float(tot))
		self.__ct_prob.variables.add(obj=coef, names=y_names)
		#print("All the variables: ", ct_prob.variables.get_names())
		#print(coef)

		##############################################################
		#Set conservative marking constraints: C^T y = 0			
		F = self.__pe.get_f()
		C = F-B
		n_constr = 0
		for t in tid_mapping.keys():
			ind = []
			val = []
			for p in pid_mapping.keys():
				if C[pid_mapping[p],tid_mapping[t]] != 0:
					ind.append(int(pid_mapping[p]))
					val.append(float(C[pid_mapping[p],tid_mapping[t]]))
			self.__ct_prob.linear_constraints.add(lin_expr=[cplex.SparsePair(ind, val)], rhs=[0.0], senses=["E"], names=['pinv'+str(n_constr)])
			n_constr += 1

		##############################################################
		#Set initial marking constraints: M0^T y = 1
		M0 = self.__pe.get_m0()
		ind = []
		val = []
		for p in pid_mapping.keys():
			if M0[0,pid_mapping[p]] > 0:
				ind.append(int(pid_mapping[p]))
				val.append(1.0)
		self.__ct_prob.linear_constraints.add(lin_expr=[cplex.SparsePair(ind, val)], rhs=[1.0], senses=["E"], names=['inimark'+str(n_constr)])
		
		##############################################################
		#Solve the lp problem
		try:
			self.__ct_prob.solve()
			#Debug: display solutions
			print("====================================================")
			print("Solution status: ", self.__ct_prob.solution.get_status()) # 1=optimal solution found
			print("Min cycle time ", self.__tr_name, ":" ,self.__ct_prob.solution.get_objective_value())	
			#Update PTPN
			self.__update_net(ptpn,"CT")

		except CplexError as exc:
			raise
		
	def __update_net(self, ptpn: PTPN, metric):
		#Update transition metric
		trans = ptpn.get_transitions()
		i = 0
		found = False
		while i < len(trans) and not found:
			if trans[i].get_name() == self.__tr_name:
				if metric == "X":
					trans[i].set_bounds(dict({'Throughput': [self.__prob_type, self.__prob.solution.get_objective_value()]}))
				else:
					trans[i].set_bounds(dict({'Cycle time': ['min', self.__ct_prob.solution.get_objective_value()]}))
				found = True 
				#Debug
				#print("PTPN updated: ", "Transition: ", trans[i].get_name(), "Bounds: ", trans[i].get_bounds())
			i += 1
		#Update subnet when cycle time has been computed
		if metric == 'CT':
			var = self.__ct_prob.variables.get_names()
			values = self.__ct_prob.solution.get_values()
			pid_mapping = self.__pe.get_pid_to_dokid()
			tid_mapping = self.__pe.get_tid_to_dokid()
			#Collecting places of the subnet
			places = ptpn.get_places()	
			
			subnet_places_pid2dokid = dict()
			for p in pid_mapping.keys():
				if values[pid_mapping[p]] > 0.0:
					subnet_places_pid2dokid.update({p:pid_mapping[p]})
			subnet_places = set()
			for pl in places:
				if pl.get_id() in subnet_places_pid2dokid.keys():
					subnet_places.add(pl)			
			subnet_trans = set()
			C = self.__pe.get_f() - self.__pe.get_b()
			for tr in trans:
				if self.__check_belong_subnet(tid_mapping[tr.get_id()], subnet_places_pid2dokid.values(), C):
					subnet_trans.add(tr)					
			ptpn.set_critical_subnet(dict({'places': subnet_places, 'trans': subnet_trans}))
			

	def __print_lp_max_X_solution(self,ptpn: PTPN):
		#Print optimal solution using PTPN place/transition names
		print("Solution:")
		values = self.__prob.solution.get_values()
		dokid2pid,dokid2tid = self.__backward_mapping()
		places = ptpn.get_places()
		trans = ptpn.get_transitions()
		for k in dokid2pid.keys():
			pl_name = self.__get_name(places,dokid2pid[k])
			if pl_name != None:
				print("M(", pl_name, "):",values[k])
		np=len(dokid2pid)
		nt=len(dokid2tid)
		for k in dokid2tid.keys():
			tr_name = self.__get_name(trans,dokid2tid[k])
			if tr_name != None:
				print("s(", tr_name,"):",values[np+int(k)])
				print("x(", tr_name,"):",values[np+nt+int(k)])
		print("====================================================")

	def __print_lp_min_CT_solution(self,ptpn: PTPN):
		#Slowest subnet from the updated PTPN
		print("Places of the slowest subnet:")
		subnet = ptpn.get_critical_subnet()
		for p in subnet['places']:
			print(p.get_name())
		print("Transitions of the slowest subnet:")
		for t in subnet['trans']:
			print(t.get_name())
		print("====================================================")




