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
IF new.status IN ('new', 'ongoing', 'success', 'failure') THEN
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
    etag character varying(40) DEFAULT gen_etag() NOT NULL
);


--
-- Name: jobs; Type: TABLE; Schema: public; Owner: -; Tablespace:
--

CREATE TABLE jobs (
    id uuid DEFAULT gen_uuid() NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL,
    remoteci_id uuid NOT NULL,
    etag character varying(40) DEFAULT gen_etag() NOT NULL,
    version_id uuid NOT NULL,
    test_id uuid NOT NULL
);


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
    etag character varying(40) DEFAULT gen_etag() NOT NULL
);


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
-- Name: remotecis; Type: TABLE; Schema: public; Owner: -; Tablespace:
--

CREATE TABLE remotecis (
    id uuid DEFAULT gen_uuid() NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL,
    name character varying(255),
    etag character varying(40) DEFAULT gen_etag() NOT NULL
);


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
-- Name: versions; Type: TABLE; Schema: public; Owner: -; Tablespace:
--

CREATE TABLE versions (
    id uuid NOT NULL,
    created_at timestamp with time zone NOT NULL,
    updated_at timestamp with time zone NOT NULL,
    name character varying(255) NOT NULL,
    etag character varying(40) NOT NULL,
    product_id uuid NOT NULL,
    data json
);


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
    ADD CONSTRAINT notifications_pkey PRIMARY KEY (id, created_at, updated_at, etag);


--
-- Name: products_pkey; Type: CONSTRAINT; Schema: public; Owner: -; Tablespace:
--

ALTER TABLE ONLY products
    ADD CONSTRAINT products_pkey PRIMARY KEY (id);


--
-- Name: remotecis_pkey; Type: CONSTRAINT; Schema: public; Owner: -; Tablespace:
--

ALTER TABLE ONLY remotecis
    ADD CONSTRAINT remotecis_pkey PRIMARY KEY (id);


--
-- Name: status_pkey; Type: CONSTRAINT; Schema: public; Owner: -; Tablespace:
--

ALTER TABLE ONLY jobstates
    ADD CONSTRAINT status_pkey PRIMARY KEY (id);


--
-- Name: tests_pkey; Type: CONSTRAINT; Schema: public; Owner: -; Tablespace:
--

ALTER TABLE ONLY tests
    ADD CONSTRAINT tests_pkey PRIMARY KEY (id);


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
-- Name: verify_jobstates_status; Type: TRIGGER; Schema: public; Owner: -
--

CREATE TRIGGER verify_jobstates_status BEFORE INSERT OR UPDATE ON jobstates FOR EACH ROW EXECUTE PROCEDURE jobstate_status_in_list();


--
-- Name: files_status_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY files
    ADD CONSTRAINT files_status_fkey FOREIGN KEY (jobstate_id) REFERENCES jobstates(id) ON DELETE CASCADE;


--
-- Name: jobs_remoteci_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY jobs
    ADD CONSTRAINT jobs_remoteci_id_fkey FOREIGN KEY (remoteci_id) REFERENCES remotecis(id) ON DELETE CASCADE;


--
-- Name: jobs_test_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY jobs
    ADD CONSTRAINT jobs_test_id_fkey FOREIGN KEY (test_id) REFERENCES tests(id) ON DELETE CASCADE;


--
-- Name: jobs_version_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY jobs
    ADD CONSTRAINT jobs_version_id_fkey FOREIGN KEY (version_id) REFERENCES versions(id) ON DELETE CASCADE;


--
-- Name: notifications_version_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY notifications
    ADD CONSTRAINT notifications_version_id_fkey FOREIGN KEY (version_id) REFERENCES versions(id) ON DELETE CASCADE;


--
-- Name: status_job_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY jobstates
    ADD CONSTRAINT status_job_fkey FOREIGN KEY (job_id) REFERENCES jobs(id) ON DELETE CASCADE;


--
-- Name: versions_product_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY versions
    ADD CONSTRAINT versions_product_id_fkey FOREIGN KEY (product_id) REFERENCES products(id) ON DELETE CASCADE;


--
-- Name: public; Type: ACL; Schema: -; Owner: -
--

REVOKE ALL ON SCHEMA public FROM PUBLIC;
REVOKE ALL ON SCHEMA public FROM postgres;
GRANT ALL ON SCHEMA public TO postgres;
GRANT ALL ON SCHEMA public TO PUBLIC;


--
-- PostgreSQL database dump complete
--

