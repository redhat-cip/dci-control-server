import datetime


def get_utc_now():
    return datetime.datetime.utcnow()


def get_job_duration(job):
    job_duration = get_utc_now() - job.created_at
    return job_duration.total_seconds()
