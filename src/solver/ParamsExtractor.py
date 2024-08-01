#@Author: Simona Bernardi
#@Date: 28/7/2024
#!/usr/bin/python3
# -*- coding: UTF-8 -*-
#from typing import List

from scipy.sparse import dok_array #Dictionary Of Keys based sparse array
from src.net.PTPN import PTPN

class ParamsExtractor:
	def __init__(self):
		self.__m0 = None
		self.__b = None
		self.__f = None
		self.__w = None
		self.__delta = None
		#Dictionary for mapping net infos to the net structures
		self.__pid_to_dokid = dict()
		self.__tid_to_dokid = dict()

	def __identify_arc(self, tid, a):

		source_id = a.get_source().get_id()
		target_id = a.get_target().get_id()
		if tid == source_id:
			kind = 'O'
			connected_place = target_id
		elif tid == target_id:
			kind = 'I'
			connected_place = source_id
		else:
			kind = 'N'
			connected_place=None
		return kind, connected_place

	def __update_post_set(self, post_set, key, value):

		if key in post_set.keys():
			#key is already in the dictionary: update the corresponding value to val
			post_set[key].append(value)
		else:
			#new key: add (key,val) to the dictionary
			post_set.update({key: [value]})

	def get_m0(self):
		return self.__m0

	def get_b(self):
		return self.__b

	def get_f(self):
		return self.__f

	def get_w(self):
		return self.__w

	def get_delta(self):
		return self.__delta

	def get_pid_to_dokid(self):
		return self.__pid_to_dokid

	def get_tid_to_dokid(self):
		return self.__tid_to_dokid

	def retrieve_net_structure(self, ptpn : PTPN):

		places = ptpn.get_places()
		trans = ptpn.get_transitions()

		#Set initial structures dimension
		self.__m0 = dok_array((1,len(places)),dtype=int)
		self.__b = dok_array((len(places),len(trans)),dtype=int)
		self.__f = dok_array((len(places),len(trans)),dtype=int)
		self.__w = dok_array((len(trans),1),dtype=float)
		self.__delta = dok_array((len(trans),1),dtype=float)
		

		for i in range(len(places)):
			self.__pid_to_dokid.update({places[i].get_id() : i})
			#update m0
			self.__m0[0,i] = places[i].get_initial_marking()
			
		for i in range(len(trans)):
			self.__tid_to_dokid.update({trans[i].get_id() : i})
			#update r and delta
			self.__w[i,0] = 1.0 #original transitions have weights 1
			self.__delta[i,0] = trans[i].get_delay()

		#Debug
		#print("-----------------------------")
		#print("initial structure")
		#print("-----------------------------")
		#self.print_net_structure()
		
		arcs = ptpn.get_arcs()
		#Complexity: O(|T|*|A| + |T|*MAX_DIST*MAX_OUTCOMES) ~ O(|T|*|A|), where:
		#MAX_DIST = max no. of transition distributions  
		#MAX_OUTCOMES = max no. of distribution outcomes
		for t in trans:
			#b and f are filled considering the transition view point 
			post_set = dict() # {dist_id : [pid,mult,prob]}
			tid = t.get_id()
			for arc in arcs:
				#Identify the kind of arc I/O/N connecting  t and return the connecting place id
				kind, pid = self.__identify_arc(tid,arc)
				if kind == 'I':
					#update b using the mapping 
					self.__b[ self.__pid_to_dokid[pid], self.__tid_to_dokid[tid] ] = 1
				elif kind == 'O':
					#update post-set
					key = arc.get_dist_id()
					value = [pid, arc.get_mult(), arc.get_prob()]
					self.__update_post_set(post_set, key, value)
			#Considering the post_set a net transformation is needed (new places/new transitions)
			#PTPN->GeneralizedSPN
			for d in post_set.keys():
				#print(d,post_set[d])
				if d != None:
					#Add a new place p with pid_p=tid + "_" + dist (must be unique!)
					pid_p = tid + "_" + str(d)
					#Update the mapping pid_to_idx
					self.__pid_to_dokid.update({pid_p: len(self.__pid_to_dokid)})
					#Resize m0 (+element): set 0 as initial_marking to the new p entry as 
					self.__m0.resize((1,len(self.__pid_to_dokid)))
					self.__m0[0,self.__pid_to_dokid[pid_p]] = 0
					#Resize b (+row)
					self.__b.resize((len(self.__pid_to_dokid),len(self.__tid_to_dokid)))
					#Resize f (+row): set 1 as multiplicity of the new arc t->p
					self.__f.resize((len(self.__pid_to_dokid),len(self.__tid_to_dokid)))
					self.__f[self.__pid_to_dokid[pid_p], self.__tid_to_dokid[tid] ] = 1

					for pid,mult,prob in post_set[d]:
						#Add a new transition tnew with tid_t'=pid_p + "_" + pid (must be unique!)
						tid_tnew = pid_p + "_" + pid
						#Update the mapping tid_to_idx
						self.__tid_to_dokid.update({tid_tnew: len(self.__tid_to_dokid)})
						#Resize w (+element): set "prob" as weight of the new transition tnew
						self.__w.resize((len(self.__tid_to_dokid),1))
						self.__w[self.__tid_to_dokid[tid_tnew],0] = prob
						#Resize delta (+element): set "0.0" as delay of the new transition tnew (immediate)
						self.__delta.resize((len(self.__tid_to_dokid),1))
						self.__delta[self.__tid_to_dokid[tid_tnew],0] = 0.0
						#Resize b(+column): set 1 as multiplicity of the new arc p->tnew
						self.__b.resize((len(self.__pid_to_dokid),len(self.__tid_to_dokid)))
						self.__b[self.__pid_to_dokid[pid_p], self.__tid_to_dokid[tid_tnew]] = 1
						#Resize f(+column): set "mult" as multiplicity of the new arc tnew->pid
						self.__f.resize((len(self.__pid_to_dokid),len(self.__tid_to_dokid)))
						self.__f[self.__pid_to_dokid[pid], self.__tid_to_dokid[tid_tnew]] = mult
				else:
					pid,mult,_ = post_set[d][0]
					self.__f[self.__pid_to_dokid[pid], self.__tid_to_dokid[tid] ] = mult

			#Debug
			#self.print_net_structure()
		#return self.__m0, self.__b, self.__f, self.__r, self.__delta

	#Debug purpose
	def print_net_structure(self):

		print("========================================")
		print(len(self.__pid_to_dokid), " places.")
		print("Place mapping: ")
		print(self.__pid_to_dokid)

		print(len(self.__tid_to_dokid), " transitions.")
		print("Transition mapping: ")
		print(self.__tid_to_dokid)

		print("Initial marking: ")
		print(self.__m0)

		print("Pre-incidence matrix: ")
		print(self.__b)

		print("Post-incidence matrix: ")
		print(self.__f)

		print("Transition weights: ")
		print(self.__w)

		print("Transition mean firing times: ")
		print(self.__delta)
