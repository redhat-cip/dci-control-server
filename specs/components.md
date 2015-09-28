# from product to component

## Adjust the DB schema

Add the componenttypes tables:

    CREATE TABLE componenttypes (
        id uuid DEFAULT gen_uuid() NOT NULL,
        created_at timestamp with time zone DEFAULT now() NOT NULL,
        updated_at timestamp with time zone DEFAULT now() NOT NULL,
        name character varying(255) NOT NULL,
        etag character varying(40) DEFAULT gen_etag() NOT NULL
    );
    COMMENT ON TABLE componenttypes IS 'The different type of components.';

This is an of componet types:

- git commit
- a gerrit review
- yum repository snapshot
- disk image

Add the components table:

    CREATE TABLE components (
        id uuid DEFAULT gen_uuid() NOT NULL,
        created_at timestamp with time zone DEFAULT now() NOT NULL,
        updated_at timestamp with time zone DEFAULT now() NOT NULL,
        componenttype_id uuid NOT NULL,
        version_id uuid,
        name character varying(255) NOT NULL,
        etag character varying(40) DEFAULT gen_etag() NOT NULL,
        data json,
        sha text,
        title text,
        message text,
        url text,
        ref text
    );
    COMMENT ON TABLE components IS 'The components, like a git commit, a Yum repository or a disk image URL.';

Add a jobdefinitions table. The anchor for the different components.

    CREATE TABLE jobdefinitions (
        id uuid DEFAULT gen_uuid() NOT NULL,
        created_at timestamp with time zone DEFAULT now() NOT NULL,
        updated_at timestamp with time zone DEFAULT now() NOT NULL,
        etag character varying(40) DEFAULT gen_etag() NOT NULL,
        name character varying(100),
        test_id uuid NOT NULL
    );

Finally a jobdefinition_components table (1 to n). This table replace
the former `testversions` table:

    CREATE TABLE jobdefinition_components (
        id uuid DEFAULT gen_uuid() NOT NULL,
        created_at timestamp with time zone DEFAULT now() NOT NULL,
        updated_at timestamp with time zone DEFAULT now() NOT NULL,
        etag character varying(40) DEFAULT gen_etag() NOT NULL,
        jobdefinition_id uuid NOT NULL,
        component_id uuid NOT NULL,
        test_id uuid NOT NULL,
        name character varying(100)
    );


We just now have to add a jobdefinition_id to the jobs table.


## Patch the code of app.py

1. Adjust `aggregate_job_date` so it also include component.
2. Adjust the `tox_agent` first.
3. Adjust the `khaleesi_agent`.
4. Drop the `products`, `productversions`, `testversions` and `versions`  tables.
