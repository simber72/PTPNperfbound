#@Author: Simona Bernardi
#@Date: 03/08/2024
#!/usr/bin/python3
# -*- coding: UTF-8 -*-
#from typing import List

import string  #to generate random IDs
from xml.dom import minidom
import graphviz

from src.net.Transition import Transition
from src.net.Place import Place
from src.net.Arc import Arc

class PTPN:
	"""PTPNet container (includes also de page, assuming one page in a model)
	"""	
	def __init__(self,name):
		self.__net_id = None
		self.__page_id = None
		self.__name = name
		"""# @AssociationMultiplicity 1..*
		# @AssociationKind Composition"""
		self.__transitions = []
		self.__places = []
		"""# @AssociationMultiplicity 1..*
		# @AssociationKind Composition"""
		self.__arcs = []
		self.__subnet = None

	def set_critical_subnet(self,subnet):
		self.__subnet = subnet

	def get_critical_subnet(self):
		return self.__subnet

	def get_name(self):
		return self.__name

	def get_arcs(self):
		return self.__arcs

	def get_places(self):
		return self.__places

	def get_transitions(self):
		return self.__transitions
	
	def __get_text(self,element):
		"""Returns 'data' from <element><text>data</text></element>"""
		value_node_list = element.getElementsByTagName("text")
		return value_node_list[0].firstChild.data

	def __get_node(self,identifier,nodes_list):

		for node in nodes_list:
			if (node.get_id() == identifier):
				return node
		return None

	def import_pnml(self, filename):
		"""Parses 'filename' and loads the PTPN model"""
		model = minidom.parse(filename)

		#Load net and page id
		node_list = model.getElementsByTagName("net")
		self.__net_id = node_list[0].getAttribute("id")
		node_list =  node_list[0].getElementsByTagName("page")
		self.__page_id = node_list[0].getAttribute("id")

		#Load places
		place_node_list = model.getElementsByTagName("place")
		for p in place_node_list:
			pid = p.getAttribute("id")
			node_list = p.getElementsByTagName("name")
			name = self.__get_text(node_list[0])
			node_list = p.getElementsByTagName("initialMarking")
			m0 = 0 #default value
			#Initial marking field (optional)
			if node_list.length == 1:
				m0 = int(self.__get_text(node_list[0]))
			pl = Place(pid,name,m0)
			self.__places.append(pl)

		#Load transitions
		trans_node_list = model.getElementsByTagName("transition")
		for t in trans_node_list:
			tid = t.getAttribute("id")
			node_list = t.getElementsByTagName("name")
			name = self.__get_text(node_list[0])
			time_function = None #default value
			params = None #default value
			node_list = t.getElementsByTagName("time_function")
			if (node_list.length == 1):
				time_function = node_list[0].getAttribute("type")
				node_list = node_list[0].getElementsByTagName("param")
				params = dict()
				for p in node_list:
					par = p.getAttribute("name")
					value = float(self.__get_text(p))
					params.update({par : value})

			tr = Transition(tid,name,time_function,params)
			self.__transitions.append(tr)

		#Load arcs
		arc_node_list = model.getElementsByTagName("arc")
		for a in arc_node_list:
			aid = a.getAttribute("id")			
			source_id = a.getAttribute("source")
			target_id = a.getAttribute("target")
			source = self.__get_node(source_id,self.__places)
			if (source == None):
				source = self.__get_node(source_id,self.__transitions)
				target = self.__get_node(target_id,self.__places)
			else:
				target = self.__get_node(target_id,self.__transitions)
			if (source == None or target == None):
				raise Exception("Error in arc: ",aid) 

			mult = 0 #default value
			node_list = a.getElementsByTagName("inscription")
			if (node_list.length == 1):
				mult = int(self.__get_text(node_list[0]))
			
			did = None #default value (P/T net arc)
			prob = None #default value (P/T net arc)
			node_list = a.getElementsByTagName("distribution")
			if (node_list.length == 1): #it is an arc with distribution
				did = node_list[0].getAttribute("id")
				node_list = node_list[0].getElementsByTagName("probability")
				prob = float(self.__get_text(node_list[0]))

			arc = Arc(aid,mult,did,prob,source,target)
			self.__arcs.append(arc)
		
		#Debug
		#print("PTPN model loaded.")	
	
	#Debug purposes
	def print_net(self):
		print("id: ", self.__net_id, " name: ", self.__name, " page id: ", self.__page_id)
		print("=======")
		print("Places:")
		print("=======")
		for p in self.__places:
			pid = p.get_id()
			pname = p.get_name()
			m0 = p.get_initial_marking()
			print("ID:", pid, " name: ", pname, " m0: ", m0)

		print("============")
		print("Transitions:")
		print("============")
		for t in self.__transitions:
			tid = t.get_id()
			tname = t.get_name()
			tfunc = t.get_time_function()
			tparams = t.get_params()
			print("ID:", tid, " name: ", tname)
			print("----> time_function: ", tfunc)
			print("----> tparams: ", tparams)
			tdelay = t.get_delay()
			print("----> delay: ", tdelay)

		print("============")
		print("Arcs:")
		print("============")
		for a in self.__arcs:
			source_id = a.get_source().get_id()
			target_id = a.get_target().get_id()
			mult = a.get_mult()
			dist_id = a.get_dist_id()
			prob = a.get_prob()
			print("source_id: ", source_id, " target_id: ", target_id, " mult: ", mult)
			print("dist_id: ", dist_id, " prob: ", prob)

	def export_pnml(self,filename):
		"""
		Export the PTPN model to  pnml (if bounds are computed it exports the bound results)
		filename: filename.pnml is created
		"""
		#Heading
		ptpn = '<?xml version="1.0" encoding="iso-8859-1"?>\n'
		ptpn += '<pnml xmlns="http://www.pnml.org/version-2009/grammar/pnml">\n'
		ptpn += ' <net id="{0}" type="http://www.pnml.org/version-2009/grammar/ptnet">\n'.format(self.__net_id)
		ptpn += '  <page id="{0}">\n'.format(self.__page_id)
		#Places
		positionx = 0
		for p in self.__places:
			ptpn += '    <place id="{0}">\n'.format(p.get_id())
			ptpn += '     <graphics>\n'
			ptpn += '      <position x="{0}" y="150.0"/>\n'.format(positionx)
			ptpn += '     </graphics>\n'
			ptpn += '     <name>\n'
			ptpn += '      <text>{0}</text>\n'.format(p.get_name())
			ptpn += '     </name>\n'
			ptpn += '     <initialMarking>\n'
			ptpn += '      <text>{0}</text>\n'.format(p.get_initial_marking())
			ptpn += '     </initialMarking>\n' 
			ptpn += '    </place>\n'
			positionx += 50
		#Transitions
		positionx = 0
		for t in self.__transitions:
			ptpn += '    <transition id="{0}">\n'.format(t.get_id())
			ptpn += '     <graphics>\n'
			ptpn += '      <position x="{0}" y="240.0"/>\n'.format(positionx)
			ptpn += '     </graphics>\n'
			ptpn += '     <name>\n'
			ptpn += '      <text>{0}</text>\n'.format(t.get_name())
			ptpn += '     </name>\n'
			ptpn += '     <toolspecific tool="PTPNperfbound" version="0.1">\n'
			ptpn += '      <time_function type="{0}">\n'.format(t.get_time_function())
			for p, value in t.get_params().items():
				ptpn += '       <param name="{0}">\n'.format(p)
				ptpn += '         <text>{0}</text>\n'.format(value)
				ptpn += '       </param>\n'
			ptpn += '      </time_function>\n'
			bounds = t.get_bounds()
			if bounds:
				for b in bounds.keys():
					ptpn += '      <bound metric="{0}" statQ="{1}">\n'.format(b,bounds[b][0])
					ptpn += '       <text>{0}</text>\n'.format(bounds[b][1])
					ptpn += '      </bound>\n'
			ptpn += '     </toolspecific>\n'
			ptpn += '    </transition>\n'
			positionx += 50
		#Arcs
		for a in self.__arcs:
			ptpn += '    <arc id="{0}" source="{1}" target="{2}">\n'.format(a.get_id(), a.get_source().get_id(), a.get_target().get_id())
			ptpn += '     <inscription>\n'
			ptpn += '      <text>{0}</text>\n'.format(a.get_mult())  # arc multiplicity
			ptpn += '     </inscription>\n'
			did = a.get_dist_id()
			if (did != None):
				#PTPN arcs
				ptpn += '     <toolspecific tool="PTPNperfbound" version="0.1">\n'
				ptpn += '      <distribution id="{0}">\n'.format(did)
				ptpn += '        <probability>\n'
				ptpn += '          <text>{0}</text>\n'.format(a.get_prob())
				ptpn += '        </probability>\n'
				ptpn += '      </distribution>\n'
				ptpn += '     </toolspecific>\n'
			ptpn += '    </arc>\n'
		if self.__subnet:
			ptpn += '  <toolspecific tool="PTPNperfbound" version="0.1">\n'
			ptpn += '   <critical_subnet>\n'
			for p in self.__subnet['places']:
				ptpn += '    <pl id="{0}"/>\n'.format(p.get_id())
			for t in self.__subnet['trans']:
				ptpn += '    <tr id="{0}"/>\n'.format(t.get_id())
			ptpn += '   </critical_subnet>\n'
			ptpn += '  </toolspecific>\n'
		#Closings
		ptpn += '  </page>\n'
		ptpn += ' </net>\n'
		ptpn += '</pnml>'
		#Write to file
		f = open(filename, "w")
		f.write(ptpn)
		f.close()

	def export_dot(self,filename):
		dot = graphviz.Digraph(comment=self.__name)
		dot.attr(rankdir='TB')  # vertical
		for p in self.__places:			
			if p in self.__subnet['places']:
				dot.node(p.get_name(), shape='circle', label="•"*p.get_initial_marking(), xlabel=p.get_name(), color="red")
			else:
				dot.node(p.get_name(), shape='circle', label="point"*p.get_initial_marking(), xlabel=p.get_name())
		for t in self.__transitions:
			if t in self.__subnet['trans']:
				if t.get_bounds():
					label = "bounds:\n Thr:" + str(t.get_bounds()['Throughput']) + "\n CT:" + str(t.get_bounds()['Cycle time'])
					dot.node(t.get_name(), shape='rect', color="red", xlabel=label)
				else:
					dot.node(t.get_name(), shape='rect', color="red")
			else:
				dot.node(t.get_name(), shape='rect')
		for a in self.__arcs:
			target = a.get_target()
			if target in self.__transitions:
				#Input arc
				dot.edge(a.get_source().get_name(), target.get_name(), label=str(a.get_mult()))
			else:
				#Output arc
				if a.get_dist_id() != None:
					dot.node(a.get_id(), shape='point',label="")
					dot.edge(a.get_source().get_name(), a.get_id(), label=str([a.get_dist_id(),a.get_prob()]), style='dashed')
					dot.edge(a.get_id(), target.get_name(), label=str(a.get_mult()))
				else:
					dot.edge(a.get_source().get_name(), target.get_name(), label=str(a.get_mult()))

		dot.render(filename)





		

