--
-- PostgreSQL database dump
--

SET statement_timeout = 0;
SET lock_timeout = 0;
SET client_encoding = 'UTF8';
SET standard_conforming_strings = on;
SET check_function_bodies = false;
SET client_min_messages = warning;

--
-- Name: plpgsql; Type: EXTENSION; Schema: -; Owner: -
--

CREATE EXTENSION IF NOT EXISTS plpgsql WITH SCHEMA pg_catalog;


--
-- Name: EXTENSION plpgsql; Type: COMMENT; Schema: -; Owner: -
--

COMMENT ON EXTENSION plpgsql IS 'PL/pgSQL procedural language';


--
-- Name: pgcrypto; Type: EXTENSION; Schema: -; Owner: -
--

CREATE EXTENSION IF NOT EXISTS pgcrypto WITH SCHEMA public;


--
-- Name: EXTENSION pgcrypto; Type: COMMENT; Schema: -; Owner: -
--

COMMENT ON EXTENSION pgcrypto IS 'cryptographic functions';


SET search_path = public, pg_catalog;

--
-- Name: gen_etag(); Type: FUNCTION; Schema: public; Owner: -
--

CREATE FUNCTION gen_etag() RETURNS text
    LANGUAGE sql IMMUTABLE
    AS $$select substring(encode(md5(random()::text)::bytea, 'hex') from 0 for 37)$$;


--
-- Name: gen_uuid(); Type: FUNCTION; Schema: public; Owner: -
--

CREATE FUNCTION gen_uuid() RETURNS uuid
    LANGUAGE sql IMMUTABLE
    AS $$SELECT uuid_in(md5(random()::text)::cstring)$$;


--
-- Name: jobstate_status_in_list(); Type: FUNCTION; Schema: public; Owner: -
--

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


--
-- Name: refresh_update_at_column(); Type: FUNCTION; Schema: public; Owner: -
--

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


--
-- Name: FUNCTION refresh_update_at_column(); Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON FUNCTION refresh_update_at_column() IS 'Refresh the etag and the updated_at on UPDATE.';


SET default_tablespace = '';

SET default_with_oids = false;

--
-- Name: files; Type: TABLE; Schema: public; Owner: -; Tablespace:
--

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


--
-- Name: TABLE files; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON TABLE files IS 'The output of a command execution. The file is associated to a jobstate of a given job.';


--
-- Name: jobs; Type: TABLE; Schema: public; Owner: -; Tablespace:
--

CREATE TABLE jobs (
    id uuid DEFAULT gen_uuid() NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL,
    remoteci_id uuid NOT NULL,
    etag character varying(40) DEFAULT gen_etag() NOT NULL,
    testversion_id uuid NOT NULL,
    team_id uuid NOT NULL
);


--
-- Name: TABLE jobs; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON TABLE jobs IS 'An association between a testversion and a remoteci.';


--
-- Name: COLUMN jobs.testversion_id; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN jobs.testversion_id IS 'If the parameter is empty, the REST API will automatically pick an available testversions.';


--
-- Name: jobstates; Type: TABLE; Schema: public; Owner: -; Tablespace:
--

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


--
-- Name: TABLE jobstates; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON TABLE jobstates IS 'One of the status during the execution of a job. The last one is the last know status.';


--
-- Name: COLUMN jobstates.status; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN jobstates.status IS 'ongoing: the job is still running, failure: the job has failed and this is the last status, success: the job has been run successfully.';


--
-- Name: notifications; Type: TABLE; Schema: public; Owner: -; Tablespace:
--

CREATE TABLE notifications (
    id uuid DEFAULT gen_uuid() NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL,
    etag character varying(40) DEFAULT gen_etag() NOT NULL,
    struct json,
    sent boolean DEFAULT false,
    version_id uuid NOT NULL
);


--
-- Name: TABLE notifications; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON TABLE notifications IS 'experimental: notifications associated to a version.';


--
-- Name: products; Type: TABLE; Schema: public; Owner: -; Tablespace:
--

CREATE TABLE products (
    id uuid DEFAULT gen_uuid() NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL,
    name character varying(255) NOT NULL,
    etag character varying(40) DEFAULT gen_etag() NOT NULL,
    data json
);


--
-- Name: TABLE products; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON TABLE products IS 'A product';


--
-- Name: remotecis; Type: TABLE; Schema: public; Owner: -; Tablespace:
--

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


--
-- Name: TABLE remotecis; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON TABLE remotecis IS 'The remote CI agent that process the test.';


--
-- Name: roles; Type: TABLE; Schema: public; Owner: -; Tablespace:
--

CREATE TABLE roles (
    id uuid DEFAULT gen_uuid() NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL,
    etag character varying(40) DEFAULT gen_etag() NOT NULL,
    name character varying(100)
);


--
-- Name: TABLE roles; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON TABLE roles IS 'The user roles.';


--
-- Name: teams; Type: TABLE; Schema: public; Owner: -; Tablespace:
--

CREATE TABLE teams (
    id uuid DEFAULT gen_uuid() NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL,
    etag character varying(40) DEFAULT gen_etag() NOT NULL,
    name character varying(100)
);


--
-- Name: TABLE teams; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON TABLE teams IS 'The user team. An user can only be in one team. All the resource created by an user are shared with his/her team members.';


--
-- Name: tests; Type: TABLE; Schema: public; Owner: -; Tablespace:
--

CREATE TABLE tests (
    id uuid DEFAULT gen_uuid() NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL,
    name character varying(255) NOT NULL,
    etag character varying(40) DEFAULT gen_etag() NOT NULL,
    data json
);


--
-- Name: TABLE tests; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON TABLE tests IS 'A QA test.';


SET default_with_oids = true;

--
-- Name: testversions; Type: TABLE; Schema: public; Owner: -; Tablespace:
--

CREATE TABLE testversions (
    id uuid DEFAULT gen_uuid() NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL,
    etag character varying(40) DEFAULT gen_etag() NOT NULL,
    test_id uuid NOT NULL,
    version_id uuid NOT NULL
);


--
-- Name: TABLE testversions; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON TABLE testversions IS 'The association between a QA test and a given product version.';


SET default_with_oids = false;

--
-- Name: user_remotecis; Type: TABLE; Schema: public; Owner: -; Tablespace:
--

CREATE TABLE user_remotecis (
    id uuid DEFAULT gen_uuid() NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL,
    etag character varying(40) DEFAULT gen_etag() NOT NULL,
    user_id uuid NOT NULL,
    remoteci_id uuid NOT NULL
);


--
-- Name: TABLE user_remotecis; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON TABLE user_remotecis IS 'experimental';


--
-- Name: user_roles; Type: TABLE; Schema: public; Owner: -; Tablespace:
--

CREATE TABLE user_roles (
    id uuid DEFAULT gen_uuid() NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL,
    etag character varying(40) DEFAULT gen_etag() NOT NULL,
    user_id uuid NOT NULL,
    role_id uuid NOT NULL
);


--
-- Name: TABLE user_roles; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON TABLE user_roles IS 'Relation table between the users and the roles.';


--
-- Name: users; Type: TABLE; Schema: public; Owner: -; Tablespace:
--

CREATE TABLE users (
    id uuid DEFAULT gen_uuid() NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL,
    etag character varying(40) DEFAULT gen_etag() NOT NULL,
    name character varying(100),
    password text,
    team_id uuid NOT NULL
);


--
-- Name: TABLE users; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON TABLE users IS 'The user list.';


--
-- Name: versions; Type: TABLE; Schema: public; Owner: -; Tablespace:
--

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


--
-- Name: TABLE versions; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON TABLE versions IS 'A given product versions. For example, a release tag or a git revision.';


--
-- Name: files_pkey; Type: CONSTRAINT; Schema: public; Owner: -; Tablespace:
--

ALTER TABLE ONLY files
    ADD CONSTRAINT files_pkey PRIMARY KEY (id);


--
-- Name: jobs_pkey; Type: CONSTRAINT; Schema: public; Owner: -; Tablespace:
--

ALTER TABLE ONLY jobs
    ADD CONSTRAINT jobs_pkey PRIMARY KEY (id);


--
-- Name: notifications_pkey; Type: CONSTRAINT; Schema: public; Owner: -; Tablespace:
--

ALTER TABLE ONLY notifications
    ADD CONSTRAINT notifications_pkey PRIMARY KEY (id);


--
-- Name: product_sha_unicity; Type: CONSTRAINT; Schema: public; Owner: -; Tablespace:
--

ALTER TABLE ONLY versions
    ADD CONSTRAINT product_sha_unicity UNIQUE (product_id, sha);


--
-- Name: product_unicity; Type: CONSTRAINT; Schema: public; Owner: -; Tablespace:
--

ALTER TABLE ONLY products
    ADD CONSTRAINT product_unicity UNIQUE (name);


--
-- Name: products_pkey; Type: CONSTRAINT; Schema: public; Owner: -; Tablespace:
--

ALTER TABLE ONLY products
    ADD CONSTRAINT products_pkey PRIMARY KEY (id);


--
-- Name: remotecis_name_key; Type: CONSTRAINT; Schema: public; Owner: -; Tablespace:
--

ALTER TABLE ONLY remotecis
    ADD CONSTRAINT remotecis_name_key UNIQUE (name);


--
-- Name: remotecis_pkey; Type: CONSTRAINT; Schema: public; Owner: -; Tablespace:
--

ALTER TABLE ONLY remotecis
    ADD CONSTRAINT remotecis_pkey PRIMARY KEY (id);


--
-- Name: roles_name_key; Type: CONSTRAINT; Schema: public; Owner: -; Tablespace:
--

ALTER TABLE ONLY roles
    ADD CONSTRAINT roles_name_key UNIQUE (name);


--
-- Name: roles_pkey; Type: CONSTRAINT; Schema: public; Owner: -; Tablespace:
--

ALTER TABLE ONLY roles
    ADD CONSTRAINT roles_pkey PRIMARY KEY (id);


--
-- Name: status_pkey; Type: CONSTRAINT; Schema: public; Owner: -; Tablespace:
--

ALTER TABLE ONLY jobstates
    ADD CONSTRAINT status_pkey PRIMARY KEY (id);


--
-- Name: team_pkey; Type: CONSTRAINT; Schema: public; Owner: -; Tablespace:
--

ALTER TABLE ONLY teams
    ADD CONSTRAINT team_pkey PRIMARY KEY (id);


--
-- Name: teams_name_key; Type: CONSTRAINT; Schema: public; Owner: -; Tablespace:
--

ALTER TABLE ONLY teams
    ADD CONSTRAINT teams_name_key UNIQUE (name);


--
-- Name: tests_pkey; Type: CONSTRAINT; Schema: public; Owner: -; Tablespace:
--

ALTER TABLE ONLY tests
    ADD CONSTRAINT tests_pkey PRIMARY KEY (id);


--
-- Name: testsversions_pkey; Type: CONSTRAINT; Schema: public; Owner: -; Tablespace:
--

ALTER TABLE ONLY testversions
    ADD CONSTRAINT testsversions_pkey PRIMARY KEY (id);


--
-- Name: user_remotecis_pkey; Type: CONSTRAINT; Schema: public; Owner: -; Tablespace:
--

ALTER TABLE ONLY user_remotecis
    ADD CONSTRAINT user_remotecis_pkey PRIMARY KEY (id);


--
-- Name: user_remotecis_user_id_remoteci_id_key; Type: CONSTRAINT; Schema: public; Owner: -; Tablespace:
--

ALTER TABLE ONLY user_remotecis
    ADD CONSTRAINT user_remotecis_user_id_remoteci_id_key UNIQUE (user_id, remoteci_id);


--
-- Name: user_roles_pkey; Type: CONSTRAINT; Schema: public; Owner: -; Tablespace:
--

ALTER TABLE ONLY user_roles
    ADD CONSTRAINT user_roles_pkey PRIMARY KEY (id);


--
-- Name: user_roles_user_id_role_id_key; Type: CONSTRAINT; Schema: public; Owner: -; Tablespace:
--

ALTER TABLE ONLY user_roles
    ADD CONSTRAINT user_roles_user_id_role_id_key UNIQUE (user_id, role_id);


--
-- Name: users_name_key; Type: CONSTRAINT; Schema: public; Owner: -; Tablespace:
--

ALTER TABLE ONLY users
    ADD CONSTRAINT users_name_key UNIQUE (name);


--
-- Name: users_pkey; Type: CONSTRAINT; Schema: public; Owner: -; Tablespace:
--

ALTER TABLE ONLY users
    ADD CONSTRAINT users_pkey PRIMARY KEY (id);


--
-- Name: versions_pkey; Type: CONSTRAINT; Schema: public; Owner: -; Tablespace:
--

ALTER TABLE ONLY versions
    ADD CONSTRAINT versions_pkey PRIMARY KEY (id);


--
-- Name: refresh_files_update_at_column; Type: TRIGGER; Schema: public; Owner: -
--

CREATE TRIGGER refresh_files_update_at_column BEFORE UPDATE ON files FOR EACH ROW EXECUTE PROCEDURE refresh_update_at_column();


--
-- Name: refresh_jobs_update_at_column; Type: TRIGGER; Schema: public; Owner: -
--

CREATE TRIGGER refresh_jobs_update_at_column BEFORE UPDATE ON jobs FOR EACH ROW EXECUTE PROCEDURE refresh_update_at_column();


--
-- Name: refresh_jobstates_update_at_column; Type: TRIGGER; Schema: public; Owner: -
--

CREATE TRIGGER refresh_jobstates_update_at_column BEFORE UPDATE ON jobstates FOR EACH ROW EXECUTE PROCEDURE refresh_update_at_column();


--
-- Name: refresh_remotecis_update_at_column; Type: TRIGGER; Schema: public; Owner: -
--

CREATE TRIGGER refresh_remotecis_update_at_column BEFORE UPDATE ON remotecis FOR EACH ROW EXECUTE PROCEDURE refresh_update_at_column();


--
-- Name: refresh_scenarios_update_at_column; Type: TRIGGER; Schema: public; Owner: -
--

CREATE TRIGGER refresh_scenarios_update_at_column BEFORE UPDATE ON jobs FOR EACH ROW EXECUTE PROCEDURE refresh_update_at_column();


--
-- Name: refresh_testsversions_update_at_column; Type: TRIGGER; Schema: public; Owner: -
--

CREATE TRIGGER refresh_testsversions_update_at_column BEFORE UPDATE ON testversions FOR EACH ROW EXECUTE PROCEDURE refresh_update_at_column();


--
-- Name: verify_jobstates_status; Type: TRIGGER; Schema: public; Owner: -
--

CREATE TRIGGER verify_jobstates_status BEFORE INSERT OR UPDATE ON jobstates FOR EACH ROW EXECUTE PROCEDURE jobstate_status_in_list();


--
-- Name: files_status_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY files
    ADD CONSTRAINT files_status_fkey FOREIGN KEY (jobstate_id) REFERENCES jobstates(id) ON DELETE CASCADE;


--
-- Name: files_team_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY files
    ADD CONSTRAINT files_team_id_fkey FOREIGN KEY (team_id) REFERENCES teams(id) ON DELETE CASCADE;


--
-- Name: jobs_remoteci_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY jobs
    ADD CONSTRAINT jobs_remoteci_id_fkey FOREIGN KEY (remoteci_id) REFERENCES remotecis(id) ON DELETE CASCADE;


--
-- Name: jobs_team_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY jobs
    ADD CONSTRAINT jobs_team_id_fkey FOREIGN KEY (team_id) REFERENCES teams(id) ON DELETE CASCADE;


--
-- Name: jobs_testversion_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY jobs
    ADD CONSTRAINT jobs_testversion_id_fkey FOREIGN KEY (testversion_id) REFERENCES testversions(id) ON DELETE CASCADE;


--
-- Name: jobstates_team_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY jobstates
    ADD CONSTRAINT jobstates_team_id_fkey FOREIGN KEY (team_id) REFERENCES teams(id) ON DELETE CASCADE;


--
-- Name: notifications_version_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY notifications
    ADD CONSTRAINT notifications_version_id_fkey FOREIGN KEY (version_id) REFERENCES versions(id) ON DELETE CASCADE;


--
-- Name: remotecis_team_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY remotecis
    ADD CONSTRAINT remotecis_team_id_fkey FOREIGN KEY (team_id) REFERENCES teams(id) ON DELETE CASCADE;


--
-- Name: remotecis_test_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY remotecis
    ADD CONSTRAINT remotecis_test_id_fkey FOREIGN KEY (test_id) REFERENCES tests(id) ON DELETE CASCADE;


--
-- Name: status_job_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY jobstates
    ADD CONSTRAINT status_job_fkey FOREIGN KEY (job_id) REFERENCES jobs(id) ON DELETE CASCADE;


--
-- Name: testsversions_test_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY testversions
    ADD CONSTRAINT testsversions_test_id_fkey FOREIGN KEY (test_id) REFERENCES tests(id) ON DELETE CASCADE;


--
-- Name: testsversions_version_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY testversions
    ADD CONSTRAINT testsversions_version_id_fkey FOREIGN KEY (version_id) REFERENCES versions(id) ON DELETE CASCADE;


--
-- Name: user_remotecis_remoteci_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY user_remotecis
    ADD CONSTRAINT user_remotecis_remoteci_id_fkey FOREIGN KEY (remoteci_id) REFERENCES remotecis(id) ON DELETE CASCADE;


--
-- Name: user_remotecis_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY user_remotecis
    ADD CONSTRAINT user_remotecis_user_id_fkey FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE;


--
-- Name: user_roles_role_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY user_roles
    ADD CONSTRAINT user_roles_role_id_fkey FOREIGN KEY (role_id) REFERENCES roles(id) ON DELETE CASCADE;


--
-- Name: user_roles_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY user_roles
    ADD CONSTRAINT user_roles_user_id_fkey FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE;


--
-- Name: users_team_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY users
    ADD CONSTRAINT users_team_id_fkey FOREIGN KEY (team_id) REFERENCES teams(id) ON DELETE CASCADE;


--
-- Name: versions_product_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY versions
    ADD CONSTRAINT versions_product_id_fkey FOREIGN KEY (product_id) REFERENCES products(id) ON DELETE CASCADE;


--
-- Name: public; Type: ACL; Schema: -; Owner: -
--

REVOKE ALL ON SCHEMA public FROM PUBLIC;
GRANT ALL ON SCHEMA public TO PUBLIC;
