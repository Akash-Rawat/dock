import pendulum
from prefect.schedules import CronSchedule


prefect_schedule = CronSchedule(
    cron='0 4 * * *', start_date=pendulum.now("UTC")
)