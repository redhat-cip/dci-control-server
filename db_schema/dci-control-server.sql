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
-- Name: plpgsql; Type: EXTENSION; Schema: -; Owner:
--

CREATE EXTENSION IF NOT EXISTS plpgsql WITH SCHEMA pg_catalog;


--
-- Name: EXTENSION plpgsql; Type: COMMENT; Schema: -; Owner:
--

COMMENT ON EXTENSION plpgsql IS 'PL/pgSQL procedural language';


SET search_path = public, pg_catalog;

--
-- Name: gen_uuid(); Type: FUNCTION; Schema: public; Owner: postgres
--

CREATE FUNCTION gen_uuid() RETURNS uuid
    LANGUAGE sql IMMUTABLE
    AS $$SELECT uuid_in(md5(random()::text)::cstring)$$;


ALTER FUNCTION public.gen_uuid() OWNER TO postgres;

--
-- Name: jobstate_status_in_list(); Type: FUNCTION; Schema: public; Owner: boa
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


ALTER FUNCTION public.jobstate_status_in_list() OWNER TO boa;

--
-- Name: refresh_update_at_column(); Type: FUNCTION; Schema: public; Owner: postgres
--

CREATE FUNCTION refresh_update_at_column() RETURNS trigger
    LANGUAGE plpgsql
    AS $$ BEGIN NEW.updated_at = now(); RETURN NEW; END; $$;


ALTER FUNCTION public.refresh_update_at_column() OWNER TO postgres;

SET default_tablespace = '';

SET default_with_oids = false;

--
-- Name: environments; Type: TABLE; Schema: public; Owner: boa; Tablespace:
--

CREATE TABLE environments (
    id uuid DEFAULT gen_uuid() NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone,
    name character varying(255) NOT NULL
);


ALTER TABLE public.environments OWNER TO boa;

--
-- Name: files; Type: TABLE; Schema: public; Owner: boa; Tablespace:
--

CREATE TABLE files (
    id uuid DEFAULT gen_uuid() NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone,
    name character varying(512) NOT NULL,
    content text NOT NULL,
    mime character varying(100) DEFAULT 'text/plain'::character varying NOT NULL,
    md5 character varying(32),
    jobstate_id uuid NOT NULL
);


ALTER TABLE public.files OWNER TO boa;

--
-- Name: jobs; Type: TABLE; Schema: public; Owner: boa; Tablespace:
--

CREATE TABLE jobs (
    id uuid DEFAULT gen_uuid() NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone,
    platform_id uuid NOT NULL,
    scenario_id uuid NOT NULL,
    environment_id uuid NOT NULL
);


ALTER TABLE public.jobs OWNER TO boa;

--
-- Name: jobstates; Type: TABLE; Schema: public; Owner: boa; Tablespace:
--

CREATE TABLE jobstates (
    id uuid DEFAULT gen_uuid() NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone,
    status character varying,
    comment text,
    job_id uuid NOT NULL
);


ALTER TABLE public.jobstates OWNER TO boa;

--
-- Name: platforms; Type: TABLE; Schema: public; Owner: boa; Tablespace:
--

CREATE TABLE platforms (
    id uuid DEFAULT gen_uuid() NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone,
    name character varying(255)
);


ALTER TABLE public.platforms OWNER TO boa;

--
-- Name: scenarios; Type: TABLE; Schema: public; Owner: boa; Tablespace:
--

CREATE TABLE scenarios (
    id uuid DEFAULT gen_uuid() NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone,
    name character varying(255) NOT NULL,
    content text NOT NULL
);


ALTER TABLE public.scenarios OWNER TO boa;

--
-- Name: environments_name_key; Type: CONSTRAINT; Schema: public; Owner: boa; Tablespace:
--

ALTER TABLE ONLY environments
    ADD CONSTRAINT environments_name_key UNIQUE (name);


--
-- Name: environments_pkey; Type: CONSTRAINT; Schema: public; Owner: boa; Tablespace:
--

ALTER TABLE ONLY environments
    ADD CONSTRAINT environments_pkey PRIMARY KEY (id);


--
-- Name: files_pkey; Type: CONSTRAINT; Schema: public; Owner: boa; Tablespace:
--

ALTER TABLE ONLY files
    ADD CONSTRAINT files_pkey PRIMARY KEY (id);


--
-- Name: jobs_pkey; Type: CONSTRAINT; Schema: public; Owner: boa; Tablespace:
--

ALTER TABLE ONLY jobs
    ADD CONSTRAINT jobs_pkey PRIMARY KEY (id);


--
-- Name: platforms_pkey; Type: CONSTRAINT; Schema: public; Owner: boa; Tablespace:
--

ALTER TABLE ONLY platforms
    ADD CONSTRAINT platforms_pkey PRIMARY KEY (id);


--
-- Name: scenarios_name_key; Type: CONSTRAINT; Schema: public; Owner: boa; Tablespace:
--

ALTER TABLE ONLY scenarios
    ADD CONSTRAINT scenarios_name_key UNIQUE (name);


--
-- Name: scenarios_pkey; Type: CONSTRAINT; Schema: public; Owner: boa; Tablespace:
--

ALTER TABLE ONLY scenarios
    ADD CONSTRAINT scenarios_pkey PRIMARY KEY (id);


--
-- Name: status_pkey; Type: CONSTRAINT; Schema: public; Owner: boa; Tablespace:
--

ALTER TABLE ONLY jobstates
    ADD CONSTRAINT status_pkey PRIMARY KEY (id);


--
-- Name: refresh_environments_update_at_column; Type: TRIGGER; Schema: public; Owner: boa
--

CREATE TRIGGER refresh_environments_update_at_column BEFORE UPDATE ON environments FOR EACH ROW EXECUTE PROCEDURE refresh_update_at_column();


--
-- Name: refresh_files_update_at_column; Type: TRIGGER; Schema: public; Owner: boa
--

CREATE TRIGGER refresh_files_update_at_column BEFORE UPDATE ON files FOR EACH ROW EXECUTE PROCEDURE refresh_update_at_column();


--
-- Name: refresh_jobs_update_at_column; Type: TRIGGER; Schema: public; Owner: boa
--

CREATE TRIGGER refresh_jobs_update_at_column BEFORE UPDATE ON jobs FOR EACH ROW EXECUTE PROCEDURE refresh_update_at_column();


--
-- Name: refresh_jobstates_update_at_column; Type: TRIGGER; Schema: public; Owner: boa
--

CREATE TRIGGER refresh_jobstates_update_at_column BEFORE UPDATE ON jobstates FOR EACH ROW EXECUTE PROCEDURE refresh_update_at_column();


--
-- Name: refresh_platforms_update_at_column; Type: TRIGGER; Schema: public; Owner: boa
--

CREATE TRIGGER refresh_platforms_update_at_column BEFORE UPDATE ON platforms FOR EACH ROW EXECUTE PROCEDURE refresh_update_at_column();


--
-- Name: refresh_scenarios_update_at_column; Type: TRIGGER; Schema: public; Owner: boa
--

CREATE TRIGGER refresh_scenarios_update_at_column BEFORE UPDATE ON jobs FOR EACH ROW EXECUTE PROCEDURE refresh_update_at_column();


--
-- Name: verify_jobstates_status; Type: TRIGGER; Schema: public; Owner: boa
--

CREATE TRIGGER verify_jobstates_status BEFORE INSERT OR UPDATE ON jobstates FOR EACH ROW EXECUTE PROCEDURE jobstate_status_in_list();


--
-- Name: files_status_fkey; Type: FK CONSTRAINT; Schema: public; Owner: boa
--

ALTER TABLE ONLY files
    ADD CONSTRAINT files_status_fkey FOREIGN KEY (jobstate_id) REFERENCES jobstates(id) ON DELETE CASCADE;


--
-- Name: jobs_environment_fkey; Type: FK CONSTRAINT; Schema: public; Owner: boa
--

ALTER TABLE ONLY jobs
    ADD CONSTRAINT jobs_environment_fkey FOREIGN KEY (environment_id) REFERENCES environments(id) ON DELETE CASCADE;


--
-- Name: jobs_platform_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: boa
--

ALTER TABLE ONLY jobs
    ADD CONSTRAINT jobs_platform_id_fkey FOREIGN KEY (platform_id) REFERENCES platforms(id) ON DELETE CASCADE;


--
-- Name: jobs_scenario_fkey; Type: FK CONSTRAINT; Schema: public; Owner: boa
--

ALTER TABLE ONLY jobs
    ADD CONSTRAINT jobs_scenario_fkey FOREIGN KEY (scenario_id) REFERENCES scenarios(id) ON DELETE CASCADE;


--
-- Name: status_job_fkey; Type: FK CONSTRAINT; Schema: public; Owner: boa
--

ALTER TABLE ONLY jobstates
    ADD CONSTRAINT status_job_fkey FOREIGN KEY (job_id) REFERENCES jobs(id) ON DELETE CASCADE;


--
-- Name: public; Type: ACL; Schema: -; Owner: postgres
--

REVOKE ALL ON SCHEMA public FROM PUBLIC;
REVOKE ALL ON SCHEMA public FROM postgres;
GRANT ALL ON SCHEMA public TO postgres;
GRANT ALL ON SCHEMA public TO PUBLIC;


--
-- PostgreSQL database dump complete
--

