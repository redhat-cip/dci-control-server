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
    uuid uuid DEFAULT gen_uuid() NOT NULL,
    created_at date DEFAULT now() NOT NULL,
    updated_at date,
    name character varying(255) NOT NULL
);


ALTER TABLE public.environments OWNER TO boa;

--
-- Name: job_environments; Type: TABLE; Schema: public; Owner: boa; Tablespace: 
--

CREATE TABLE job_environments (
    uuid uuid DEFAULT gen_uuid() NOT NULL,
    environment uuid,
    job uuid,
    create_at date DEFAULT now() NOT NULL
);


ALTER TABLE public.job_environments OWNER TO boa;

--
-- Name: jobs; Type: TABLE; Schema: public; Owner: boa; Tablespace: 
--

CREATE TABLE jobs (
    uuid uuid DEFAULT gen_uuid() NOT NULL,
    created_at date DEFAULT now() NOT NULL,
    updated_at date,
    name character varying(255) NOT NULL,
    description text,
    platform uuid NOT NULL,
    status character varying(12) DEFAULT 'NEW'::text NOT NULL,
    content text NOT NULL,
    finished_at date
);


ALTER TABLE public.jobs OWNER TO boa;

--
-- Name: logs; Type: TABLE; Schema: public; Owner: boa; Tablespace: 
--

CREATE TABLE logs (
    uuid uuid DEFAULT gen_uuid() NOT NULL,
    created_at date DEFAULT now() NOT NULL,
    updated_at date,
    name text NOT NULL,
    content bytea NOT NULL,
    mime character varying(100) NOT NULL,
    checksum character varying(64) NOT NULL,
    job uuid NOT NULL
);


ALTER TABLE public.logs OWNER TO boa;

--
-- Name: platforms; Type: TABLE; Schema: public; Owner: boa; Tablespace: 
--

CREATE TABLE platforms (
    uuid uuid DEFAULT gen_uuid() NOT NULL,
    created_at date DEFAULT now() NOT NULL,
    updated_at date,
    name character varying(255)
);


ALTER TABLE public.platforms OWNER TO boa;

--
-- Name: environments_name_key; Type: CONSTRAINT; Schema: public; Owner: boa; Tablespace: 
--

ALTER TABLE ONLY environments
    ADD CONSTRAINT environments_name_key UNIQUE (name);


--
-- Name: environments_pkey; Type: CONSTRAINT; Schema: public; Owner: boa; Tablespace: 
--

ALTER TABLE ONLY environments
    ADD CONSTRAINT environments_pkey PRIMARY KEY (uuid);


--
-- Name: job_environments_pkey; Type: CONSTRAINT; Schema: public; Owner: boa; Tablespace: 
--

ALTER TABLE ONLY job_environments
    ADD CONSTRAINT job_environments_pkey PRIMARY KEY (uuid);


--
-- Name: jobs_name_key; Type: CONSTRAINT; Schema: public; Owner: boa; Tablespace: 
--

ALTER TABLE ONLY jobs
    ADD CONSTRAINT jobs_name_key UNIQUE (name);


--
-- Name: jobs_pkey; Type: CONSTRAINT; Schema: public; Owner: boa; Tablespace: 
--

ALTER TABLE ONLY jobs
    ADD CONSTRAINT jobs_pkey PRIMARY KEY (uuid);


--
-- Name: logs_pkey; Type: CONSTRAINT; Schema: public; Owner: boa; Tablespace: 
--

ALTER TABLE ONLY logs
    ADD CONSTRAINT logs_pkey PRIMARY KEY (uuid);


--
-- Name: platforms_pkey; Type: CONSTRAINT; Schema: public; Owner: boa; Tablespace: 
--

ALTER TABLE ONLY platforms
    ADD CONSTRAINT platforms_pkey PRIMARY KEY (uuid);


--
-- Name: refresh_environments_update_at_column; Type: TRIGGER; Schema: public; Owner: boa
--

CREATE TRIGGER refresh_environments_update_at_column BEFORE UPDATE ON environments FOR EACH ROW EXECUTE PROCEDURE refresh_update_at_column();


--
-- Name: refresh_jobs_update_at_column; Type: TRIGGER; Schema: public; Owner: boa
--

CREATE TRIGGER refresh_jobs_update_at_column BEFORE UPDATE ON jobs FOR EACH ROW EXECUTE PROCEDURE refresh_update_at_column();


--
-- Name: refresh_logs_update_at_column; Type: TRIGGER; Schema: public; Owner: boa
--

CREATE TRIGGER refresh_logs_update_at_column BEFORE UPDATE ON logs FOR EACH ROW EXECUTE PROCEDURE refresh_update_at_column();


--
-- Name: refresh_platforms_update_at_column; Type: TRIGGER; Schema: public; Owner: boa
--

CREATE TRIGGER refresh_platforms_update_at_column BEFORE UPDATE ON platforms FOR EACH ROW EXECUTE PROCEDURE refresh_update_at_column();


--
-- Name: job_environments_environment_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: boa
--

ALTER TABLE ONLY job_environments
    ADD CONSTRAINT job_environments_environment_id_fkey FOREIGN KEY (environment) REFERENCES environments(uuid) ON DELETE CASCADE;


--
-- Name: job_environments_job_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: boa
--

ALTER TABLE ONLY job_environments
    ADD CONSTRAINT job_environments_job_id_fkey FOREIGN KEY (job) REFERENCES jobs(uuid) ON DELETE CASCADE;


--
-- Name: jobs_platform_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: boa
--

ALTER TABLE ONLY jobs
    ADD CONSTRAINT jobs_platform_id_fkey FOREIGN KEY (platform) REFERENCES platforms(uuid) ON DELETE CASCADE;


--
-- Name: logs_job_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: boa
--

ALTER TABLE ONLY logs
    ADD CONSTRAINT logs_job_id_fkey FOREIGN KEY (job) REFERENCES jobs(uuid) ON DELETE CASCADE;


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

