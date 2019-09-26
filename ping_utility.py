# -*- coding: utf-8 -*-
'''
Script Name:	ping_Utility.py
Path:			\IPS_DecisionFabric\Exception Handling\
Description:	This script is considered as a module for the Application level Exception handling in DF framework.
Author:			Yogesh Suryawanshi
Version:		1.0
Revision History:
----------------------------------------------------------------------------------------------------------------------
S.No.			Date(MM/DD/YY)		Changed By			Change Description 	
----------------------------------------------------------------------------------------------------------------------
1.				05/16/2019			Y Suryawanshi		Initial Version (Exception Handling v1.1.1)
2.				06/21/2019			Y Suryawanshi		Fixed the bug for ISODate object
3.				23/09/2019			Y Suryawanshi		Added Process ID and Dynamic behaivior and minor enhancements.
----------------------------------------------------------------------------------------------------------------------
'''

try:
	from datetime import datetime
	from time import sleep
	import logging
	import sys, os
	import pandas as pd
	from subprocess import call
	import ping_services
	sys.path.insert(0,'/IPS_DecisionFabric/Control Framework')
	from mongo_operations import Mongo
except Exception as Error:
	print("Unable to import all modules", Error)
	
def ping_utility(time_min, config_file, csv_file):
	df, error_dict = ping_services.check_for_status(config_file, csv_file)
	df_error = df[df['count'] >= 3]
	
	PID = os.getpid()

	connection = Mongo()
	connection.Mongodb['PROCESS_MASTER'].update_one({"Application_Code": 'PING_UTILITY'},
													{"$set": {"Process_ID": str(PID)}})
	error_master = pd.DataFrame(list(connection.Mongodb['EXCEPTION_ERROR_MASTER'].find({"Error_Code": 'CONNECTION_ERROR'},
																					   {'_id': 0}).limit(1)))
	pro_master = pd.DataFrame(list(connection.Mongodb['PROCESS_MASTER'].find({"Application_Code": 'PING_UTILITY'},
																			 {'_id': 0}).limit(1)))
	application_master = pd.DataFrame(list(connection.Mongodb['APPLICATION_MASTER'].find({'Application_Code': 'PING_UTILITY'},
																						 {'_id': 0}).limit(1)))

	if (len(df_error.index) > 0):
		for ind in df_error.index:
			App_Name = df_error.loc[ind, 'Application_name']
			IP = (df_error.loc[ind, 'IP'])
			Port = (df_error.loc[ind, 'Port'])
			error_message = "{0}:{1} Application {2} is not reachable".format(IP, Port, App_Name)
			error_log = pd.DataFrame(columns=['Exception_Log_Dtm',
											  'Application_Code',
											  'Application_Name',
											  'Process_ID',
											  'Process_Name',
											  'Error_Category',
											  'Error_Code',
											  'Error_Desc',
											  'Error_Severity',
											  'Script_Name',
											  'Active_Flag',
											  'Rec_Inserted_By',
											  'Rec_Inserted_Dtm',
											  'Rec_Updated_By',
											  'Rec_Updated_Dtm']
									)
			error_log = error_log.append(pd.Series(), ignore_index=True)
			error_log[['Application_Code', 'Application_Name']] = application_master[['Application_Code', 'Application_Name']]
			error_log[['Process_ID', 'Process_Name']] = pro_master[['Process_ID', 'Process_Name']]
			error_log[['Error_Category', 'Error_Code',
					   'Error_Severity', 'Active_Flag']] = error_master[['Error_Category', 'Error_Code',
																		 'Error_Severity', 'Active_Flag']]
			error_log['Rec_Inserted_By'] = "ping_utility"
			error_log['Error_Desc'] = error_message
			error_log['Exception_Log_Dtm'] = df_error.loc[ind, 'Timestamp']
			error_log['Rec_Inserted_Dtm'] = datetime.now()
			error_log['Rec_Updated_By'] = 'ping_utility'
			error_log['Rec_Updated_Dtm'] = datetime.now()
			error_log['Script_Name'] = __file__
			connection.insert_record_in_table(error_log, 'IPS_EXCEPTION_LOG')
			df.loc[ind, 'count'] = 0
	df.to_csv(csv_file, index=False)
	logging.info("\n")
	sleep(time_min * 60)
			
def create_config(filename):
	try:
		connection = Mongo()
		App_master = pd.DataFrame(list(connection.Mongodb['APPLICATION_MASTER'].find({})))

		with open(filename, "w+") as configuration_:
			df = App_master[['Application_IP_Address', 'Application_Port_No',
							 'Application_Name']]
			df = df.dropna()
			for index, row in df.iterrows():
				data = [row.Application_IP_Address, row.Application_Port_No,
						row.Application_Name]
				sent = ("IP={0}\tport={1}\tapp={2}\n".format(data[0], int(data[1]),
															 data[2]))
				configuration_.write(sent)
		logging.debug("{} has been created".format(filename))
	except Exception as Error:
		logging.debug("Connection is not cretaed with MONGO DB while creating"
					  " configfile:", Error)


if __name__=="__main__":
	# Initiallising logging
	dtstr = datetime.now().strftime("%d%m%Y")
	log_file = "APPLICATION_STATUS_LOG_{0}.log".format(dtstr)
	FORMAT = ('%(asctime)s    %(levelname)s    \t %(message)s')
	logging.basicConfig(filename=log_file, level=logging.DEBUG, format=FORMAT)

	PID = os.getpid()
	with open("PingPID.txt", "w") as process:
		process.write(str(PID))
		process.close()

	# Check if the configuration file is existing
	config_file = "ping_config.txt"
	file_exist = os.path.isfile(config_file)
	if file_exist == False:
		logging.debug("{} not found".format(config_file))
		create_config(config_file)

	# Check if external timer is provided, default 5 minutes
	if len(sys.argv) > 1:
		times = float(sys.argv[1])
		logging.debug("Externally time is set to {0:.2f} seconds".format(times*60))
	else:
		times = 5
		logging.debug("Default timer is set to 5 min")
		
	csv_file = ('ip_port_app.csv')

	while True:
		ping_utility(times, config_file, csv_file)
