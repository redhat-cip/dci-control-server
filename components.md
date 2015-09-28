# from product to component

## Adjust the DB schema

Add the component tables:

    CREATE TABLE componenttypes (
        id uuid DEFAULT gen_uuid() NOT NULL,
        created_at timestamp with time zone DEFAULT now() NOT NULL,
        updated_at timestamp with time zone DEFAULT now() NOT NULL,
        name character varying(255) NOT NULL,
        etag character varying(40) DEFAULT gen_etag() NOT NULL
    );
    COMMENT ON TABLE componenttypes IS 'The different type of components.';

    CREATE TABLE components (
        id uuid DEFAULT gen_uuid() NOT NULL,
        created_at timestamp with time zone DEFAULT now() NOT NULL,
        updated_at timestamp with time zone DEFAULT now() NOT NULL,
        componenttype_id uuid NOT NULL,
        version_id uuid,
        name character varying(255) NOT NULL,
        etag character varying(40) DEFAULT gen_etag() NOT NULL,
        data json
    );
    COMMENT ON TABLE components IS 'The components.';

NOTE(Gonéri): Should we use a `components.version_id` key and key the
current `versions` table?

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
4. Drop the `products`, `productversions` and `testversions`  tables

