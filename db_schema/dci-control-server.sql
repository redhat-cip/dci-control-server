SET statement_timeout = 0;
SET lock_timeout = 0;
SET client_encoding = 'UTF8';
SET standard_conforming_strings = on;
SET check_function_bodies = false;
SET client_min_messages = warning;
SET default_tablespace = '';
SET default_with_oids = false;

CREATE EXTENSION IF NOT EXISTS plpgsql WITH SCHEMA pg_catalog;
COMMENT ON EXTENSION plpgsql IS 'PL/pgSQL procedural language';
CREATE EXTENSION IF NOT EXISTS pgcrypto WITH SCHEMA public;
COMMENT ON EXTENSION pgcrypto IS 'cryptographic functions';
SET search_path = public, pg_catalog;

CREATE FUNCTION gen_etag() RETURNS text
    LANGUAGE sql IMMUTABLE
    AS $$select substring(encode(md5(random()::text)::bytea, 'hex') from 0 for 37)$$;

CREATE FUNCTION gen_uuid() RETURNS uuid
    LANGUAGE sql IMMUTABLE
    AS $$SELECT uuid_in(md5(random()::text)::cstring)$$;

CREATE FUNCTION jobstate_status_in_list() RETURNS trigger
    LANGUAGE plpgsql
    AS $$
BEGIN
IF new.status IN ('new', 'ongoing', 'success', 'failure', 'killed', 'unfinished') THEN
    RETURN NEW;
ELSE
    RAISE EXCEPTION 'Bad status. valid are: new, ongoing, success, failure';
END IF;
END;
$$;

CREATE FUNCTION refresh_update_at_column() RETURNS trigger
    LANGUAGE plpgsql
    AS $$
BEGIN
IF NEW.updated_at IS NULL OR (OLD.updated_at = NEW.updated_at) THEN
    NEW.updated_at = now();
END IF;
IF NEW.etag IS NULL OR (OLD.etag = NEW.etag) THEN
    NEW.etag = md5(random()::text);
END IF;
    RETURN NEW;
END; $$;

COMMENT ON FUNCTION refresh_update_at_column() IS 'Refresh the etag and the updated_at on UPDATE.';

CREATE TABLE files (
    id uuid DEFAULT gen_uuid() NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL,
    name character varying(512) NOT NULL,
    content text NOT NULL,
    mime character varying(100) DEFAULT 'text/plain'::character varying NOT NULL,
    md5 character varying(32),
    jobstate_id uuid NOT NULL,
    etag character varying(40) DEFAULT gen_etag() NOT NULL,
    team_id uuid NOT NULL
);
COMMENT ON TABLE files IS 'The output of a command execution. The file is associated to a jobstate of a given job.';

CREATE TABLE jobs (
    id uuid DEFAULT gen_uuid() NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL,
    remoteci_id uuid NOT NULL,
    etag character varying(40) DEFAULT gen_etag() NOT NULL,
    testversion_id uuid NOT NULL,
    team_id uuid NOT NULL
);
COMMENT ON TABLE jobs IS 'An association between a testversion and a remoteci.';
COMMENT ON COLUMN jobs.testversion_id IS 'If the parameter is empty, the REST API will automatically pick an available testversions.';

CREATE TABLE jobstates (
    id uuid DEFAULT gen_uuid() NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL,
    status character varying,
    comment text,
    job_id uuid NOT NULL,
    etag character varying(40) DEFAULT gen_etag() NOT NULL,
    team_id uuid NOT NULL
);
COMMENT ON TABLE jobstates IS 'One of the status during the execution of a job. The last one is the last know status.';
COMMENT ON COLUMN jobstates.status IS 'ongoing: the job is still running, failure: the job has failed and this is the last status, success: the job has been run successfully.';

CREATE TABLE products (
    id uuid DEFAULT gen_uuid() NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL,
    name character varying(255) NOT NULL,
    etag character varying(40) DEFAULT gen_etag() NOT NULL,
    data json
);
COMMENT ON TABLE products IS 'A product';

CREATE TABLE remotecis (
    id uuid DEFAULT gen_uuid() NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL,
    name character varying(255),
    etag character varying(40) DEFAULT gen_etag() NOT NULL,
    team_id uuid NOT NULL,
    test_id uuid NOT NULL,
    data json
);
COMMENT ON TABLE remotecis IS 'The remote CI agent that process the test.';

CREATE TABLE roles (
    id uuid DEFAULT gen_uuid() NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL,
    etag character varying(40) DEFAULT gen_etag() NOT NULL,
    name character varying(100)
);
COMMENT ON TABLE roles IS 'The user roles.';

CREATE TABLE teams (
    id uuid DEFAULT gen_uuid() NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL,
    etag character varying(40) DEFAULT gen_etag() NOT NULL,
    name character varying(100)
);
COMMENT ON TABLE teams IS 'The user team. An user can only be in one team. All the resource created by an user are shared with his/her team members.';

CREATE TABLE tests (
    id uuid DEFAULT gen_uuid() NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL,
    name character varying(255) NOT NULL,
    etag character varying(40) DEFAULT gen_etag() NOT NULL,
    data json
);
COMMENT ON TABLE tests IS 'A QA test.';

CREATE TABLE testversions (
    id uuid DEFAULT gen_uuid() NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL,
    etag character varying(40) DEFAULT gen_etag() NOT NULL,
    test_id uuid NOT NULL,
    version_id uuid NOT NULL
);
COMMENT ON TABLE testversions IS 'The association between a QA test and a given product version.';

CREATE TABLE user_remotecis (
    id uuid DEFAULT gen_uuid() NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL,
    etag character varying(40) DEFAULT gen_etag() NOT NULL,
    user_id uuid NOT NULL,
    remoteci_id uuid NOT NULL
);
COMMENT ON TABLE user_remotecis IS 'experimental';

CREATE TABLE user_roles (
    id uuid DEFAULT gen_uuid() NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL,
    etag character varying(40) DEFAULT gen_etag() NOT NULL,
    user_id uuid NOT NULL,
    role_id uuid NOT NULL
);
COMMENT ON TABLE user_roles IS 'Relation table between the users and the roles.';

CREATE TABLE users (
    id uuid DEFAULT gen_uuid() NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL,
    etag character varying(40) DEFAULT gen_etag() NOT NULL,
    name character varying(100),
    password text,
    team_id uuid NOT NULL
);
COMMENT ON TABLE users IS 'The user list.';

CREATE TABLE versions (
    id uuid DEFAULT gen_uuid() NOT NULL,
    created_at timestamp with time zone NOT NULL,
    updated_at timestamp with time zone NOT NULL,
    name character varying(255) NOT NULL,
    etag character varying(40) NOT NULL,
    product_id uuid NOT NULL,
    data json,
    sha text,
    title text,
    message text,
    url text,
    ref text
);
COMMENT ON TABLE versions IS 'A given product versions. For example, a release tag or a git revision.';

ALTER TABLE ONLY files
    ADD CONSTRAINT files_pkey PRIMARY KEY (id);
ALTER TABLE ONLY jobs
    ADD CONSTRAINT jobs_pkey PRIMARY KEY (id);
ALTER TABLE ONLY versions
    ADD CONSTRAINT product_sha_unicity UNIQUE (product_id, sha);
ALTER TABLE ONLY products
    ADD CONSTRAINT product_unicity UNIQUE (name);
ALTER TABLE ONLY products
    ADD CONSTRAINT products_pkey PRIMARY KEY (id);
ALTER TABLE ONLY remotecis
    ADD CONSTRAINT remotecis_name_key UNIQUE (name);
ALTER TABLE ONLY remotecis
    ADD CONSTRAINT remotecis_pkey PRIMARY KEY (id);
ALTER TABLE ONLY roles
    ADD CONSTRAINT roles_name_key UNIQUE (name);
ALTER TABLE ONLY roles
    ADD CONSTRAINT roles_pkey PRIMARY KEY (id);
ALTER TABLE ONLY jobstates
    ADD CONSTRAINT status_pkey PRIMARY KEY (id);
ALTER TABLE ONLY teams
    ADD CONSTRAINT team_pkey PRIMARY KEY (id);
ALTER TABLE ONLY teams
    ADD CONSTRAINT teams_name_key UNIQUE (name);
ALTER TABLE ONLY tests
    ADD CONSTRAINT tests_pkey PRIMARY KEY (id);
ALTER TABLE ONLY testversions
    ADD CONSTRAINT testsversions_pkey PRIMARY KEY (id);
ALTER TABLE ONLY user_remotecis
    ADD CONSTRAINT user_remotecis_pkey PRIMARY KEY (id);
ALTER TABLE ONLY user_remotecis
    ADD CONSTRAINT user_remotecis_user_id_remoteci_id_key UNIQUE (user_id, remoteci_id);
ALTER TABLE ONLY user_roles
    ADD CONSTRAINT user_roles_pkey PRIMARY KEY (id);
ALTER TABLE ONLY user_roles
    ADD CONSTRAINT user_roles_user_id_role_id_key UNIQUE (user_id, role_id);
ALTER TABLE ONLY users
    ADD CONSTRAINT users_name_key UNIQUE (name);
ALTER TABLE ONLY users
    ADD CONSTRAINT users_pkey PRIMARY KEY (id);
ALTER TABLE ONLY versions
    ADD CONSTRAINT versions_pkey PRIMARY KEY (id);

-- Triggers
CREATE TRIGGER refresh_files_update_at_column BEFORE UPDATE ON files FOR EACH ROW EXECUTE PROCEDURE refresh_update_at_column();
CREATE TRIGGER refresh_jobs_update_at_column BEFORE UPDATE ON jobs FOR EACH ROW EXECUTE PROCEDURE refresh_update_at_column();
CREATE TRIGGER refresh_jobstates_update_at_column BEFORE UPDATE ON jobstates FOR EACH ROW EXECUTE PROCEDURE refresh_update_at_column();
CREATE TRIGGER refresh_remotecis_update_at_column BEFORE UPDATE ON remotecis FOR EACH ROW EXECUTE PROCEDURE refresh_update_at_column();
CREATE TRIGGER refresh_scenarios_update_at_column BEFORE UPDATE ON jobs FOR EACH ROW EXECUTE PROCEDURE refresh_update_at_column();
CREATE TRIGGER refresh_testsversions_update_at_column BEFORE UPDATE ON testversions FOR EACH ROW EXECUTE PROCEDURE refresh_update_at_column();
CREATE TRIGGER verify_jobstates_status BEFORE INSERT OR UPDATE ON jobstates FOR EACH ROW EXECUTE PROCEDURE jobstate_status_in_list();

ALTER TABLE ONLY files
    ADD CONSTRAINT files_status_fkey FOREIGN KEY (jobstate_id) REFERENCES jobstates(id) ON DELETE CASCADE;
ALTER TABLE ONLY files
    ADD CONSTRAINT files_team_id_fkey FOREIGN KEY (team_id) REFERENCES teams(id) ON DELETE CASCADE;
ALTER TABLE ONLY jobs
    ADD CONSTRAINT jobs_remoteci_id_fkey FOREIGN KEY (remoteci_id) REFERENCES remotecis(id) ON DELETE CASCADE;
ALTER TABLE ONLY jobs
    ADD CONSTRAINT jobs_team_id_fkey FOREIGN KEY (team_id) REFERENCES teams(id) ON DELETE CASCADE;
ALTER TABLE ONLY jobs
    ADD CONSTRAINT jobs_testversion_id_fkey FOREIGN KEY (testversion_id) REFERENCES testversions(id) ON DELETE CASCADE;
ALTER TABLE ONLY jobstates
    ADD CONSTRAINT jobstates_team_id_fkey FOREIGN KEY (team_id) REFERENCES teams(id) ON DELETE CASCADE;
ALTER TABLE ONLY remotecis
    ADD CONSTRAINT remotecis_team_id_fkey FOREIGN KEY (team_id) REFERENCES teams(id) ON DELETE CASCADE;
ALTER TABLE ONLY remotecis
    ADD CONSTRAINT remotecis_test_id_fkey FOREIGN KEY (test_id) REFERENCES tests(id) ON DELETE CASCADE;
ALTER TABLE ONLY jobstates
    ADD CONSTRAINT status_job_fkey FOREIGN KEY (job_id) REFERENCES jobs(id) ON DELETE CASCADE;
ALTER TABLE ONLY testversions
    ADD CONSTRAINT testsversions_test_id_fkey FOREIGN KEY (test_id) REFERENCES tests(id) ON DELETE CASCADE;
ALTER TABLE ONLY testversions
    ADD CONSTRAINT testsversions_version_id_fkey FOREIGN KEY (version_id) REFERENCES versions(id) ON DELETE CASCADE;
ALTER TABLE ONLY user_remotecis
    ADD CONSTRAINT user_remotecis_remoteci_id_fkey FOREIGN KEY (remoteci_id) REFERENCES remotecis(id) ON DELETE CASCADE;
ALTER TABLE ONLY user_remotecis
    ADD CONSTRAINT user_remotecis_user_id_fkey FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE;
ALTER TABLE ONLY user_roles
    ADD CONSTRAINT user_roles_role_id_fkey FOREIGN KEY (role_id) REFERENCES roles(id) ON DELETE CASCADE;
ALTER TABLE ONLY user_roles
    ADD CONSTRAINT user_roles_user_id_fkey FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE;
ALTER TABLE ONLY users
    ADD CONSTRAINT users_team_id_fkey FOREIGN KEY (team_id) REFERENCES teams(id) ON DELETE CASCADE;
ALTER TABLE ONLY versions
    ADD CONSTRAINT versions_product_id_fkey FOREIGN KEY (product_id) REFERENCES products(id) ON DELETE CASCADE;
REVOKE ALL ON SCHEMA public FROM PUBLIC;
GRANT ALL ON SCHEMA public TO PUBLIC;
