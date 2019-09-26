# -*- coding: utf-8 -*-

'''
Script Name:	ping_services.py
Path:			\IPS_DecisionFabric\Exception Handling\
Description:	This script is considered as a module for the Ping Utility in DF framework.
Author:			Yogesh Suryawanshi
Revision History:
----------------------------------------------------------------------------------------------------------------------
S.No.			Date(MM/DD/YY)		Changed By			Change Description 	
----------------------------------------------------------------------------------------------------------------------
1.				05/10/2019			Y Suryawanshi		Initial Version (Exception Handling v1.1.1)
2.				06/20/2019			Y Suryawanshi		Fixed the bug for ISODate object
----------------------------------------------------------------------------------------------------------------------
'''

try:
	import socket
	import logging
	import pandas as pd
	import os, sys
	from datetime import datetime
except ImportError as IE:
	logging.error("All modules are not imported successfully! {}".format(IE))
	
class Mysocket:
	""" Initiallise the socket object """
	def __init__(self):
		self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

	def get_response(self, sock_ip, sock_port, sock_app):
		self._ip = sock_ip
		self._appname = sock_app
		self.status = ""
		self._port = int(sock_port)
		
		# Check Application Status
		try:
			self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
			self.sock.connect((self._ip, self._port))
			self.sktstatus = "UP"
			logging.info("[{0}:{1}]\t'{2}'\tApplication is 'UP'".format(self._ip, self._port, self._appname))
		except:
			self.sktstatus = "DOWN"
			logging.info("[{0}:{1}]\t'{2}'\tApplication is 'DOWN'".format(self._ip, self._port, self._appname))

		return {"Time": datetime.now(), "IP": self._ip, "Port": self._port,
				"Application": self._appname, "App_Status": self.sktstatus}
	
	
class Configuration_file:
	"""The file object to initiallise configurations"""
	def __init__(self, filename):
		"""Initialize the Configfile object"""
		self.filename = filename
		self.ip_port_tuplelst = []
		self.ip_port_str = []

	def read_config(self):
		""" returns touple for all applications"""
		# self.ip_port_tuplelst = []
		fp = open(self.filename)
		try:
			content = fp.read()
			logging.debug("{} File has been read".format(self.filename))
		except IOError as Errormsg:
			logging.error("Unable to read {0}\n{1}".format(self.filename, Errormsg))
		finally:
			fp.close()
			
		try:
			if content:
				for index, eachline in enumerate(content.split('\n')):
					if index != len(content.split('\n'))-1: 
						line = eachline.split("\t")
						ip = line[0].split("=")[1]
						port = line[1].split("=")[1]
						app = line[2].split("=")[1]
						self.ip_port_tuplelst.append((ip, port, app))
				return self.ip_port_tuplelst
		except:
			logging.debug("Unable to read the content of {}".format(self.filename))


def create_dict(dict_csv, Status, app_id_dict, process_Id, res, count):
	dict_csv["Application_name"].append(Status["Application"])
	dict_csv["Application_ID"].append(app_id_dict[Status["Application"]])
	if res == True:
		dict_csv["Process_ID"].append("")
	else:
		dict_csv["Process_ID"].append(process_Id["Application_Down"])
	dict_csv["IP"].append(Status["IP"])
	dict_csv["Port"].append(Status["Port"])
	dict_csv["App_Status"].append(Status["App_Status"])
	dict_csv["Timestamp"].append(Status["Time"])
	dict_csv["count"].append(count)
	return dict_csv    
			
def create_application_id(ip_port_app):
	application = {}
	for tuple in ip_port_app:
		application[tuple[2]] = tuple[2].upper().replace(" ", "_") 
	return application
			
def get_status(csv_exist, csv_file, ip_port_app, SOCK):
	""" Returns the dictionary having the information of application status """
	app_id_dict = create_application_id(ip_port_app)
	process_Id = {"Application_Down": "PID009"}
	dictionary_info = {"Application_ID": [],
					   "Application_name": [],
					   "Process_ID": [],
					   "IP": [],
					   "Port": [],
					   "App_Status": [],
					   "Timestamp": [],
					   "count": []}

	# If the ip_port_app csv isn't available create initially.
	if csv_exist is False:
		for ind, app in enumerate(ip_port_app):
			Status = SOCK.get_response(app[0], app[1], app[2])
			if(Status["App_Status"] == "DOWN"):
				csv_records = create_dict(dictionary_info, Status,
										  app_id_dict, process_Id,
										  True, 1)
			else:
				csv_records = create_dict(dictionary_info,Status,
											  app_id_dict, process_Id,
											  True, 0)
		try:
			csv_df = pd.DataFrame(csv_records)
			csv_df.to_csv(csv_file, index=False)
			logging.debug("{} is created Initially.\n".format(csv_file))
			return csv_df, csv_records
		except Exception as csverr:
			logging.error("Error while creating the csv initially: {}".format(csverr))
			sys.exit(2)
	
	# If the ip_port_app csv is existing already.
	else:
		try:
			csv_df = pd.read_csv(csv_file)
		except Exception as csverr2:
			logging.error("Unable to read csv: {}".format(csverr2))
		for ind, Apptup in enumerate(ip_port_app):
			Status =  SOCK.get_response(Apptup[0], Apptup[1], Apptup[2])
			_app = Status["Application"]
			status = Status["App_Status"]
			appli_row = csv_df.loc[csv_df['Application_name'] == _app]
			ser = appli_row["count"]
			# Application is UP
			if(status =="UP"):
				csv_records = create_dict(dictionary_info, Status,
											  app_id_dict, process_Id,
											  True, 0)

			# Application is down then increase count
			elif(status =="DOWN" and ser[ind] < 3):
				count = ser[ind] + 1
				csv_records = create_dict(dictionary_info, Status,
										  app_id_dict, process_Id,
										  False, count)

				# Raise Exception
				if(count >= 3):
					logging.warning("Application Status Down count is occured Thrice, Raising Exception")
					if csv_records["Application_name"][ind] == _app:
						logging.debug({"Application_name": dictionary_info["Application_name"][ind],
									   "Application_ID": dictionary_info["Application_ID"][ind],
									   "IP": dictionary_info["IP"][ind],
									   "Process_ID": dictionary_info["Process_ID"][ind],
									   "Port": dictionary_info["Port"][ind],
									   "Status": dictionary_info["App_Status"][ind],
									   "Time": dictionary_info["Timestamp"][ind]})
			
		dataframe = pd.DataFrame(csv_records)
		return dataframe, csv_records
			
def check_for_status(confile, csv_file):
	""" for once ip,port,appname touple list, check the response status """
	csv_exist = os.path.isfile(csv_file)
	C = Configuration_file(confile)
	try:
		SOCK = Mysocket()
		ip_port_app = C.read_config()
		logging.debug("Data extracted from {}".format(confile))
		return get_status(csv_exist, csv_file, ip_port_app, SOCK)
	except FileNotFoundError as FNF:
		logging.error("{0} File not Found. Error: {1}".format(confile, FNF))
	
if __name__=="__main__":
	print("{} has no main function to execute..".format(__file__))
