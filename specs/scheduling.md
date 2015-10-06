# Simple scheduler

We need to have priorities on the products that we tests.

The idea is to have the ability to put a priority on a product
so that it will be tested before another ones.

## Database schema impact

The table 'jobdefinition' gather a list of components and the tests
to run on it. So it's the best place to put the priority.

This feature implies to put a column 'priority' on the table
jobdefinition.

## Request for a job

When a remote ci ask for a job to run, we simply need to sort the table
jobdefinition by priority and return the jobdefinition with the highest
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
