import copy
import subprocess
import datetime
import prefect
from prefect import Task
from time import sleep
from prefect.engine.signals import LOOP
import json
from azure.storage.fileshare import ShareFileClient
import os
import re

from utils.email_notification import prefect_email_notification

azure_client_id = os.environ.get("AZURE_CLIENT_ID")
azure_client_secret = os.environ.get("AZURE_CLIENT_SECRET")
azure_tenant_id = os.environ.get("AZURE_TENANT_ID")
azure_connection_string = os.environ.get("AZURE_STORAGE_CONNECTION_STRING")
azure_container_name = os.environ.get("AZURE_CONTAINER_NAME")
azure_share_name = os.environ.get("AZURE_SHARE_NAME")
run_environment = os.environ.get("RUN_ENVIRONMENT")
docker_image_name = os.environ.get("DOCKER_IMAGE_NAME")
docker_secret_name = os.environ.get("DOCKER_SECRET_NAME")
aks_cluster_name = os.environ.get("AKS_CLUSTER_NAME")
aks_cluster_resource_group_name = os.environ.get("AKS_CLUSTER_RESOURCE_GROUP_NAME")
azure_salesforce_share_name_sub_path = os.environ.get("AZURE_SALESFORCE_SHARE_NAME_SUB_PATH")

logger = prefect.context.get("logger")

current_timestamp = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")

log_file_name = "/prefect/logs/ingest_salesforce_snowflake" + current_timestamp + ".log"

start_time = datetime.datetime.now()

current_date_job = datetime.datetime.now().strftime('%y%m%d')
current_time_job = datetime.datetime.now().strftime('%H%M%S')

if azure_container_name is None:
    job_name = "dp-ingest-salesforce-snowflake-" + current_date_job + "-" + current_time_job
else:
    job_name = azure_container_name + "-" + current_date_job + "-" + current_time_job

job_creation_yaml_path = "/prefect/aks/jobyaml/aks-salesforce-snowflake-job.yaml"

email_subject = "Source Salesforce and Target Snowflake Flow Notification - Environment: " + str(run_environment) \
                            + " - Prefect Flow Name: salesforce_snowflake_flow"
email_message = "Source salesforce and target snowflake tasks are failed because of errors in " + str(run_environment) \
                + " environment. Due to this task failure flow salesforce_snowflake_flow is failed. " \
                  "Please check the prefect logs for more information. "

azure_salesforce_log_file_path = str(azure_salesforce_share_name_sub_path) + "/ingest_salesforce_snowflake.log"
file_name1 = str(azure_salesforce_share_name_sub_path) + "/logs/ingest_salesforce_snowflake_" + current_timestamp + \
             ".log"
azure_salesforce_state_file_path = str(azure_salesforce_share_name_sub_path) + "/source_salesforce_state.json"


class AzureContainerGroupLogin:
    def __init__(self):
        pass

    @staticmethod
    def azure_login(login_type):

        azure_aci_login_cmd = ['az', 'login', '--service-principal',
                               '--username', azure_client_id,
                               '--password', azure_client_secret,
                               '--tenant', azure_tenant_id]

        azure_aci_login_cmd_str = copy.copy(azure_aci_login_cmd)

        azure_aci_login_cmd_str[4] = 'xxxxxxxxx'
        azure_aci_login_cmd_str[6] = 'xxxxxxxxx'
        azure_aci_login_cmd_str[8] = 'xxxxxxxxx'

        logger.info(
            'Running azure container ' + login_type + ' login command:{0}'.format(
                ' '.join(azure_aci_login_cmd_str)))

        azure_aci_login_proc = subprocess.Popen(azure_aci_login_cmd, stdout=subprocess.PIPE,
                                                stderr=subprocess.PIPE,
                                                universal_newlines=True)
        azure_aci_start_output, azure_aci_login_error = azure_aci_login_proc.communicate()

        azure_aci_login_return_code = azure_aci_login_proc.returncode

        if azure_aci_login_return_code == 0:
            logger.info("Azure container " + login_type + " login command success!")
        else:
            logger.info("Error in azure container " + login_type + " login : " + azure_aci_login_error)


class AzureAKSGetCredentials:
    def __init__(self):
        pass

    @staticmethod
    def azure_aks_get_credentials(get_type):

        azure_aks_get_credentials_cmd = ['az', 'aks', 'get-credentials', '--name', aks_cluster_name,
                                         '--resource-group', aks_cluster_resource_group_name, '--admin']

        azure_aks_get_credentials_cmd_str = copy.copy(azure_aks_get_credentials_cmd)

        azure_aks_get_credentials_cmd_str[4] = 'xxxxxxxxx'
        azure_aks_get_credentials_cmd_str[6] = 'xxxxxxxxx'

        logger.info('Running azure aks get credentials command for ' + get_type + ' :{0}'.format(
            ' '.join(azure_aks_get_credentials_cmd_str)))

        azure_aks_get_credentials_proc = subprocess.Popen(azure_aks_get_credentials_cmd,
                                                          stdout=subprocess.PIPE,
                                                          stderr=subprocess.PIPE,
                                                          universal_newlines=True)

        azure_aks_get_credentials_output, azure_aks_get_credentials_error = azure_aks_get_credentials_proc.communicate()

        azure_aks_get_credentials_return_code = azure_aks_get_credentials_proc.returncode

        if azure_aks_get_credentials_return_code == 0:
            logger.info("Azure aks get credentials command for " + get_type + " success!")
        else:
            logger.info("Error in azure aks get credentials command for " + get_type + " : " +
                        azure_aks_get_credentials_error)


class AzureContainerGroupLogout:
    def __init__(self):
        pass

    @staticmethod
    def azure_logout(logout_type):

        azure_aci_logout_cmd = ['az', 'logout', '--username', azure_client_id]

        azure_aci_logout_cmd_str = copy.copy(azure_aci_logout_cmd)

        azure_aci_logout_cmd_str[3] = 'xxxxxxxxx'

        logger.info('Running azure container ' + logout_type + ' logout command:{0}'.format(
            ' '.join(azure_aci_logout_cmd_str)))

        azure_aci_logout_proc = subprocess.Popen(azure_aci_logout_cmd, stdout=subprocess.PIPE,
                                                 stderr=subprocess.PIPE,
                                                 universal_newlines=True)

        azure_aci_logout_output, azure_aci_logout_error = azure_aci_logout_proc.communicate()

        azure_aci_logout_return_code = azure_aci_logout_proc.returncode

        if azure_aci_logout_return_code == 0:
            logger.info("Azure container " + logout_type + " logout command success!")
        else:
            logger.info("Error in azure container " + logout_type + " logout command run : " +
                        azure_aci_logout_error)


class AzureAKSGetPodName:

    def __init__(self):
        pass

    @staticmethod
    def aks_get_pod_name():

        select_job = "job-name=" + job_name

        azure_aks_pod_get_cmd = ['kubectl', 'get', 'pods', '-l', select_job,
                                 '-n', azure_container_name, '-o', 'json']

        azure_aks_pod_get_cmd_str = copy.copy(azure_aks_pod_get_cmd)

        azure_aks_pod_get_cmd_str[4] = 'xxxxxxxxx'
        azure_aks_pod_get_cmd_str[6] = 'xxxxxxxxx'

        logger.info('Running azure aks pod get command:{0}'.format(' '.join(azure_aks_pod_get_cmd_str)))

        azure_aks_pod_get_proc = subprocess.Popen(azure_aks_pod_get_cmd, stdout=subprocess.PIPE,
                                                  stderr=subprocess.PIPE,
                                                  universal_newlines=True)

        azure_aks_pod_get_output, azure_aks_pod_get_error = azure_aks_pod_get_proc.communicate()

        azure_aks_pod_get_return_code = azure_aks_pod_get_proc.returncode

        if azure_aks_pod_get_return_code == 0:
            logger.info("Azure aks pod get command success!")
        else:
            logger.info("Error in azure aks pod get command run : " + azure_aks_pod_get_error)

        pod_get_name_output = json.loads(azure_aks_pod_get_output)

        if "metadata" in pod_get_name_output['items'][0]:
            logger.info("Pod get name response has required key")
            pod_name = pod_get_name_output['items'][0]['metadata']['name']
        else:
            logger.info("Pod get name response data has no required key")
            pod_name = job_name

        logger.info("Pod Name is: " + pod_name)

        return pod_name


class AzureAKSJobDelete:

    def __init__(self):
        pass

    @staticmethod
    def aks_job_delete():

        azure_aks_job_delete_cmd = ['kubectl', 'delete', 'jobs', job_name,
                                    '-n', azure_container_name, '--cascade=orphan']

        azure_aks_job_delete_cmd_str = copy.copy(azure_aks_job_delete_cmd)

        azure_aks_job_delete_cmd_str[3] = 'xxxxxxxxx'
        azure_aks_job_delete_cmd_str[5] = 'xxxxxxxxx'

        logger.info('Running azure aks job delete command:{0}'.format(' '.join(azure_aks_job_delete_cmd_str)))

        azure_aks_job_delete_proc = subprocess.Popen(azure_aks_job_delete_cmd, stdout=subprocess.PIPE,
                                                     stderr=subprocess.PIPE,
                                                     universal_newlines=True)

        azure_aks_job_delete_output, azure_aks_job_delete_error = azure_aks_job_delete_proc.communicate()

        azure_aks_job_delete_return_code = azure_aks_job_delete_proc.returncode

        if azure_aks_job_delete_return_code == 0:
            logger.info("Azure aks job delete command success!")
        else:
            logger.info("Error in azure aks job delete command run : " + azure_aks_job_delete_error)


class AzureAKSPodDelete:

    def __init__(self):
        pass

    @staticmethod
    def aks_pod_delete():

        pod_name = azure_aks_pod_get.aks_get_pod_name()

        azure_aks_pod_delete_cmd = ['kubectl', 'delete', 'pods', pod_name,
                                    '-n', azure_container_name, '--grace-period=0', '--force']

        azure_aks_pod_delete_cmd_str = copy.copy(azure_aks_pod_delete_cmd)

        azure_aks_pod_delete_cmd_str[3] = 'xxxxxxxxx'
        azure_aks_pod_delete_cmd_str[5] = 'xxxxxxxxx'

        logger.info('Running azure aks pod delete command:{0}'.format(' '.join(azure_aks_pod_delete_cmd_str)))

        azure_aks_pod_delete_proc = subprocess.Popen(azure_aks_pod_delete_cmd, stdout=subprocess.PIPE,
                                                     stderr=subprocess.PIPE,
                                                     universal_newlines=True)

        azure_aks_pod_delete_output, azure_aks_pod_delete_error = azure_aks_pod_delete_proc.communicate()

        azure_aks_pod_delete_return_code = azure_aks_pod_delete_proc.returncode

        if azure_aks_pod_delete_return_code == 0:
            logger.info("Azure aks pod delete command success!")
        else:
            logger.info("Error in azure aks pod delete command run : " + azure_aks_pod_delete_error)


class AzureAKSJobCreationYamlUpdate:

    def __init__(self):
        pass

    @staticmethod
    def aks_job_yaml_update():

        with open("/prefect/aks/aks-salesforce-snowflake-job.txt", "r") as aks_job_create_file:
            newlines = []
            for line in aks_job_create_file.readlines():
                if "JOB_NAME" in line:
                    pos = line.index(': ')
                    newlines.append(line[:pos + 2] + job_name + '\n')
                elif "NAMESPACE_NAME" in line or "AKS_NAME" in line:
                    pos = line.index(': ')
                    newlines.append(line[:pos + 2] + azure_container_name + '\n')
                elif "DOCKER_IMAGE_NAME" in line:
                    pos = line.index(': ')
                    newlines.append(line[:pos + 2] + docker_image_name + '\n')
                elif "DOCKER_SECRET" in line:
                    pos = line.index(': ')
                    newlines.append(line[:pos + 2] + docker_secret_name + '\n')
                elif "AZ_SHARE_NAME" in line:
                    pos = line.index(': ')
                    newlines.append(line[:pos + 2] + azure_share_name + '\n')
                elif "AZURE_SALESFORCE_SHARE_NAME_SUB_PATH" in line:
                    pos = line.index(': ')
                    newlines.append(line[:pos + 2] + azure_salesforce_share_name_sub_path + '\n')
                else:
                    newlines.append(line)

        with open(job_creation_yaml_path, 'w') as azure_job_create_yaml_file:
            for line in newlines:
                azure_job_create_yaml_file.write(line)

        logger.info("Azure AKS Job Yaml Update Successful!")


class SalesforceSnowflakeEmailNotificationSubjectMessage:

    def __init__(self):
        pass

    @staticmethod
    def email_notification_subject_message(task_name, flow_name):

        global email_subject
        global email_message

        if task_name == "AzureAKSJobStart":
            email_subject = "Source Salesforce and Target Snowflake Flow Notification - Environment: " + run_environment \
                            + " - Prefect Flow Name: " + flow_name
            email_message = "Source salesforce and target snowflake task AzureAKSJobStart is " \
                            "failed because of errors in " + \
                            run_environment + " environment. Due to this task failure flow " + flow_name + \
                            " is failed. Please check the prefect logs for more information. "
        elif task_name == "AzureAKSJobStatusCheck":
            email_subject = "Source Salesforce and Target Snowflake Flow Notification - Environment: " + run_environment \
                            + " - Prefect Flow Name: " + flow_name
            email_message = "Source salesforce and target snowflake tasks are failed because prefect flow is running " \
                            "more than or equal to 23 hours in " + run_environment + \
                            " environment. Long running prefect flow name is " \
                            + flow_name + ". Please check the prefect logs for more information."
        elif task_name == "AzureAKSJobFailureCheck":
            email_subject = "Source Salesforce and Target Snowflake Flow Notification - Environment: " + run_environment \
                            + " - Prefect Flow Name: " + flow_name
            email_message = "Source salesforce and target snowflake tasks are failed because the associated " \
                            "AKS job has failed in " + run_environment + \
                            " environment. The failed prefect flow name is " \
                            + flow_name + ". Please check the prefect logs for more information."
        elif task_name == "SalesforceLogFileWithTimestampUploadToAzure":
            email_subject = "Source Salesforce and Target Snowflake Flow Notification - Environment: " + run_environment \
                            + " - Prefect Flow Name: " + flow_name
            email_message = "Source salesforce and target snowflake task SalesforceLogFileWithTimestampUploadToAzure is failed " \
                            "because of errors in " + run_environment + \
                            " environment. Due to this task failure flow " + \
                            flow_name + " is failed. Please check the prefect logs for more information. "
        elif task_name == "SalesforceLogFileCheckForErrorsToSendNotification":
            email_subject = "Source Salesforce and Target Snowflake Flow Notification - Environment: " + run_environment \
                            + " - Prefect Flow Name: " + flow_name
            email_message = "Source salesforce and target snowflake tasks are failed because errors are detected in " \
                            "ingest_salesforce_snowflake.log file in " + run_environment + " environment. Errors detected " \
                                                                                      "flow name is " + flow_name + \
                            ". Please check the prefect logs for more information. "
        elif task_name == "SalesforceStateFileUploadToAzure":
            email_subject = "Source Salesforce and Target Snowflake Flow Notification - Environment: " + run_environment \
                            + " - Prefect Flow Name: " + flow_name
            email_message = "Source salesforce and target snowflake task SalesforceStateFileUploadToAzure is failed " \
                            "because of errors in " + run_environment + " environment. " \
                                                                        "Due to this task failure flow " + \
                            flow_name + " is failed. Please check the prefect logs for more information. "
        elif task_name == "AzureAKSJobAndPodDeletion":
            email_subject = "Source Salesforce and Target Snowflake Flow Notification - Environment: " + run_environment \
                            + " - Prefect Flow Name: " + flow_name
            email_message = "Source salesforce and target snowflake task AzureAKSJobAndPodDeletion is failed " \
                            "because of errors in " + run_environment + " environment. " \
                                                                        "Due to this task failure flow " + \
                            flow_name + " is failed. Please check the prefect logs for more information. "
        else:
            email_subject = "Source Salesforce and Target Snowflake Flow Notification - Environment: " + run_environment \
                            + " - Prefect Flow Name: " + flow_name
            email_message = "Source salesforce and target snowflake unknown task is failed because of errors in " \
                            + run_environment + " environment. Due to this task failure flow " + \
                            flow_name + " is failed. Please check the prefect logs for more information. "


azure_login = AzureContainerGroupLogin()
azure_aks_get_credentials = AzureAKSGetCredentials()
azure_logout = AzureContainerGroupLogout()
azure_aks_pod_get = AzureAKSGetPodName()
azure_aks_job_delete = AzureAKSJobDelete()
azure_aks_pod_delete = AzureAKSPodDelete()
azure_aks_job_yaml_creation = AzureAKSJobCreationYamlUpdate()
salesforce_snowflake_email_notification_subject_message = SalesforceSnowflakeEmailNotificationSubjectMessage()


class AzureAKSJobStart(Task):

    def run(self, flow_name):

        salesforce_snowflake_email_notification_subject_message.\
            email_notification_subject_message("AzureAKSJobStart", flow_name)

        azure_login.azure_login("start")

        azure_aks_get_credentials.azure_aks_get_credentials("start")

        azure_aks_job_yaml_creation.aks_job_yaml_update()

        azure_aks_job_start_cmd = ['kubectl', 'apply', '-f', job_creation_yaml_path]

        logger.info('Running azure kubectl apply job command:{0}'.format(' '.join(azure_aks_job_start_cmd)))

        azure_aks_job_start_proc = subprocess.Popen(azure_aks_job_start_cmd, stdout=subprocess.PIPE,
                                                    stderr=subprocess.PIPE,
                                                    universal_newlines=True)

        azure_aks_job_start_output, azure_aks_job_start_error = azure_aks_job_start_proc.communicate()

        azure_aks_job_start_return_code = azure_aks_job_start_proc.returncode

        if azure_aks_job_start_return_code == 0:
            logger.info("Azure aks job start command success!")
        else:
            logger.info("Error in azure aks job start command run : " + azure_aks_job_start_error)

        azure_logout.azure_logout("start")


class AzureAKSJobStatusCheck(Task):

    def run(self, flow_name):

        sleep(300)

        azure_login.azure_login("status check")

        azure_aks_get_credentials.azure_aks_get_credentials("status check")

        azure_aks_job_status_check_cmd = ['kubectl', 'get', 'jobs', job_name, '--namespace', azure_container_name,
                                          '-o', 'json']

        azure_aks_job_status_check_cmd_str = copy.copy(azure_aks_job_status_check_cmd)

        azure_aks_job_status_check_cmd_str[3] = 'xxxxxxxxx'
        azure_aks_job_status_check_cmd_str[5] = 'xxxxxxxxx'

        logger.info('Running azure aks job status check command:{0}'.format(
            ' '.join(azure_aks_job_status_check_cmd_str)))

        azure_aks_job_status_check_proc = subprocess.Popen(azure_aks_job_status_check_cmd, stdout=subprocess.PIPE,
                                                           stderr=subprocess.PIPE,
                                                           universal_newlines=True)

        azure_aks_job_status_check_output, azure_aks_job_status_check_error = \
            azure_aks_job_status_check_proc.communicate()

        azure_aks_job_status_check_return_code = azure_aks_job_status_check_proc.returncode

        if azure_aks_job_status_check_return_code == 0:
            logger.info("Azure aks job status check command success!")
        else:
            logger.info("Error in azure aks job status check command run : " + azure_aks_job_status_check_error)

        azure_logout.azure_logout("status check")

        current_time = datetime.datetime.now()
        time_diff = current_time - start_time

        if time_diff >= datetime.timedelta(hours=23):
            logger.info("Job start time and current time difference is greater than or equal 23 hours")
            salesforce_snowflake_email_notification_subject_message.\
                email_notification_subject_message("AzureAKSJobStatusCheck", flow_name)
            raise ValueError("Prefect salesforce snowflake flow is running more than or equal to 23 hours")
        else:
            logger.info("Job start time and current time difference is less than 23 hours")

        status_output = json.loads(azure_aks_job_status_check_output)

        if "conditions" in status_output['status']:
            if "failed" in status_output['status']:
                logger.info("AKS job has failed.")
                logger.info("Status output: " + json.dumps(status_output))
                salesforce_snowflake_email_notification_subject_message.\
                    email_notification_subject_message("AzureAKSJobFailureCheck", flow_name)
                raise ValueError("AKS job has failed.")
            else:
                logger.info("Job status check key exist in aks job status response data and job completed")
                state = status_output['status']['conditions'][0]['status']
        else:
            logger.info("Job status check key doesn't exist in aks job status response data and job is still running")
            state = "False"

        logger.info("State: " + state)

        if state not in ['True']:
            raise LOOP(result=state)

        return state


class SalesforceLogFileWithTimestampUploadToAzure(Task):

    def run(self, flow_name):

        salesforce_snowflake_email_notification_subject_message.\
            email_notification_subject_message("SalesforceLogFileWithTimestampUploadToAzure", flow_name)

        file_share_download_client = ShareFileClient.from_connection_string(
            conn_str=azure_connection_string,
            share_name=azure_share_name,
            file_path=azure_salesforce_log_file_path)

        with open(log_file_name, "wb") as file1:
            stream = file_share_download_client.download_file()
            file1.write(stream.readall())

        file_share_upload_client = ShareFileClient.from_connection_string(
            conn_str=azure_connection_string,
            share_name=azure_share_name,
            file_path=file_name1)

        with open(log_file_name, "rb") as file2:
            file_share_upload_client.upload_file(file2)

        logger.info("Salesforce Log File with Timestamp Upload Successful!")


class SalesforceLogFileCheckForErrorsToSendNotification(Task):

    def run(self, flow_name):

        list1 = []
        last_line = ""
        with open(log_file_name, "r") as logfile:
            for num, line in enumerate(logfile):
                if re.findall('(error|errors|Error|ERROR|FATAL|CRITICAL)', line):
                    list1.append(num + 1)
                last_line = line

        if len(list1) != 0:
            logger.info("Errors found in salesforce snowflake data ingestion log file ")
            salesforce_snowflake_email_notification_subject_message.\
                email_notification_subject_message("SalesforceLogFileCheckForErrorsToSendNotification", flow_name)
            os.remove(log_file_name)
            raise ValueError("Errors found in salesforce snowflake ingestion log file")
        elif not last_line.startswith('{"bookmarks":'):
            logger.info("The salesforce snowflake data ingestion log file did not end with the bookmarks ")
            salesforce_snowflake_email_notification_subject_message.\
                email_notification_subject_message("SalesforceLogFileCheckForErrorsToSendNotification", flow_name)
            os.remove(log_file_name)
            raise ValueError("The salesforce snowflake data ingestion log file did not end with the bookmarks ")
        else:
            logger.info("No errors found in salesforce snowflake data ingestion log file ")

        logger.info("Salesforce Log File Check for Errors to send notification Successful!")


class SalesforceStateFileUploadToAzure(Task):

    def run(self, flow_name):

        salesforce_snowflake_email_notification_subject_message.\
            email_notification_subject_message("SalesforceStateFileUploadToAzure", flow_name)

        last_state_line = ""

        with open(log_file_name, 'r') as logfile:
            for num, line in enumerate(logfile):
                last_state_line = line

        if last_state_line.startswith('{"bookmarks":') or last_state_line.startswith('{"current_stream":'):
            final_state_json = json.loads(last_state_line)
            with open("/prefect/state/source_salesforce_state.json", 'w', encoding='utf-8') as logfile1:
                json.dump(final_state_json, logfile1, ensure_ascii=False, sort_keys=True, indent=4)

            file_share_client = ShareFileClient.from_connection_string(
                conn_str=azure_connection_string,
                share_name=azure_share_name,
                file_path=azure_salesforce_state_file_path)

            with open("/prefect/state/source_salesforce_state.json", "rb") as file3:
                file_share_client.upload_file(file3)
        else:
            print("No last state details found in ingestion log file")

        os.remove(log_file_name)

        logger.info("Salesforce State File Upload Successful!")


class AzureAKSJobAndPodDeletion(Task):

    def run(self, flow_name):

        salesforce_snowflake_email_notification_subject_message.\
            email_notification_subject_message("AzureAKSJobAndPodDeletion", flow_name)

        azure_login.azure_login("job pod delete")

        azure_aks_get_credentials.azure_aks_get_credentials("job pod delete")

        azure_aks_job_delete.aks_job_delete()
        azure_aks_pod_delete.aks_pod_delete()

        azure_logout.azure_logout("job pod delete")

        logger.info("Azure AKS Job and Pod Deletion Step Completed Successful!")


class SalesforceAllTasksSuccess(Task):

    def run(self, **kwargs):
        logger.info("Source Salesforce and Target Snowflake Flow completed without any issues")
        logger.info("SalesforceAllTasksSuccess task triggered and completed Successfully!")


class SalesforceAnyoneTaskFailed(Task):

    def run(self, **kwargs):
        try:
            azure_aks_job_delete.aks_job_delete()
            azure_aks_pod_delete.aks_pod_delete()
            logger.info("Some of the reference tasks failed in Source Salesforce and Target Snowflake. ")
            prefect_email_notification.run(subject=email_subject,
                                           msg=email_message, )
        except Exception as e:
            email_subject_except = "Source Salesforce and Target Snowflake Flow Notification - Environment: " + \
                                   str(run_environment) + " - Prefect Flow Name: salesforce_snowflake_flow"
            email_message_except = "Source salesforce and target snowflake tasks are failed while cleaning up " \
                                   "job and pod in AKS cluster in " + str(run_environment) + \
                                   " environment. Due to this failure flow salesforce_snowflake_flow is failed. " \
                                   "Please check the prefect logs for more information. "
            prefect_email_notification.run(subject=email_subject_except,
                                           msg=email_message_except, )
            logger.info(e)

            raise RuntimeError("Something Bad Happened") from e

        logger.info("SalesforceAnyoneTaskFailed task triggered and completed Successfully!")
