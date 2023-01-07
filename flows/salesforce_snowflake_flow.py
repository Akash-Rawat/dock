from prefect import Flow
from prefect.triggers import all_successful, any_failed

from tasks.sourcesalesforcetargetsnowflaketasks import AzureAKSJobStart, AzureAKSJobStatusCheck, \
    SalesforceStateFileUploadToAzure, SalesforceLogFileWithTimestampUploadToAzure, SalesforceLogFileCheckForErrorsToSendNotification, \
    SalesforceAllTasksSuccess, SalesforceAnyoneTaskFailed, AzureAKSJobAndPodDeletion

from utils.config import docker_run, azure_store
from utils.schedule_config import prefect_schedule

flow_name = "salesforce_snowflake_flow"
azure_aks_job_start = AzureAKSJobStart()
azure_aks_job_status_check = AzureAKSJobStatusCheck()
salesforce_log_file_upload_to_azure = SalesforceLogFileWithTimestampUploadToAzure()
salesforce_log_file_check_for_errors_to_send_notification = SalesforceLogFileCheckForErrorsToSendNotification()
salesforce_state_file_upload_to_azure = SalesforceStateFileUploadToAzure()
azure_aks_job_and_pod_deletion = AzureAKSJobAndPodDeletion()
salesforce_all_tasks_success = SalesforceAllTasksSuccess(trigger=all_successful)
salesforce_anyone_task_failed = SalesforceAnyoneTaskFailed(trigger=any_failed)

with Flow(name=flow_name, schedule=prefect_schedule, run_config=docker_run, storage=azure_store) as flow:
    azure_aks_job_start = azure_aks_job_start(flow_name)
    azure_aks_job_status_check = azure_aks_job_status_check(flow_name)
    salesforce_log_file_upload_to_azure = salesforce_log_file_upload_to_azure(flow_name)
    salesforce_log_file_check_for_errors_to_send_notification = \
        salesforce_log_file_check_for_errors_to_send_notification(flow_name)
    salesforce_state_file_upload_to_azure = salesforce_state_file_upload_to_azure(flow_name)
    azure_aks_job_and_pod_deletion = azure_aks_job_and_pod_deletion(flow_name)

    azure_aks_job_status_check.set_upstream(azure_aks_job_start)
    salesforce_log_file_upload_to_azure.set_upstream(azure_aks_job_status_check)
    salesforce_log_file_check_for_errors_to_send_notification.set_upstream(salesforce_log_file_upload_to_azure)
    salesforce_state_file_upload_to_azure.set_upstream(salesforce_log_file_check_for_errors_to_send_notification)
    azure_aks_job_and_pod_deletion.set_upstream(salesforce_state_file_upload_to_azure)

    success_email_task = salesforce_all_tasks_success(upstream_tasks=[azure_aks_job_start,
                                                                 azure_aks_job_status_check,
                                                                 salesforce_log_file_upload_to_azure,
                                                                 salesforce_log_file_check_for_errors_to_send_notification,
                                                                 salesforce_state_file_upload_to_azure,
                                                                 azure_aks_job_and_pod_deletion])

    failure_email_task = salesforce_anyone_task_failed(upstream_tasks=[azure_aks_job_start,
                                                                  azure_aks_job_status_check,
                                                                  salesforce_log_file_upload_to_azure,
                                                                  salesforce_log_file_check_for_errors_to_send_notification,
                                                                  salesforce_state_file_upload_to_azure,
                                                                  azure_aks_job_and_pod_deletion])
    flow.set_reference_tasks([success_email_task])
