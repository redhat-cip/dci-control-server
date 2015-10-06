# Simple scheduler

We need to have priorities on the products that we tests.

The idea is to have the ability to put a priority on a product
so that it will be tested before another ones.

## Database schema impact

The table 'jobdefinition' gather a list of components and the tests
to run on it. So it's the best place to put the priority.

This feature implies to put a column 'priority' on the table
jobdefinition.

## Re-prioritize the jobs

We can re-prioritize the jobs by modifying the priority of the jobdefinitions.

## Recheck on a given remoteci

To make a recheck on a given remoteci we can put a flag 'recheck' on the jobs
table. If it's set to True, when the remote ci will request a job then
the server will first check if there is a job assigned to that remote ci and
the flag set. In that case, the server will create a new job with the same
data and set the 'recheck' to False.

## Request for a job

First the server check if their is a job to recheck, if yes it send it.

Otherwise for creating a job, we simply need to sort the table
jobdefinition by priority and use the jobdefinition with the highest
priority.

    SELECT
        jobdefinitions.id
    FROM
        jobdefinitions, remotecis
    WHERE jobdefinitions.id NOT IN (
        SELECT
            jobs.jobdefinition_id
        FROM jobs
        WHERE jobs.remoteci_id=:remoteci_id
    ) AND jobdefinitions.test_id=remotecis.test_id AND
    remotecis.id=:remoteci_id
    ORDER BY
        priority ASC
    LIMIT 1
