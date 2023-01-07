from prefect.tasks.notifications import EmailTask

prefect_email_notification = EmailTask(
    email_to="DataPlatform@accruent.com",
    email_from="notifications@prefect.io",
    smtp_server="10.50.4.31",
    smtp_port=25,
    smtp_type="INSECURE",
)
