import datetime


def get_job_duration(job):
    job_duration = datetime.datetime.utcnow() - job.created_at
    return job_duration.total_seconds()
