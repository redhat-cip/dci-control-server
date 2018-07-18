--
-- PostgreSQL database cluster dump
--

SET default_transaction_read_only = off;

SET client_encoding = 'UTF8';
SET standard_conforming_strings = on;

--
-- Drop databases
--

DROP DATABASE dci;




--
-- Drop roles
--

DROP ROLE dci;
DROP ROLE postgres;


--
-- Roles
--

CREATE ROLE dci;
ALTER ROLE dci WITH SUPERUSER INHERIT NOCREATEROLE NOCREATEDB LOGIN NOREPLICATION PASSWORD 'md5544fa7d5b8627ef63de912301fdbb7e7';
CREATE ROLE postgres;
ALTER ROLE postgres WITH SUPERUSER INHERIT CREATEROLE CREATEDB LOGIN REPLICATION;






--
-- Database creation
--

CREATE DATABASE dci WITH TEMPLATE = template0 OWNER = dci;
REVOKE ALL ON DATABASE template1 FROM PUBLIC;
REVOKE ALL ON DATABASE template1 FROM postgres;
GRANT ALL ON DATABASE template1 TO postgres;
GRANT CONNECT ON DATABASE template1 TO PUBLIC;


\connect dci

SET default_transaction_read_only = off;

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
-- Name: final_statuses; Type: TYPE; Schema: public; Owner: dci
--

CREATE TYPE final_statuses AS ENUM (
    'success',
    'failure',
    'error'
);


ALTER TYPE final_statuses OWNER TO dci;

--
-- Name: states; Type: TYPE; Schema: public; Owner: dci
--

CREATE TYPE states AS ENUM (
    'active',
    'inactive',
    'archived'
);


ALTER TYPE states OWNER TO dci;

--
-- Name: statuses; Type: TYPE; Schema: public; Owner: dci
--

CREATE TYPE statuses AS ENUM (
    'new',
    'pre-run',
    'running',
    'post-run',
    'success',
    'failure',
    'killed',
    'error'
);


ALTER TYPE statuses OWNER TO dci;

--
-- Name: trackers; Type: TYPE; Schema: public; Owner: dci
--

CREATE TYPE trackers AS ENUM (
    'github',
    'bugzilla'
);


ALTER TYPE trackers OWNER TO dci;

SET default_tablespace = '';

SET default_with_oids = false;

--
-- Name: alembic_version; Type: TABLE; Schema: public; Owner: dci; Tablespace: 
--

CREATE TABLE alembic_version (
    version_num character varying(32) NOT NULL
);


ALTER TABLE alembic_version OWNER TO dci;

--
-- Name: component_files; Type: TABLE; Schema: public; Owner: dci; Tablespace: 
--

CREATE TABLE component_files (
    id uuid NOT NULL,
    created_at timestamp without time zone NOT NULL,
    updated_at timestamp without time zone NOT NULL,
    name character varying(255) NOT NULL,
    mime character varying,
    md5 character varying(32),
    size bigint,
    component_id uuid,
    state states,
    etag character varying(40) NOT NULL
);


ALTER TABLE component_files OWNER TO dci;

--
-- Name: components; Type: TABLE; Schema: public; Owner: dci; Tablespace: 
--

CREATE TABLE components (
    id uuid NOT NULL,
    created_at timestamp without time zone NOT NULL,
    updated_at timestamp without time zone NOT NULL,
    etag character varying(40) NOT NULL,
    name character varying(255) NOT NULL,
    type character varying(255) NOT NULL,
    canonical_project_name character varying,
    data json,
    title text,
    message text,
    url text,
    export_control boolean NOT NULL,
    topic_id uuid,
    state states
);


ALTER TABLE components OWNER TO dci;

--
-- Name: components_issues; Type: TABLE; Schema: public; Owner: dci; Tablespace: 
--

CREATE TABLE components_issues (
    component_id uuid NOT NULL,
    issue_id uuid NOT NULL,
    user_id uuid NOT NULL
);


ALTER TABLE components_issues OWNER TO dci;

--
-- Name: counter; Type: TABLE; Schema: public; Owner: dci; Tablespace: 
--

CREATE TABLE counter (
    created_at timestamp without time zone NOT NULL,
    updated_at timestamp without time zone NOT NULL,
    name character varying(255) NOT NULL,
    sequence integer,
    etag character varying(40) NOT NULL
);


ALTER TABLE counter OWNER TO dci;

--
-- Name: feeders; Type: TABLE; Schema: public; Owner: dci; Tablespace: 
--

CREATE TABLE feeders (
    id uuid NOT NULL,
    created_at timestamp without time zone NOT NULL,
    updated_at timestamp without time zone NOT NULL,
    etag character varying(40) NOT NULL,
    name character varying(255) NOT NULL,
    data json,
    api_secret character varying(64),
    team_id uuid NOT NULL,
    role_id uuid,
    state states
);


ALTER TABLE feeders OWNER TO dci;

--
-- Name: files; Type: TABLE; Schema: public; Owner: dci; Tablespace: 
--

CREATE TABLE files (
    id uuid NOT NULL,
    created_at timestamp without time zone NOT NULL,
    updated_at timestamp without time zone NOT NULL,
    name character varying(255) NOT NULL,
    mime character varying,
    md5 character varying(32),
    size bigint,
    jobstate_id uuid,
    test_id uuid,
    team_id uuid NOT NULL,
    job_id uuid,
    state states,
    etag character varying(40) NOT NULL
);


ALTER TABLE files OWNER TO dci;

--
-- Name: issues; Type: TABLE; Schema: public; Owner: dci; Tablespace: 
--

CREATE TABLE issues (
    id uuid NOT NULL,
    created_at timestamp without time zone NOT NULL,
    updated_at timestamp without time zone NOT NULL,
    url text,
    tracker trackers NOT NULL
);


ALTER TABLE issues OWNER TO dci;

--
-- Name: jobs; Type: TABLE; Schema: public; Owner: dci; Tablespace: 
--

CREATE TABLE jobs (
    id uuid NOT NULL,
    created_at timestamp without time zone NOT NULL,
    updated_at timestamp without time zone NOT NULL,
    etag character varying(40) NOT NULL,
    comment text,
    status statuses,
    rconfiguration_id uuid,
    topic_id uuid,
    remoteci_id uuid NOT NULL,
    team_id uuid NOT NULL,
    user_agent character varying(255),
    client_version character varying(255),
    previous_job_id uuid,
    state states,
    update_previous_job_id uuid
);


ALTER TABLE jobs OWNER TO dci;

--
-- Name: jobs_components; Type: TABLE; Schema: public; Owner: dci; Tablespace: 
--

CREATE TABLE jobs_components (
    job_id uuid NOT NULL,
    component_id uuid NOT NULL
);


ALTER TABLE jobs_components OWNER TO dci;

--
-- Name: jobs_events; Type: TABLE; Schema: public; Owner: dci; Tablespace: 
--

CREATE TABLE jobs_events (
    id integer NOT NULL,
    created_at timestamp without time zone NOT NULL,
    job_id uuid NOT NULL,
    topic_id uuid NOT NULL,
    status final_statuses
);


ALTER TABLE jobs_events OWNER TO dci;

--
-- Name: jobs_events_id_seq; Type: SEQUENCE; Schema: public; Owner: dci
--

CREATE SEQUENCE jobs_events_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE jobs_events_id_seq OWNER TO dci;

--
-- Name: jobs_events_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: dci
--

ALTER SEQUENCE jobs_events_id_seq OWNED BY jobs_events.id;


--
-- Name: jobs_issues; Type: TABLE; Schema: public; Owner: dci; Tablespace: 
--

CREATE TABLE jobs_issues (
    job_id uuid NOT NULL,
    issue_id uuid NOT NULL,
    user_id uuid
);


ALTER TABLE jobs_issues OWNER TO dci;

--
-- Name: jobstates; Type: TABLE; Schema: public; Owner: dci; Tablespace: 
--

CREATE TABLE jobstates (
    id uuid NOT NULL,
    created_at timestamp without time zone NOT NULL,
    status statuses NOT NULL,
    comment text,
    job_id uuid NOT NULL,
    team_id uuid NOT NULL
);


ALTER TABLE jobstates OWNER TO dci;

--
-- Name: logs; Type: TABLE; Schema: public; Owner: dci; Tablespace: 
--

CREATE TABLE logs (
    id uuid NOT NULL,
    created_at timestamp without time zone NOT NULL,
    user_id uuid NOT NULL,
    team_id uuid NOT NULL,
    action text NOT NULL
);


ALTER TABLE logs OWNER TO dci;

--
-- Name: metas; Type: TABLE; Schema: public; Owner: dci; Tablespace: 
--

CREATE TABLE metas (
    id uuid NOT NULL,
    created_at timestamp without time zone NOT NULL,
    updated_at timestamp without time zone NOT NULL,
    etag character varying(40) NOT NULL,
    name text,
    value text,
    job_id uuid NOT NULL
);


ALTER TABLE metas OWNER TO dci;

--
-- Name: permissions; Type: TABLE; Schema: public; Owner: dci; Tablespace: 
--

CREATE TABLE permissions (
    id uuid NOT NULL,
    created_at timestamp without time zone NOT NULL,
    updated_at timestamp without time zone NOT NULL,
    etag character varying(40) NOT NULL,
    name character varying(255) NOT NULL,
    label character varying(255) NOT NULL,
    description text,
    state states
);


ALTER TABLE permissions OWNER TO dci;

--
-- Name: products; Type: TABLE; Schema: public; Owner: dci; Tablespace: 
--

CREATE TABLE products (
    id uuid NOT NULL,
    created_at timestamp without time zone NOT NULL,
    updated_at timestamp without time zone NOT NULL,
    etag character varying(40) NOT NULL,
    name character varying(255) NOT NULL,
    label character varying(255) NOT NULL,
    description text,
    state states,
    team_id uuid NOT NULL
);


ALTER TABLE products OWNER TO dci;

--
-- Name: rconfigurations; Type: TABLE; Schema: public; Owner: dci; Tablespace: 
--

CREATE TABLE rconfigurations (
    id uuid NOT NULL,
    created_at timestamp without time zone NOT NULL,
    updated_at timestamp without time zone NOT NULL,
    etag character varying(40) NOT NULL,
    state states,
    topic_id uuid,
    name character varying(255) NOT NULL,
    component_types json,
    data json
);


ALTER TABLE rconfigurations OWNER TO dci;

--
-- Name: remoteci_tests; Type: TABLE; Schema: public; Owner: dci; Tablespace: 
--

CREATE TABLE remoteci_tests (
    remoteci_id uuid NOT NULL,
    test_id uuid NOT NULL
);


ALTER TABLE remoteci_tests OWNER TO dci;

--
-- Name: remotecis; Type: TABLE; Schema: public; Owner: dci; Tablespace: 
--

CREATE TABLE remotecis (
    id uuid NOT NULL,
    created_at timestamp without time zone NOT NULL,
    updated_at timestamp without time zone NOT NULL,
    etag character varying(40) NOT NULL,
    name character varying(255),
    data json,
    api_secret character varying(64),
    team_id uuid NOT NULL,
    role_id uuid,
    public boolean,
    state states,
    cert_fp character varying(255)
);


ALTER TABLE remotecis OWNER TO dci;

--
-- Name: remotecis_rconfigurations; Type: TABLE; Schema: public; Owner: dci; Tablespace: 
--

CREATE TABLE remotecis_rconfigurations (
    remoteci_id uuid NOT NULL,
    rconfiguration_id uuid NOT NULL
);


ALTER TABLE remotecis_rconfigurations OWNER TO dci;

--
-- Name: roles; Type: TABLE; Schema: public; Owner: dci; Tablespace: 
--

CREATE TABLE roles (
    id uuid NOT NULL,
    created_at timestamp without time zone NOT NULL,
    updated_at timestamp without time zone NOT NULL,
    etag character varying(40) NOT NULL,
    name character varying(255) NOT NULL,
    label character varying(255) NOT NULL,
    description text,
    state states
);


ALTER TABLE roles OWNER TO dci;

--
-- Name: roles_permissions; Type: TABLE; Schema: public; Owner: dci; Tablespace: 
--

CREATE TABLE roles_permissions (
    role_id uuid NOT NULL,
    permission_id uuid NOT NULL
);


ALTER TABLE roles_permissions OWNER TO dci;

--
-- Name: teams; Type: TABLE; Schema: public; Owner: dci; Tablespace: 
--

CREATE TABLE teams (
    id uuid NOT NULL,
    created_at timestamp without time zone NOT NULL,
    updated_at timestamp without time zone NOT NULL,
    etag character varying(40) NOT NULL,
    name character varying(255) NOT NULL,
    country character varying(255),
    state states,
    external boolean,
    parent_id uuid
);


ALTER TABLE teams OWNER TO dci;

--
-- Name: tests; Type: TABLE; Schema: public; Owner: dci; Tablespace: 
--

CREATE TABLE tests (
    id uuid NOT NULL,
    created_at timestamp without time zone NOT NULL,
    updated_at timestamp without time zone NOT NULL,
    name character varying(255) NOT NULL,
    data json,
    team_id uuid NOT NULL,
    state states,
    etag character varying(40) NOT NULL
);


ALTER TABLE tests OWNER TO dci;

--
-- Name: tests_results; Type: TABLE; Schema: public; Owner: dci; Tablespace: 
--

CREATE TABLE tests_results (
    id uuid NOT NULL,
    created_at timestamp without time zone NOT NULL,
    updated_at timestamp without time zone NOT NULL,
    name character varying(255) NOT NULL,
    total integer,
    success integer,
    skips integer,
    failures integer,
    errors integer,
    "time" integer,
    job_id uuid NOT NULL,
    file_id uuid NOT NULL,
    tests_cases json,
    regressions integer
);


ALTER TABLE tests_results OWNER TO dci;

--
-- Name: topic_tests; Type: TABLE; Schema: public; Owner: dci; Tablespace: 
--

CREATE TABLE topic_tests (
    topic_id uuid NOT NULL,
    test_id uuid NOT NULL
);


ALTER TABLE topic_tests OWNER TO dci;

--
-- Name: topics; Type: TABLE; Schema: public; Owner: dci; Tablespace: 
--

CREATE TABLE topics (
    id uuid NOT NULL,
    created_at timestamp without time zone NOT NULL,
    updated_at timestamp without time zone NOT NULL,
    etag character varying(40) NOT NULL,
    name character varying(255) NOT NULL,
    label text,
    component_types json,
    product_id uuid,
    state states,
    data json,
    next_topic_id uuid
);


ALTER TABLE topics OWNER TO dci;

--
-- Name: topics_teams; Type: TABLE; Schema: public; Owner: dci; Tablespace: 
--

CREATE TABLE topics_teams (
    topic_id uuid NOT NULL,
    team_id uuid NOT NULL
);


ALTER TABLE topics_teams OWNER TO dci;

--
-- Name: user_remotecis; Type: TABLE; Schema: public; Owner: dci; Tablespace: 
--

CREATE TABLE user_remotecis (
    user_id uuid NOT NULL,
    remoteci_id uuid NOT NULL
);


ALTER TABLE user_remotecis OWNER TO dci;

--
-- Name: users; Type: TABLE; Schema: public; Owner: dci; Tablespace: 
--

CREATE TABLE users (
    id uuid NOT NULL,
    created_at timestamp without time zone NOT NULL,
    updated_at timestamp without time zone NOT NULL,
    etag character varying(40) NOT NULL,
    name character varying(255) NOT NULL,
    sso_username character varying(255),
    fullname character varying(255) NOT NULL,
    email character varying(255) NOT NULL,
    password text,
    timezone character varying(255) NOT NULL,
    role_id uuid,
    team_id uuid,
    state states
);


ALTER TABLE users OWNER TO dci;

--
-- Name: id; Type: DEFAULT; Schema: public; Owner: dci
--

ALTER TABLE ONLY jobs_events ALTER COLUMN id SET DEFAULT nextval('jobs_events_id_seq'::regclass);


--
-- Data for Name: alembic_version; Type: TABLE DATA; Schema: public; Owner: dci
--

COPY alembic_version (version_num) FROM stdin;
d7d29a66aac5
\.


--
-- Data for Name: component_files; Type: TABLE DATA; Schema: public; Owner: dci
--

COPY component_files (id, created_at, updated_at, name, mime, md5, size, component_id, state, etag) FROM stdin;
\.


--
-- Data for Name: components; Type: TABLE DATA; Schema: public; Owner: dci
--

COPY components (id, created_at, updated_at, etag, name, type, canonical_project_name, data, title, message, url, export_control, topic_id, state) FROM stdin;
bafbf13f-1173-46f3-978b-5c479c70dc16	2018-07-18 14:13:14.421132	2018-07-18 14:13:14.421132	abaf08cf9810c7a4591555b930c29ff5	RH7-RHOS-10.0 2016-10-28.1	puddle	\N	{}	\N	\N	\N	t	9a73cedf-8a9a-4a31-a09a-4c8a6d46e7a1	active
e6068b41-65b3-450a-aa35-7b6c4228d1ca	2018-07-18 14:13:14.881057	2018-07-18 14:13:14.881057	51483d85702e6cf0ede425e806b485ea	RH7-RHOS-10.0 2016-11-12.1	puddle	\N	{}	\N	\N	\N	t	9a73cedf-8a9a-4a31-a09a-4c8a6d46e7a1	active
da35b887-e390-4790-b131-74307c09cb34	2018-07-18 14:13:15.363931	2018-07-18 14:13:15.363931	303ec41603f49af6ede5fcfce8a423ee	RH7-RHOS-11.0 2016-11-11.1	puddle	\N	{}	\N	\N	\N	t	2bc8911f-6bac-4d85-85c7-5654b65d4acb	active
ae1f4397-4a84-4cdb-9c38-c7a9623b591b	2018-07-18 14:13:15.833212	2018-07-18 14:13:15.833212	e34e9f41a369483eb5384e4779feb215	RH7-RHOS-12.0 2016-11-12.1	puddle	\N	{}	\N	\N	\N	t	04ee3d7a-9335-49e9-bc42-d68a9a053263	active
15aa5438-f020-47e4-9ac4-361c3b1e46dc	2018-07-18 14:13:16.318047	2018-07-18 14:13:16.318047	8eaa226397a8ad29d4c00827435349d5	Ansible devel	snapshot_ansible	\N	{}	\N	\N	\N	t	4b3540d6-234f-4435-954b-6bb9cdbf9a5e	active
74574abd-a8f6-4d8a-b5d1-a861c079c5b6	2018-07-18 14:13:16.80297	2018-07-18 14:13:16.80297	344c3316c7240d53b756a5d0258beaba	Ansible 2.4	snapshot_ansible	\N	{}	\N	\N	\N	t	0c38dfa5-6e7a-454d-9902-e02802594076	active
78961d16-8367-4630-b996-01b2fe8b7272	2018-07-18 14:13:17.286568	2018-07-18 14:13:17.286568	223fcb558df3b1e22819e5878eea1d05	RHEL-7.6-20180513.n.0	Compose	\N	{}	\N	\N	\N	t	e73df03e-c57e-48b3-912d-2b61a552fc7e	active
e629f76d-6c6a-42d7-a6d8-636d5320e394	2018-07-18 14:13:17.774717	2018-07-18 14:13:17.774717	a931fa8eef398149660e912d47b7a483	RHEL-8.0-20180503.n.2	Compose	\N	{}	\N	\N	\N	t	1267f96c-f064-41ce-9e9b-6e2e8ae43c4e	active
\.


--
-- Data for Name: components_issues; Type: TABLE DATA; Schema: public; Owner: dci
--

COPY components_issues (component_id, issue_id, user_id) FROM stdin;
\.


--
-- Data for Name: counter; Type: TABLE DATA; Schema: public; Owner: dci
--

COPY counter (created_at, updated_at, name, sequence, etag) FROM stdin;
\.


--
-- Data for Name: feeders; Type: TABLE DATA; Schema: public; Owner: dci
--

COPY feeders (id, created_at, updated_at, etag, name, data, api_secret, team_id, role_id, state) FROM stdin;
\.


--
-- Data for Name: files; Type: TABLE DATA; Schema: public; Owner: dci
--

COPY files (id, created_at, updated_at, name, mime, md5, size, jobstate_id, test_id, team_id, job_id, state, etag) FROM stdin;
836c9ecb-b39f-46d7-94d0-785fbe402671	2018-07-18 14:13:25.129332	2018-07-18 14:13:25.129338	Tempest	application/junit	\N	23785	\N	\N	8a3bd725-8ece-4acc-9199-afe6c51afecc	c12208f2-9532-42dc-922a-794b72e2b0bf	active	67d965363d852ad77d9d1ccb5840c12b
49eaaf4d-3096-48a3-9384-ceff76c04288	2018-07-18 14:13:26.010313	2018-07-18 14:13:26.010322	Tempest	application/junit	\N	23785	\N	\N	8a3bd725-8ece-4acc-9199-afe6c51afecc	024e5e39-b694-4045-9f9f-150c18ddb440	active	58a4656b50e057072a8ee7b457e5ad25
5c67f325-d5c2-486f-b338-5da4261f5b15	2018-07-18 14:13:27.112531	2018-07-18 14:13:27.112549	Rally	application/junit	\N	1440	\N	\N	8a3bd725-8ece-4acc-9199-afe6c51afecc	c12208f2-9532-42dc-922a-794b72e2b0bf	active	3e15251b56d37593a05c938153f55680
77409c2a-fa01-4721-a36c-b7f14bfc8a9a	2018-07-18 14:13:28.316532	2018-07-18 14:13:28.316541	Rally	application/junit	\N	1501	\N	\N	8a3bd725-8ece-4acc-9199-afe6c51afecc	024e5e39-b694-4045-9f9f-150c18ddb440	active	05a4f48d3690d6d1e2c2436109e9fd52
69735816-f432-40eb-bd3c-6143bc7ad551	2018-07-18 14:13:29.235828	2018-07-18 14:13:29.235834	certification.xml.gz	application/x-compressed	\N	1608	\N	\N	8a3bd725-8ece-4acc-9199-afe6c51afecc	024e5e39-b694-4045-9f9f-150c18ddb440	active	dad1a7594a9179e2af37f433c943c160
\.


--
-- Data for Name: issues; Type: TABLE DATA; Schema: public; Owner: dci
--

COPY issues (id, created_at, updated_at, url, tracker) FROM stdin;
\.


--
-- Data for Name: jobs; Type: TABLE DATA; Schema: public; Owner: dci
--

COPY jobs (id, created_at, updated_at, etag, comment, status, rconfiguration_id, topic_id, remoteci_id, team_id, user_agent, client_version, previous_job_id, state, update_previous_job_id) FROM stdin;
d3bb13dc-35fd-4027-adee-3d9c7b999340	2018-07-18 14:13:21.285683	2018-07-18 14:13:22.420476	c55c905e63d9c0611e508cebff367cc1	\N	running	\N	04ee3d7a-9335-49e9-bc42-d68a9a053263	b4536027-a7b1-4b88-9835-5f836c1d92c9	8a3bd725-8ece-4acc-9199-afe6c51afecc	python-requests/2.19.1	\N	\N	active	\N
d218702e-1311-439d-a578-e47780f762ee	2018-07-18 14:13:21.268949	2018-07-18 14:13:23.051987	5b4d6a14ae5a78cd26ace16bda1cf5c7	\N	error	\N	2bc8911f-6bac-4d85-85c7-5654b65d4acb	b4536027-a7b1-4b88-9835-5f836c1d92c9	8a3bd725-8ece-4acc-9199-afe6c51afecc	python-requests/2.19.1	\N	\N	active	\N
024e5e39-b694-4045-9f9f-150c18ddb440	2018-07-18 14:13:21.252043	2018-07-18 14:13:23.603973	3069168a7f2056dda460e6d9c92028aa	\N	failure	\N	9a73cedf-8a9a-4a31-a09a-4c8a6d46e7a1	b4536027-a7b1-4b88-9835-5f836c1d92c9	8a3bd725-8ece-4acc-9199-afe6c51afecc	python-requests/2.19.1	\N	\N	active	\N
c12208f2-9532-42dc-922a-794b72e2b0bf	2018-07-18 14:13:21.224992	2018-07-18 14:13:24.157212	c335f27fcfbedd311ad85c9c46fcd1a4	\N	success	\N	9a73cedf-8a9a-4a31-a09a-4c8a6d46e7a1	b4536027-a7b1-4b88-9835-5f836c1d92c9	8a3bd725-8ece-4acc-9199-afe6c51afecc	python-requests/2.19.1	\N	\N	active	\N
\.


--
-- Data for Name: jobs_components; Type: TABLE DATA; Schema: public; Owner: dci
--

COPY jobs_components (job_id, component_id) FROM stdin;
c12208f2-9532-42dc-922a-794b72e2b0bf	bafbf13f-1173-46f3-978b-5c479c70dc16
024e5e39-b694-4045-9f9f-150c18ddb440	e6068b41-65b3-450a-aa35-7b6c4228d1ca
d218702e-1311-439d-a578-e47780f762ee	da35b887-e390-4790-b131-74307c09cb34
d3bb13dc-35fd-4027-adee-3d9c7b999340	ae1f4397-4a84-4cdb-9c38-c7a9623b591b
\.


--
-- Data for Name: jobs_events; Type: TABLE DATA; Schema: public; Owner: dci
--

COPY jobs_events (id, created_at, job_id, topic_id, status) FROM stdin;
1	2018-07-18 14:13:23.068978	d218702e-1311-439d-a578-e47780f762ee	2bc8911f-6bac-4d85-85c7-5654b65d4acb	error
2	2018-07-18 14:13:23.614448	024e5e39-b694-4045-9f9f-150c18ddb440	9a73cedf-8a9a-4a31-a09a-4c8a6d46e7a1	failure
3	2018-07-18 14:13:24.174137	c12208f2-9532-42dc-922a-794b72e2b0bf	9a73cedf-8a9a-4a31-a09a-4c8a6d46e7a1	success
\.


--
-- Name: jobs_events_id_seq; Type: SEQUENCE SET; Schema: public; Owner: dci
--

SELECT pg_catalog.setval('jobs_events_id_seq', 3, true);


--
-- Data for Name: jobs_issues; Type: TABLE DATA; Schema: public; Owner: dci
--

COPY jobs_issues (job_id, issue_id, user_id) FROM stdin;
\.


--
-- Data for Name: jobstates; Type: TABLE DATA; Schema: public; Owner: dci
--

COPY jobstates (id, created_at, status, comment, job_id, team_id) FROM stdin;
f91365af-95e4-4f46-98d6-d6770f7d0288	2018-07-18 14:13:22.415962	running	\N	d3bb13dc-35fd-4027-adee-3d9c7b999340	8a3bd725-8ece-4acc-9199-afe6c51afecc
38849d01-cc6b-42c3-888a-e6f4ee00bcb0	2018-07-18 14:13:23.047577	error	\N	d218702e-1311-439d-a578-e47780f762ee	8a3bd725-8ece-4acc-9199-afe6c51afecc
22559203-5b9f-4eed-afd7-7098f8bc5ce1	2018-07-18 14:13:23.598757	failure	\N	024e5e39-b694-4045-9f9f-150c18ddb440	8a3bd725-8ece-4acc-9199-afe6c51afecc
3e500746-8ed3-40ba-ae78-292779fa7106	2018-07-18 14:13:24.152177	success	\N	c12208f2-9532-42dc-922a-794b72e2b0bf	8a3bd725-8ece-4acc-9199-afe6c51afecc
\.


--
-- Data for Name: logs; Type: TABLE DATA; Schema: public; Owner: dci
--

COPY logs (id, created_at, user_id, team_id, action) FROM stdin;
da96b545-4be1-4307-9211-3583a5ed7c2f	2018-07-18 14:12:31.196397	4b322f75-9ee8-421e-9197-1603cc26c6d3	9d8f0aa9-3032-4906-94e6-13717f9e4929	create_teams
9ac51a99-44ef-4799-b32f-8d62237d18ad	2018-07-18 14:12:31.687174	4b322f75-9ee8-421e-9197-1603cc26c6d3	9d8f0aa9-3032-4906-94e6-13717f9e4929	create_teams
169bbf3c-fb8b-418c-938a-4e4fb3a9d410	2018-07-18 14:12:32.168434	4b322f75-9ee8-421e-9197-1603cc26c6d3	9d8f0aa9-3032-4906-94e6-13717f9e4929	create_teams
a35f0ce6-952d-4395-a783-246d122ba497	2018-07-18 14:12:32.658981	4b322f75-9ee8-421e-9197-1603cc26c6d3	9d8f0aa9-3032-4906-94e6-13717f9e4929	create_teams
c6476d70-fe01-4a44-b2b9-f7642042d4c0	2018-07-18 14:12:33.146232	4b322f75-9ee8-421e-9197-1603cc26c6d3	9d8f0aa9-3032-4906-94e6-13717f9e4929	create_teams
c4bfd8a9-4d80-4ea8-9759-cfdc817cdd17	2018-07-18 14:12:33.63322	4b322f75-9ee8-421e-9197-1603cc26c6d3	9d8f0aa9-3032-4906-94e6-13717f9e4929	create_teams
da227e7c-4806-4e93-94ed-9c7d2554fcfa	2018-07-18 14:12:34.129578	4b322f75-9ee8-421e-9197-1603cc26c6d3	9d8f0aa9-3032-4906-94e6-13717f9e4929	create_teams
93690beb-47fa-4d1e-b44e-0968d78788d9	2018-07-18 14:12:45.21011	4b322f75-9ee8-421e-9197-1603cc26c6d3	9d8f0aa9-3032-4906-94e6-13717f9e4929	create_product
4b8e3863-5900-4cc5-ae6e-a76e6ae3f431	2018-07-18 14:12:45.670417	4b322f75-9ee8-421e-9197-1603cc26c6d3	9d8f0aa9-3032-4906-94e6-13717f9e4929	create_product
28d71ca6-9180-43f8-be08-57108b871187	2018-07-18 14:12:46.147887	4b322f75-9ee8-421e-9197-1603cc26c6d3	9d8f0aa9-3032-4906-94e6-13717f9e4929	create_product
\.


--
-- Data for Name: metas; Type: TABLE DATA; Schema: public; Owner: dci
--

COPY metas (id, created_at, updated_at, etag, name, value, job_id) FROM stdin;
\.


--
-- Data for Name: permissions; Type: TABLE DATA; Schema: public; Owner: dci
--

COPY permissions (id, created_at, updated_at, etag, name, label, description, state) FROM stdin;
\.


--
-- Data for Name: products; Type: TABLE DATA; Schema: public; Owner: dci
--

COPY products (id, created_at, updated_at, etag, name, label, description, state, team_id) FROM stdin;
38ce41eb-557a-46a2-9204-531b3dcac402	2018-07-18 14:12:45.212998	2018-07-18 14:12:45.212998	280934809a55eb201cc53fe04306f681	OpenStack	OPENSTACK	description for OpenStack	active	ba30a049-ac32-4ec4-9ebd-40d35d8ae4cd
c22ecabf-f720-4e86-a380-07996743f770	2018-07-18 14:12:45.674153	2018-07-18 14:12:45.674153	38d5ef33f8956a58e89aa846d4ca8348	Ansible	ANSIBLE	description for Ansible	active	c8185d8a-0f5b-4d57-ae8e-43bcbde43c27
1d740465-84ad-48c4-a90f-c933c4c6be56	2018-07-18 14:12:46.151016	2018-07-18 14:12:46.151016	496285aad130b667eee4f6d50fbb8299	RHEL	RHEL	description for RHEL	active	1ae8125c-732b-41ba-843c-e3c0fea8e868
\.


--
-- Data for Name: rconfigurations; Type: TABLE DATA; Schema: public; Owner: dci
--

COPY rconfigurations (id, created_at, updated_at, etag, state, topic_id, name, component_types, data) FROM stdin;
\.


--
-- Data for Name: remoteci_tests; Type: TABLE DATA; Schema: public; Owner: dci
--

COPY remoteci_tests (remoteci_id, test_id) FROM stdin;
\.


--
-- Data for Name: remotecis; Type: TABLE DATA; Schema: public; Owner: dci
--

COPY remotecis (id, created_at, updated_at, etag, name, data, api_secret, team_id, role_id, public, state, cert_fp) FROM stdin;
675e1347-6d4f-495f-b274-a49a98cccc9e	2018-07-18 14:13:18.261795	2018-07-18 14:13:18.261795	216e54dabb08cf433be362dce5733bf1	Remoteci Cisco	{}	eDYgXhhbs8YrH5K6hrFYc2i6Gb1MddAGeP11RRk5p3fkbLLfoMDWibOms1TTzuUI	2132fcbc-15fa-45f0-b16f-77ce3a375fc6	33a68f55-50db-4d09-aa43-dd14e53739b1	f	active	\N
f361b0a4-db28-4ed7-9db6-6d961984d286	2018-07-18 14:13:18.744904	2018-07-18 14:13:18.744904	134209977139458d77e8768b599677ee	Remoteci HP	{}	xmdm6uB9dclvQ0zdfI7MbECmlWl8NfyDBIAWcJKv78d7zy8jocaGgV9GsCLfprSQ	01ed0891-d32d-47cd-bbdd-31c09201013c	33a68f55-50db-4d09-aa43-dd14e53739b1	f	active	\N
b4536027-a7b1-4b88-9835-5f836c1d92c9	2018-07-18 14:13:19.234271	2018-07-18 14:13:19.234271	30d9a42fec2629a79bbfb0eb00167fa7	Remoteci Dell	{}	o1DiCPPusIEo5ViQ653Z2ffkcStO6wfmVExeK4fjhBkN9v8UypXYKKlU3Oyspvrf	8a3bd725-8ece-4acc-9199-afe6c51afecc	33a68f55-50db-4d09-aa43-dd14e53739b1	f	active	\N
db7eda6d-b342-4181-8d10-a3fbf46f6ebd	2018-07-18 14:13:19.724724	2018-07-18 14:13:19.724724	f9526151fd81724cb91969bc96443cf5	Remoteci Ansible	{}	vjfod3nUmjkOBAYA69W0hPjtMNo26ydBBtYVbpHandHk2MiRtwXLcxk99gfY4aBk	c8185d8a-0f5b-4d57-ae8e-43bcbde43c27	33a68f55-50db-4d09-aa43-dd14e53739b1	f	active	\N
4a914438-cc9d-45c6-8ff9-c9d83bba3d88	2018-07-18 14:13:20.213625	2018-07-18 14:13:20.213625	1a93e15209c786a9d4ee4918be9495bc	Remoteci RHEL	{}	wRGsyxMkcO9gI0RfQhvEBAmicAGAHde7r3lPAOjEDtEvuwH8tE0yYfOVpEMHB3sL	1ae8125c-732b-41ba-843c-e3c0fea8e868	33a68f55-50db-4d09-aa43-dd14e53739b1	f	active	\N
e7035dac-7615-49d9-a7fd-e9136ccde0f1	2018-07-18 14:13:20.715293	2018-07-18 14:13:20.715293	c39e8da85e8957fce44e6a8c3837cf21	Remoteci Veritas	{}	49RA3HWyCpufGAWSPOI4fNGTStCJxAIzsctgp0bxZdh9Sav47sio58La9ZUJTYfL	fbda671c-003b-460a-8d14-ebff1aeecb45	33a68f55-50db-4d09-aa43-dd14e53739b1	f	active	\N
2d5c2243-e8d4-40be-b38a-28097b94f497	2018-07-18 14:13:21.209583	2018-07-18 14:13:21.209583	06690cc8b4d74f4f25047a97005d2838	Remoteci OpenStack	{}	YHhedX52NAaBNzzL90u2tqeS4W0CN2yV73JipHfbrYn3IVcRyUFdophrRuPPAuq3	ba30a049-ac32-4ec4-9ebd-40d35d8ae4cd	33a68f55-50db-4d09-aa43-dd14e53739b1	f	active	\N
\.


--
-- Data for Name: remotecis_rconfigurations; Type: TABLE DATA; Schema: public; Owner: dci
--

COPY remotecis_rconfigurations (remoteci_id, rconfiguration_id) FROM stdin;
\.


--
-- Data for Name: roles; Type: TABLE DATA; Schema: public; Owner: dci
--

COPY roles (id, created_at, updated_at, etag, name, label, description, state) FROM stdin;
1e4a0b6b-58d5-4230-8c1a-6212f82ae3fb	2018-07-18 14:12:05.948644	2018-07-18 14:12:05.948653	e4ccb162c7b81242a31b1be207d30c1a	Product Owner	PRODUCT_OWNER	Product Owner	active
5d02f2e9-5007-485f-9d47-c2c64388231d	2018-07-18 14:12:05.950518	2018-07-18 14:12:05.950525	4ae6149d130bc943d91a9e9d60909cd2	Admin	ADMIN	Admin of a team	active
d825ecec-f909-47e7-a6e7-1dc78fe794c4	2018-07-18 14:12:05.952639	2018-07-18 14:12:05.952646	974ae413248c6ae2422996036c361752	User	USER	Regular User	active
370461e1-40c7-4c3f-ab2f-7a93c4056b85	2018-07-18 14:12:05.766863	2018-07-18 14:12:05.954525	87524a1fdd036c1e13e5a3d5eb06e88f	Read only user	READ_ONLY_USER	User with RO access	active
33a68f55-50db-4d09-aa43-dd14e53739b1	2018-07-18 14:12:05.956387	2018-07-18 14:12:05.956394	5a9e357bab6b99602fd17e019bbbae0b	RemoteCI	REMOTECI	A RemoteCI	active
1ab33d3c-a367-437f-aceb-ecd36d258e04	2018-07-18 14:12:05.958146	2018-07-18 14:12:05.958152	8de447bae7839fd411c65959c22cb626	Feeder	FEEDER	A Feeder	active
31562ebf-d8bc-48f6-bea8-a1719ead8d48	2018-07-18 14:12:05.961371	2018-07-18 14:12:05.961378	025704953f29e746145a2cda43a65cde	Super Admin	SUPER_ADMIN	Admin of the platform	active
\.


--
-- Data for Name: roles_permissions; Type: TABLE DATA; Schema: public; Owner: dci
--

COPY roles_permissions (role_id, permission_id) FROM stdin;
\.


--
-- Data for Name: teams; Type: TABLE DATA; Schema: public; Owner: dci
--

COPY teams (id, created_at, updated_at, etag, name, country, state, external, parent_id) FROM stdin;
9d8f0aa9-3032-4906-94e6-13717f9e4929	2018-07-18 14:12:05.945808	2018-07-18 14:12:05.945817	638eabc13d03bd00e9a1fe233aad75ed	admin	\N	active	t	\N
ba30a049-ac32-4ec4-9ebd-40d35d8ae4cd	2018-07-18 14:12:31.200158	2018-07-18 14:12:31.200158	b8caf759ec0ef152d2f2f53040916429	OpenStack	\N	active	t	9d8f0aa9-3032-4906-94e6-13717f9e4929
c8185d8a-0f5b-4d57-ae8e-43bcbde43c27	2018-07-18 14:12:31.690537	2018-07-18 14:12:31.690537	74e0c70b499405f9cc54efa4bd2e0cc1	Ansible	\N	active	t	9d8f0aa9-3032-4906-94e6-13717f9e4929
1ae8125c-732b-41ba-843c-e3c0fea8e868	2018-07-18 14:12:32.171308	2018-07-18 14:12:32.171308	dabb18aa5f3e5dc9a811db99fc5b2a7c	RHEL	\N	active	t	9d8f0aa9-3032-4906-94e6-13717f9e4929
8a3bd725-8ece-4acc-9199-afe6c51afecc	2018-07-18 14:12:32.661871	2018-07-18 14:12:32.661871	b9db8f08a4cfe19f3a237421dc25f6e1	Dell	\N	active	t	ba30a049-ac32-4ec4-9ebd-40d35d8ae4cd
01ed0891-d32d-47cd-bbdd-31c09201013c	2018-07-18 14:12:33.149556	2018-07-18 14:12:33.149556	b4ab8642590dae5ce659aabebbb68169	HP	\N	active	t	ba30a049-ac32-4ec4-9ebd-40d35d8ae4cd
2132fcbc-15fa-45f0-b16f-77ce3a375fc6	2018-07-18 14:12:33.636982	2018-07-18 14:12:33.636982	5627ab2503c0150a75e1be6bd155a0bf	Cisco	\N	active	t	c8185d8a-0f5b-4d57-ae8e-43bcbde43c27
fbda671c-003b-460a-8d14-ebff1aeecb45	2018-07-18 14:12:34.132669	2018-07-18 14:12:34.132669	f827c3cfa49cf775c92f23a420819c84	Veritas	\N	active	t	1ae8125c-732b-41ba-843c-e3c0fea8e868
\.


--
-- Data for Name: tests; Type: TABLE DATA; Schema: public; Owner: dci
--

COPY tests (id, created_at, updated_at, name, data, team_id, state, etag) FROM stdin;
\.


--
-- Data for Name: tests_results; Type: TABLE DATA; Schema: public; Owner: dci
--

COPY tests_results (id, created_at, updated_at, name, total, success, skips, failures, errors, "time", job_id, file_id, tests_cases, regressions) FROM stdin;
f254c91f-08bd-4ebf-82ec-85ceb0fede59	2018-07-18 14:13:25.129332	2018-07-18 14:13:25.142404	Tempest	130	117	13	0	0	1308365	c12208f2-9532-42dc-922a-794b72e2b0bf	836c9ecb-b39f-46d7-94d0-785fbe402671	[{"successfix": false, "name": "test_get_flavor[id-fdfdc380-7482-4e7e-99f4-3dbdbdf4b631,smoke]", "value": "", "classname": "tempest.api.compute.flavors.test_flavors.FlavorsV2TestJSON", "time": 0.53, "action": "passed", "message": "", "type": "", "regression": false}, {"successfix": false, "name": "test_list_flavors[id-9895db89-9866-408c-a6a4-15af00ce94da,smoke]", "value": "", "classname": "tempest.api.compute.flavors.test_flavors.FlavorsV2TestJSON", "time": 0.167, "action": "passed", "message": "", "type": "", "regression": false}, {"successfix": false, "name": "test_default_domain_exists[id-fd693ced-a1d7-4687-94ed-3b81620d3991,smoke]", "value": "", "classname": "tempest.api.identity.admin.v3.test_domains.DefaultDomainTestJSON", "time": 0.228, "action": "passed", "message": "", "type": "", "regression": false}, {"successfix": false, "name": "test_security_group_rules_create[id-14deeed5-7828-4262-b1d9-f92c1821f48a,network,smoke]", "value": "", "classname": "tempest.api.compute.security_groups.test_security_group_rules.SecurityGroupRulesTestJSON", "time": 4.78, "action": "passed", "message": "", "type": "", "regression": false}, {"successfix": false, "name": "test_create_update_get_service[id-b5c88893-5c7e-4431-ae0b-012001c2d546,smoke]", "value": "", "classname": "tempest.api.identity.admin.v3.test_services.ServicesTestJSON", "time": 1.302, "action": "passed", "message": "", "type": "", "regression": false}, {"successfix": false, "name": "test_security_group_rules_list[id-bbf6f4ee-adaa-42a9-b811-4b0ec034ea58,network,smoke]", "value": "", "classname": "tempest.api.compute.security_groups.test_security_group_rules.SecurityGroupRulesTestJSON", "time": 6.598, "action": "passed", "message": "", "type": "", "regression": false}, {"successfix": false, "name": "test_security_groups_create_list_delete[id-cbada7f0-7ed0-47fe-8177-dd937d1894f8,network,smoke]", "value": "", "classname": "tempest.api.compute.security_groups.test_security_groups.SecurityGroupsTestJSON", "time": 13.727, "action": "passed", "message": "", "type": "", "regression": false}, {"successfix": false, "name": "test_get_trusts_all[id-61695af0-bec6-4bda-bf9c-ef1ba914819e,smoke]", "value": "", "classname": "tempest.api.identity.admin.v3.test_trusts.TrustsV3TestJSON", "time": 6.427, "action": "passed", "message": "", "type": "", "regression": false}, {"successfix": false, "name": "test_api_media_types[id-71478a40-38bb-42fe-b3c9-34abd8899d58,smoke]", "value": "", "classname": "tempest.api.identity.v3.test_api_discovery.TestApiDiscovery", "time": 0.228, "action": "passed", "message": "", "type": "", "regression": false}, {"successfix": false, "name": "test_api_version_resources[id-e065df73-b03f-4ce1-80d5-06a4ba8bdf4b,smoke]", "value": "", "classname": "tempest.api.identity.v3.test_api_discovery.TestApiDiscovery", "time": 0.285, "action": "passed", "message": "", "type": "", "regression": false}, {"successfix": false, "name": "test_api_version_statuses[id-269f7038-9f70-4012-95ac-a6cbbda614ce,smoke]", "value": "", "classname": "tempest.api.identity.v3.test_api_discovery.TestApiDiscovery", "time": 0.289, "action": "passed", "message": "", "type": "", "regression": false}, {"successfix": false, "name": "test_list_servers[id-433c6a8f-5e66-4761-9ade-abeb313876c6,smoke]", "value": "", "classname": "tempest.api.compute.servers.test_create_server.ServersTestManualDisk", "time": 0.349, "action": "passed", "message": "", "type": "", "regression": false}, {"successfix": false, "name": "test_verify_server_details[id-1b1bc049-9df9-4ced-9ed0-7adacf27471a,smoke]", "value": "", "classname": "tempest.api.compute.servers.test_create_server.ServersTestManualDisk", "time": 0.001, "action": "passed", "message": "", "type": "", "regression": false}, {"successfix": false, "name": "test_list_show_extensions[id-cb3968d2-1819-4b4a-98b5-850bbdb9e14b,smoke]", "value": "", "classname": "tempest.api.network.test_extensions.ExtensionsTestJSON", "time": 7.746, "action": "passed", "message": "", "type": "", "regression": false}, {"successfix": false, "name": "test_add_remove_fixed_ip[id-dc0ee336-dadc-44c1-a0bf-a65093f6644f,network,smoke]", "value": "", "classname": "tempest.api.compute.servers.test_attach_interfaces.AttachInterfacesTestJSON", "time": 34.806, "action": "passed", "message": "", "type": "", "regression": false}, {"successfix": false, "name": "test_list_servers[id-8e40ef78-2f4d-4361-9ff8-b485ec760466,smoke]", "value": "", "classname": "tempest.api.compute.servers.test_create_server.ServersTestJSON", "time": 0.33, "action": "passed", "message": "", "type": "", "regression": false}, {"successfix": false, "name": "test_verify_server_details[id-4bda6d9b-5528-4622-b240-53815132a996,smoke]", "value": "", "classname": "tempest.api.compute.servers.test_create_server.ServersTestJSON", "time": 0.001, "action": "passed", "message": "", "type": "", "regression": false}, {"successfix": false, "name": "test_create_user[id-7c2c6ff9-c611-49fa-80cc-21ac158cc6cc,smoke]", "value": "", "classname": "tempest.api.identity.admin.v2.test_users.UsersTestJSON", "time": 2.243, "action": "passed", "message": "", "type": "", "regression": false}, {"successfix": false, "name": "test_credentials_create_get_update_delete[id-a1a79747-66b3-4eaf-a9db-9dfa7697536f,smoke]", "value": "", "classname": "tempest.api.identity.admin.v3.test_credentials.CredentialsTestJSON", "time": 2.711, "action": "passed", "message": "", "type": "", "regression": false}, {"successfix": false, "name": "test_create_floating_ip_specifying_a_fixed_ip_address[id-bd3a6a9f-7311-4d18-ad4c-e8ded08539a9,smoke]", "value": "", "classname": "tempest.api.network.test_floating_ips.FloatingIPTestJSON", "time": 8.971, "action": "passed", "message": "", "type": "", "regression": false}, {"successfix": false, "name": "test_create_list_show_update_delete_floating_ip[id-26b46236-67bf-4408-85fc-b4c725b76be6,smoke]", "value": "", "classname": "tempest.api.network.test_floating_ips.FloatingIPTestJSON", "time": 8.629, "action": "passed", "message": "", "type": "", "regression": false}, {"successfix": false, "name": "test_create_update_delete_domain[id-fe4b71ea-30bd-46a4-92a0-4bd073035da0,smoke]", "value": "", "classname": "tempest.api.identity.admin.v3.test_domains.DomainsTestJSON", "time": 1.835, "action": "passed", "message": "", "type": "", "regression": false}, {"successfix": false, "name": "test_list_services[id-ecf0d25c-5d5b-4f61-bfda-f1fe34e73e69,smoke]", "value": "", "classname": "tempest.api.identity.admin.v2.test_services.ServicesTestJSON", "time": 2.637, "action": "passed", "message": "", "type": "", "regression": false}, {"successfix": false, "name": "test_update_endpoint[id-b734ae9b-12f5-46cf-a3c0-5aacefd24c7d,smoke]", "value": "", "classname": "tempest.api.identity.admin.v3.test_endpoints.EndPointsTestJSON", "time": 1.112, "action": "passed", "message": "", "type": "", "regression": false}, {"successfix": false, "name": "test_role_create_update_show_list[id-31307a8d-1b1b-4bc7-9b51-3ab0fc1b11b7,smoke]", "value": "", "classname": "tempest.api.identity.admin.v3.test_roles.RolesV3TestJSON", "time": 1.299, "action": "passed", "message": "", "type": "", "regression": false}, {"successfix": false, "name": "test_group_users_add_list_delete[id-630bcaa7-51b5-42ca-97d5-dea08605dbbf,smoke]", "value": "", "classname": "tempest.api.identity.admin.v3.test_groups.GroupsV3TestJSON", "time": 8.005, "action": "passed", "message": "", "type": "", "regression": false}, {"successfix": false, "name": "test_reboot_server_hard[id-8767976e-986f-4e19-809c-577a6c83d760,smoke]", "value": "", "classname": "tempest.api.compute.servers.test_server_actions.ServerActionsTestJSON", "time": 8.141, "action": "passed", "message": "", "type": "", "regression": false}, {"successfix": false, "name": "test_api_media_types[id-2fc6822e-b5a8-42ed-967b-11d86e881ce3,smoke]", "value": "", "classname": "tempest.api.identity.v2.test_api_discovery.TestApiDiscovery", "time": 0.272, "action": "passed", "message": "", "type": "", "regression": false}, {"successfix": false, "name": "test_api_version_resources[id-f149a4b9-57fc-4fcd-afaf-714ad0c4b207,smoke]", "value": "", "classname": "tempest.api.identity.v2.test_api_discovery.TestApiDiscovery", "time": 0.214, "action": "passed", "message": "", "type": "", "regression": false}, {"successfix": false, "name": "test_api_version_statuses[id-32fc7d57-3d2e-4d6c-aa30-e7dfc6fdc6f3,smoke]", "value": "", "classname": "tempest.api.identity.v2.test_api_discovery.TestApiDiscovery", "time": 0.415, "action": "passed", "message": "", "type": "", "regression": false}, {"successfix": false, "name": "test_create_port_in_allowed_allocation_pools[id-95a7d063-6529-49aa-9cfb-36630ed9cea7,smoke]", "value": "", "classname": "tempest.api.network.test_ports.PortsIpV6TestJSON", "time": 16.342, "action": "passed", "message": "", "type": "", "regression": false}, {"successfix": false, "name": "test_delete_image[id-4da8b06d-67e1-444e-a1ad-674c5c33db36,smoke]", "value": "", "classname": "tempest.api.image.v2.test_images.BasicOperationsImagesTest", "time": 2.207, "action": "passed", "message": "", "type": "", "regression": false}, {"successfix": false, "name": "test_register_upload_get_image_file[id-ea3084e4-bde9-4be0-90ec-46b478db894c,smoke]", "value": "", "classname": "tempest.api.image.v2.test_images.BasicOperationsImagesTest", "time": 3.372, "action": "passed", "message": "", "type": "", "regression": false}, {"successfix": false, "name": "test_create_region_with_specific_id[id-2216947c-2075-42f2-879c-341dd2eaee42,smoke]", "value": "", "classname": "tempest.api.identity.admin.v3.test_regions.RegionsTestJSON", "time": 0.735, "action": "passed", "message": "", "type": "", "regression": false}, {"successfix": false, "name": "test_update_image[id-91237988-3948-4e81-a43f-e9e34383e6c7,smoke]", "value": "", "classname": "tempest.api.image.v2.test_images.BasicOperationsImagesTest", "time": 3.69, "action": "passed", "message": "", "type": "", "regression": false}, {"successfix": false, "name": "setUpClass (tempest.api.object_storage.test_account_quotas.AccountQuotasTest)", "value": "AccountQuotasTest skipped as swift is not available", "classname": "", "time": 0.0, "action": "skipped", "message": "", "type": "", "regression": false}, {"successfix": false, "name": "test_create_port_with_no_securitygroups[id-0d9894f5-97d7-4ca4-9342-d5571d3a9b21,smoke]", "value": "", "classname": "tempest.api.network.test_ports.PortsIpV6TestJSON", "time": 16.162, "action": "passed", "message": "", "type": "", "regression": false}, {"successfix": false, "name": "test_create_update_delete_port[id-a1229df6-4e4c-485d-a72b-2b0a8af05fdd,smoke]", "value": "", "classname": "tempest.api.network.test_ports.PortsIpV6TestJSON", "time": 3.367, "action": "passed", "message": "", "type": "", "regression": false}, {"successfix": false, "name": "test_list_ports[id-21666509-180b-4171-b567-6c54f38fc3d0,smoke]", "value": "", "classname": "tempest.api.network.test_ports.PortsIpV6TestJSON", "time": 0.198, "action": "passed", "message": "", "type": "", "regression": false}, {"successfix": false, "name": "test_show_port[id-1da7a454-f57a-4e67-8f9d-24bc7d280873,smoke]", "value": "", "classname": "tempest.api.network.test_ports.PortsIpV6TestJSON", "time": 0.151, "action": "passed", "message": "", "type": "", "regression": false}, {"successfix": false, "name": "test_bulk_create_delete_network[id-94720f48-34f9-403a-b87d-5cc1fcd132d7,smoke]", "value": "", "classname": "tempest.api.network.test_networks.BulkNetworkOpsIpV6Test", "time": 5.536, "action": "passed", "message": "", "type": "", "regression": false}, {"successfix": false, "name": "test_bulk_create_delete_port[id-bd93e7f0-247d-4192-aa1c-4bb81d57469d,smoke]", "value": "", "classname": "tempest.api.network.test_networks.BulkNetworkOpsIpV6Test", "time": 7.102, "action": "passed", "message": "", "type": "", "regression": false}, {"successfix": false, "name": "test_attach_detach_volume_to_instance[compute,id-fff42874-7db5-4487-a8e1-ddda5fb5288d,smoke]", "value": "", "classname": "tempest.api.volume.test_volumes_actions.VolumesV1ActionsTest", "time": 20.023, "action": "passed", "message": "", "type": "", "regression": false}, {"successfix": false, "name": "test_bulk_create_delete_subnet[id-7549d64e-4938-489d-96ba-016451660556,smoke]", "value": "", "classname": "tempest.api.network.test_networks.BulkNetworkOpsIpV6Test", "time": 12.11, "action": "passed", "message": "", "type": "", "regression": false}, {"successfix": false, "name": "test_list_server_addresses[id-b501abea-63da-4741-b62f-10426d2bd5c8,network,smoke]", "value": "", "classname": "tempest.api.compute.servers.test_server_addresses.ServerAddressesTestJSON", "time": 0.268, "action": "passed", "message": "", "type": "", "regression": false}, {"successfix": false, "name": "test_list_server_addresses_by_network[id-8dd9d0d9-a1f9-4207-bf01-33fbd9d0adfd,network,smoke]", "value": "", "classname": "tempest.api.compute.servers.test_server_addresses.ServerAddressesTestJSON", "time": 0.409, "action": "passed", "message": "", "type": "", "regression": false}, {"successfix": false, "name": "test_create_update_delete_policy[id-2fdb5e9b-2226-4b83-9576-7037943846e1,smoke]", "value": "", "classname": "tempest.api.identity.admin.v3.test_policies.PoliciesTestJSON", "time": 0.819, "action": "passed", "message": "", "type": "", "regression": false}, {"successfix": false, "name": "test_bulk_create_delete_network[id-dd90abb7-1a4e-48e3-a167-f277ec11108f,smoke]", "value": "", "classname": "tempest.api.network.test_networks.BulkNetworkOpsTest", "time": 5.8, "action": "passed", "message": "", "type": "", "regression": false}, {"successfix": false, "name": "test_attach_detach_volume_to_instance[compute,id-fff42874-7db5-4487-a8e1-ddda5fb5288d,smoke]", "value": "", "classname": "tempest.api.volume.test_volumes_actions.VolumesV2ActionsTest", "time": 18.366, "action": "passed", "message": "", "type": "", "regression": false}, {"successfix": false, "name": "test_bulk_create_delete_port[id-eeb7533f-fd53-411a-9289-fcb4258b7f45,smoke]", "value": "", "classname": "tempest.api.network.test_networks.BulkNetworkOpsTest", "time": 7.748, "action": "passed", "message": "", "type": "", "regression": false}, {"successfix": false, "name": "test_add_multiple_router_interfaces[id-142463a1-ed6a-4b9d-abe4-78569731c6f9,smoke]", "value": "", "classname": "tempest.api.network.test_routers.RoutersTest", "time": 42.241, "action": "passed", "message": "", "type": "", "regression": false}, {"successfix": false, "name": "test_bulk_create_delete_subnet[id-09aaf80c-4cde-43f0-80bb-cc7486133057,smoke]", "value": "", "classname": "tempest.api.network.test_networks.BulkNetworkOpsTest", "time": 5.665, "action": "passed", "message": "", "type": "", "regression": false}, {"successfix": false, "name": "test_volume_list[id-44f7b3e0-6373-4427-949f-68ab32d6e184,smoke]", "value": "", "classname": "tempest.api.volume.test_volumes_list.VolumesV1ListTestJSON", "time": 0.092, "action": "passed", "message": "", "type": "", "regression": false}, {"successfix": false, "name": "setUpClass (mistral_tempest_tests.tests.api.v2.test_actions.ActionTestsV2)", "value": "Mistral support is required.", "classname": "", "time": 0.0, "action": "skipped", "message": "", "type": "", "regression": false}, {"successfix": false, "name": "test_create_update_delete_network_subnet[id-983e1633-e577-415b-851d-635eb5025ec9,smoke]", "value": "", "classname": "tempest.api.network.test_networks.NetworksIpV6Test", "time": 15.892, "action": "passed", "message": "", "type": "", "regression": false}, {"successfix": false, "name": "test_external_network_visibility[id-4334ba1b-de5c-41e7-8511-0d0eeb5c285b,smoke]", "value": "", "classname": "tempest.api.network.test_networks.NetworksIpV6Test", "time": 0.797, "action": "passed", "message": "", "type": "", "regression": false}, {"successfix": false, "name": "test_list_networks[id-593e96ef-4d7e-47a3-8d5e-9cb6c1504acb,smoke]", "value": "", "classname": "tempest.api.network.test_networks.NetworksIpV6Test", "time": 0.832, "action": "passed", "message": "", "type": "", "regression": false}, {"successfix": false, "name": "test_list_subnets[id-4f3c4a81-2c76-4c27-8b4a-ec3c4ed80107,smoke]", "value": "", "classname": "tempest.api.network.test_networks.NetworksIpV6Test", "time": 0.6, "action": "passed", "message": "", "type": "", "regression": false}, {"successfix": false, "name": "test_show_network[id-4f278dab-1e1f-4126-8112-5c8d115ad62f,smoke]", "value": "", "classname": "tempest.api.network.test_networks.NetworksIpV6Test", "time": 0.283, "action": "passed", "message": "", "type": "", "regression": false}, {"successfix": false, "name": "test_show_subnet[id-a24dbec1-c9a5-4d36-a524-20033184f620,smoke]", "value": "", "classname": "tempest.api.network.test_networks.NetworksIpV6Test", "time": 0.229, "action": "passed", "message": "", "type": "", "regression": false}, {"successfix": false, "name": "test_create_rbac_policy_with_target_tenant_none[id-ff13925f-b235-413e-8ef3-1325d463add9,smoke]", "value": "", "classname": "neutron.tests.tempest.api.admin.test_shared_network_extension.RBACSharedNetworksTest", "time": 7.025, "action": "passed", "message": "", "type": "", "regression": false}, {"successfix": false, "name": "test_add_remove_router_interface_with_port_id[id-02693de1-7330-4857-9c77-b25c33607b35,smoke]", "value": "", "classname": "tempest.api.network.test_routers.RoutersTest", "time": 29.507, "action": "passed", "message": "", "type": "", "regression": false}, {"successfix": false, "name": "test_create_rbac_policy_with_target_tenant_too_long_id[id-693b66cd-3ada-41ac-886a-6cfee12f1b7b,smoke]", "value": "", "classname": "neutron.tests.tempest.api.admin.test_shared_network_extension.RBACSharedNetworksTest", "time": 5.082, "action": "passed", "message": "", "type": "", "regression": false}, {"successfix": false, "name": "test_network_only_visible_to_policy_target[id-7c621ce5-de0d-4274-8d89-02be7bd9e225,smoke]", "value": "", "classname": "neutron.tests.tempest.api.admin.test_shared_network_extension.RBACSharedNetworksTest", "time": 12.603, "action": "passed", "message": "", "type": "", "regression": false}, {"successfix": false, "name": "test_create_update_delete_network_subnet[id-b672a174-6ed4-4d0e-a0cd-404dda544c09,smoke]", "value": "", "classname": "tempest.api.network.test_networks.NetworksTest", "time": 9.87, "action": "passed", "message": "", "type": "", "regression": false}, {"successfix": false, "name": "test_external_network_visibility[id-403ab82d-bcdf-45e2-bddb-655b3a00a1f5,smoke]", "value": "", "classname": "tempest.api.network.test_networks.NetworksTest", "time": 0.803, "action": "passed", "message": "", "type": "", "regression": false}, {"successfix": false, "name": "test_list_networks[id-5daa85e7-5edf-4deb-992c-e0107fd19b2b,smoke]", "value": "", "classname": "tempest.api.network.test_networks.NetworksTest", "time": 0.342, "action": "passed", "message": "", "type": "", "regression": false}, {"successfix": false, "name": "test_list_subnets[id-f2c03a3a-b43b-4829-8251-6c693448c8c2,smoke]", "value": "", "classname": "tempest.api.network.test_networks.NetworksTest", "time": 0.203, "action": "passed", "message": "", "type": "", "regression": false}, {"successfix": false, "name": "test_show_network[id-9b922b8a-ef9d-4a26-bbbd-7c37ecfc7f21,smoke]", "value": "", "classname": "tempest.api.network.test_networks.NetworksTest", "time": 0.293, "action": "passed", "message": "", "type": "", "regression": false}, {"successfix": false, "name": "test_show_subnet[id-2207e5f2-2de1-46c5-954d-a2295e75ca2b,smoke]", "value": "", "classname": "tempest.api.network.test_networks.NetworksTest", "time": 0.436, "action": "passed", "message": "", "type": "", "regression": false}, {"successfix": false, "name": "test_add_remove_router_interface_with_subnet_id[id-9bd032b6-4292-4e4d-ab2e-0113fc638bfa,smoke]", "value": "", "classname": "tempest.api.network.test_routers.RoutersTest", "time": 29.382, "action": "passed", "message": "", "type": "", "regression": false}, {"successfix": false, "name": "test_add_multiple_router_interfaces[id-828bca65-e8e4-4e55-88a5-ce15333ee461,smoke]", "value": "", "classname": "tempest.api.network.test_routers.RoutersIpV6Test", "time": 44.825, "action": "passed", "message": "", "type": "", "regression": false}, {"successfix": false, "name": "test_filter_network_tags[id-574d99a6-0432-4379-a3d3-238e55547eb4,smoke]", "value": "", "classname": "neutron.tests.tempest.api.test_tag.TagFilterNetworkTestJSON", "time": 3.084, "action": "passed", "message": "", "type": "", "regression": false}, {"successfix": false, "name": "test_create_show_list_update_delete_router[id-a19c4c3c-490d-41fb-9ea6-a37c04b6db89,smoke]", "value": "", "classname": "tempest.api.network.test_routers.RoutersTest", "time": 21.941, "action": "passed", "message": "", "type": "", "regression": false}, {"successfix": false, "name": "test_create_port_in_allowed_allocation_pools[id-c6c55e41-f6e5-4cc7-b2af-9b7d863a4ac7,smoke]", "value": "", "classname": "tempest.api.network.test_ports.PortsTestJSON", "time": 16.602, "action": "passed", "message": "", "type": "", "regression": false}, {"successfix": false, "name": "test_add_remove_router_interface_with_port_id[id-ac58ceb1-0cb8-40ad-8a1d-3be5636dcd41,smoke]", "value": "", "classname": "tempest.api.network.test_routers.RoutersIpV6Test", "time": 28.079, "action": "passed", "message": "", "type": "", "regression": false}, {"successfix": false, "name": "test_create_port_with_no_securitygroups[id-8ca6d376-ceff-423b-9021-38aa76bd51c5,smoke]", "value": "", "classname": "tempest.api.network.test_ports.PortsTestJSON", "time": 22.243, "action": "passed", "message": "", "type": "", "regression": false}, {"successfix": false, "name": "test_create_update_delete_port[id-153838d9-8c65-439a-91a3-ff40e5b182ac,smoke]", "value": "", "classname": "tempest.api.network.test_ports.PortsTestJSON", "time": 4.372, "action": "passed", "message": "", "type": "", "regression": false}, {"successfix": false, "name": "test_list_ports[id-124ef885-6e91-482f-9789-9315db2e13ce,smoke]", "value": "", "classname": "tempest.api.network.test_ports.PortsTestJSON", "time": 0.18, "action": "passed", "message": "", "type": "", "regression": false}, {"successfix": false, "name": "test_filter_subnet_tags[id-06dcba8d-6ce5-4cb1-b733-d5bbbd94f019,smoke]", "value": "", "classname": "neutron.tests.tempest.api.test_tag.TagFilterSubnetTestJSON", "time": 2.984, "action": "passed", "message": "", "type": "", "regression": false}, {"successfix": false, "name": "test_show_port[id-5e82e447-cca1-4794-9f2b-14465f323645,smoke]", "value": "", "classname": "tempest.api.network.test_ports.PortsTestJSON", "time": 0.239, "action": "passed", "message": "", "type": "", "regression": false}, {"successfix": false, "name": "setUpClass (tempest.api.object_storage.test_container_services.ContainerTest)", "value": "ContainerTest skipped as swift is not available", "classname": "", "time": 0.0, "action": "skipped", "message": "", "type": "", "regression": false}, {"successfix": false, "name": "setUpClass (tempest.api.object_storage.test_object_services.ObjectTest)", "value": "ObjectTest skipped as swift is not available", "classname": "", "time": 0.0, "action": "skipped", "message": "", "type": "", "regression": false}, {"successfix": false, "name": "test_add_remove_router_interface_with_subnet_id[id-5a7184b5-447d-4513-bf0e-a6c020d70ad0,smoke]", "value": "", "classname": "tempest.api.network.test_routers.RoutersIpV6Test", "time": 32.366, "action": "passed", "message": "", "type": "", "regression": false}, {"successfix": false, "name": "test_volume_create_get_update_delete[id-3d3e4c03-dd47-4cdc-a3a0-381e91a7f3f3,smoke]", "value": "", "classname": "tempest.api.volume.test_volumes_get.VolumesV1GetTest", "time": 11.841, "action": "passed", "message": "", "type": "", "regression": false}, {"successfix": false, "name": "test_create_list_update_show_delete_security_group[id-4c69f27d-f2a9-429d-9b96-49d1d19ef222,smoke]", "value": "", "classname": "tempest.api.network.test_security_groups.SecGroupIPv6Test", "time": 4.133, "action": "passed", "message": "", "type": "", "regression": false}, {"successfix": false, "name": "test_create_show_delete_security_group_rule[id-1451d282-aa92-4c28-a716-e2745da75159,smoke]", "value": "", "classname": "tempest.api.network.test_security_groups.SecGroupIPv6Test", "time": 3.423, "action": "passed", "message": "", "type": "", "regression": false}, {"successfix": false, "name": "test_list_security_groups[id-44bcc753-6d7d-4b37-9982-51069eabf339,smoke]", "value": "", "classname": "tempest.api.network.test_security_groups.SecGroupIPv6Test", "time": 0.557, "action": "passed", "message": "", "type": "", "regression": false}, {"successfix": false, "name": "test_create_show_list_update_delete_router[id-704e170b-0e14-4af7-a57b-a4a0673cb9f3,smoke]", "value": "", "classname": "tempest.api.network.test_routers.RoutersIpV6Test", "time": 22.208, "action": "passed", "message": "", "type": "", "regression": false}, {"successfix": false, "name": "test_create_list_update_show_delete_security_group[id-21fb980a-4961-47db-b093-9f8d03cf80a0,smoke]", "value": "", "classname": "tempest.api.network.test_security_groups.SecGroupTest", "time": 4.147, "action": "passed", "message": "", "type": "", "regression": false}, {"successfix": false, "name": "test_create_show_delete_security_group_rule[id-8855809c-0f3b-43b6-ab14-1b2d70b8c2a4,smoke]", "value": "", "classname": "tempest.api.network.test_security_groups.SecGroupTest", "time": 4.038, "action": "passed", "message": "", "type": "", "regression": false}, {"successfix": false, "name": "test_list_security_groups[id-b3e0158d-853c-4283-9ff8-b349ff7b5988,smoke]", "value": "", "classname": "tempest.api.network.test_security_groups.SecGroupTest", "time": 0.122, "action": "passed", "message": "", "type": "", "regression": false}, {"successfix": false, "name": "test_volume_create_get_update_delete_from_image[id-86269e74-466d-4dca-a985-267715e6383c,image,smoke]", "value": "", "classname": "tempest.api.volume.test_volumes_get.VolumesV1GetTest", "time": 20.037, "action": "passed", "message": "", "type": "", "regression": false}, {"successfix": false, "name": "test_api_version_resources[id-714f1f2a-7479-4643-8648-b94f99361db6,smoke]", "value": "", "classname": "tempest.api.network.test_versions.NetworksApiDiscovery", "time": 0.007, "action": "passed", "message": "", "type": "", "regression": false}, {"successfix": false, "name": "setUpClass (tempest.api.object_storage.test_account_services.AccountTest)", "value": "AccountTest skipped as swift is not available", "classname": "", "time": 0.0, "action": "skipped", "message": "", "type": "", "regression": false}, {"successfix": false, "name": "test_filter_subnetpool_tags[id-8c090110-ef16-429f-bae7-298f72260331,smoke]", "value": "", "classname": "neutron.tests.tempest.api.test_tag.TagFilterSubnetpoolTestJSON", "time": 2.597, "action": "passed", "message": "", "type": "", "regression": false}, {"successfix": false, "name": "test_create_list_show_update_delete_subnetpools[id-b254c398-9a00-41f2-bcc4-4ea77e80d329,smoke]", "value": "", "classname": "tempest.api.network.test_subnetpools_extensions.SubnetPoolsTestJSON", "time": 5.519, "action": "passed", "message": "", "type": "", "regression": false}, {"successfix": false, "name": "setUpClass (tempest.api.object_storage.test_container_quotas.ContainerQuotasTest)", "value": "ContainerQuotasTest skipped as swift is not available", "classname": "", "time": 0.0, "action": "skipped", "message": "", "type": "", "regression": false}, {"successfix": false, "name": "test_subnet_tags[id-e25e9a6d-8c62-476f-9e80-b154154c5592,smoke]", "value": "", "classname": "neutron.tests.tempest.api.test_tag.TagSubnetTestJSON", "time": 11.662, "action": "passed", "message": "", "type": "", "regression": false}, {"successfix": false, "name": "test_resource_type_list[id-5785f96b-c0df-46dd-b6dd-21df0f4a1da6,smoke]", "value": "", "classname": "tempest.api.orchestration.stacks.test_resource_types.ResourceTypesTest", "time": 19.945, "action": "passed", "message": "", "type": "", "regression": false}, {"successfix": false, "name": "test_stack_crud_no_resources[id-8e7d74f2-3df1-4b05-8e4d-68c5b7f86a37,smoke]", "value": "", "classname": "tempest.api.orchestration.stacks.test_stacks.StacksTestJSON", "time": 9.221, "action": "passed", "message": "", "type": "", "regression": false}, {"successfix": false, "name": "test_stack_list_responds[id-0e4738ce-c2fc-46b9-9094-2671beec28e0,smoke]", "value": "", "classname": "tempest.api.orchestration.stacks.test_stacks.StacksTestJSON", "time": 0.102, "action": "passed", "message": "", "type": "", "regression": false}, {"successfix": false, "name": "test_resource_type_show[id-8eabfe15-503c-42b9-a638-c1915a2157b4,smoke]", "value": "", "classname": "tempest.api.orchestration.stacks.test_resource_types.ResourceTypesTest", "time": 31.777, "action": "passed", "message": "", "type": "", "regression": false}, {"successfix": false, "name": "test_resource_type_template[id-632142c4-acbb-4be8-8868-ae2aba552b0b,smoke]", "value": "", "classname": "tempest.api.orchestration.stacks.test_resource_types.ResourceTypesTest", "time": 0.064, "action": "passed", "message": "", "type": "", "regression": false}, {"successfix": false, "name": "test_volume_list[id-9b45285e-9792-4478-bb6f-47e903579ea1,smoke]", "value": "", "classname": "tempest.api.volume.test_volumes_list.VolumesV2ListTestJSON", "time": 0.115, "action": "passed", "message": "", "type": "", "regression": false}, {"successfix": false, "name": "test_network_basic_ops[compute,id-f323b3ba-82f8-4db7-8ea6-6a895869ec49,network,smoke]", "value": "", "classname": "tempest.scenario.test_network_basic_ops.TestNetworkBasicOps", "time": 164.319, "action": "passed", "message": "", "type": "", "regression": false}, {"successfix": false, "name": "test_get_deployment_list[id-d1c854cf-e78b-4d59-8c67-a1b6b2519b76,smoke]", "value": "", "classname": "tempest.api.orchestration.stacks.test_soft_conf.TestSoftwareConfig", "time": 5.874, "action": "passed", "message": "", "type": "", "regression": false}, {"successfix": false, "name": "test_get_deployment_metadata[id-bcf24d12-2d8d-4c41-b97d-d735d41405d9,smoke]", "value": "", "classname": "tempest.api.orchestration.stacks.test_soft_conf.TestSoftwareConfig", "time": 1.923, "action": "passed", "message": "", "type": "", "regression": false}, {"successfix": false, "name": "test_get_software_config[id-91018d8f-041a-407d-8fc1-ca10c533b8b8,smoke]", "value": "", "classname": "tempest.api.orchestration.stacks.test_soft_conf.TestSoftwareConfig", "time": 3.052, "action": "passed", "message": "", "type": "", "regression": false}, {"successfix": false, "name": "test_software_deployment_create_validate[id-72fde0da-6755-4344-9a0c-4b32924c813b,smoke]", "value": "", "classname": "tempest.api.orchestration.stacks.test_soft_conf.TestSoftwareConfig", "time": 1.98, "action": "passed", "message": "", "type": "", "regression": false}, {"successfix": false, "name": "test_software_deployment_update_no_metadata_change[id-52177087-213d-4fe1-8fe5-15c2a7c528e5,smoke]", "value": "", "classname": "tempest.api.orchestration.stacks.test_soft_conf.TestSoftwareConfig", "time": 1.24, "action": "passed", "message": "", "type": "", "regression": false}, {"successfix": false, "name": "test_software_deployment_update_with_metadata_change[id-49b47cdc-82db-4df2-8d0a-2ec39674e25a,smoke]", "value": "", "classname": "tempest.api.orchestration.stacks.test_soft_conf.TestSoftwareConfig", "time": 1.046, "action": "passed", "message": "", "type": "", "regression": false}, {"successfix": false, "name": "test_server_basic_ops[compute,id-7fff3fb3-91d8-4fd0-bd7d-0204f1f180ba,network,smoke]", "value": "", "classname": "tempest.scenario.test_server_basic_ops.TestServerBasicOps", "time": 40.67, "action": "passed", "message": "", "type": "", "regression": false}, {"successfix": false, "name": "setUpClass (mistral_tempest_tests.tests.api.v2.test_cron_triggers.CronTriggerTestsV2)", "value": "Mistral support is required.", "classname": "", "time": 0.0, "action": "skipped", "message": "", "type": "", "regression": false}, {"successfix": false, "name": "setUpClass (mistral_tempest_tests.tests.api.v2.test_tasks.TasksTestsV2)", "value": "Mistral support is required.", "classname": "", "time": 0.0, "action": "skipped", "message": "", "type": "", "regression": false}, {"successfix": false, "name": "setUpClass (mistral_tempest_tests.tests.api.v2.test_workflows.WorkflowTestsV2)", "value": "Mistral support is required.", "classname": "", "time": 0.0, "action": "skipped", "message": "", "type": "", "regression": false}, {"successfix": false, "name": "test_subnetpool_tags[id-d0880a81-0f80-4e28-b501-9eb658700007,smoke]", "value": "", "classname": "neutron.tests.tempest.api.test_tag.TagSubnetPoolTestJSON", "time": 4.442, "action": "passed", "message": "", "type": "", "regression": false}, {"successfix": false, "name": "test_volume_create_get_update_delete[id-71611f9e-bab4-4221-b7e6-c66f6339c2bd,smoke]", "value": "", "classname": "tempest.api.volume.test_volumes_get.VolumesV2GetTest", "time": 10.531, "action": "passed", "message": "", "type": "", "regression": false}, {"successfix": false, "name": "test_volume_create_get_update_delete_from_image[id-e4d768c7-c208-4d81-b8f7-357cac931a63,image,smoke]", "value": "", "classname": "tempest.api.volume.test_volumes_get.VolumesV2GetTest", "time": 16.721, "action": "passed", "message": "", "type": "", "regression": false}, {"successfix": false, "name": "setUpClass (tempest.scenario.test_server_multinode.TestServerMultinode)", "value": "Less than 2 compute nodes, skipping multinode tests.", "classname": "", "time": 0.0, "action": "skipped", "message": "", "type": "", "regression": false}, {"successfix": false, "name": "test_filter_router_tags[id-0c2e6d83-ae24-468d-8516-b7c5785bef0a,smoke]", "value": "", "classname": "neutron.tests.tempest.api.test_tag.TagFilterRouterTestJSON", "time": 2.531, "action": "passed", "message": "", "type": "", "regression": false}, {"successfix": false, "name": "test_volume_boot_pattern[compute,id-557cd2c2-4eb8-4dce-98be-f86765ff311b,image,smoke,volume]", "value": "", "classname": "tempest.scenario.test_volume_boot_pattern.TestVolumeBootPattern", "time": 158.856, "action": "passed", "message": "", "type": "", "regression": false}, {"successfix": false, "name": "test_network_tags[id-15c72621-1e2f-4e3b-9895-1af552272aa5,smoke]", "value": "", "classname": "neutron.tests.tempest.api.test_tag.TagNetworkTestJSON", "time": 5.626, "action": "passed", "message": "", "type": "", "regression": false}, {"successfix": false, "name": "test_volume_boot_pattern[compute,id-557cd2c2-4eb8-4dce-98be-f86765ff311b,image,smoke,volume]", "value": "", "classname": "tempest.scenario.test_volume_boot_pattern.TestVolumeBootPatternV2", "time": 139.931, "action": "passed", "message": "", "type": "", "regression": false}, {"successfix": false, "name": "setUpClass (mistral_tempest_tests.tests.api.v2.test_executions.ExecutionTestsV2)", "value": "Mistral support is required.", "classname": "", "time": 0.0, "action": "skipped", "message": "", "type": "", "regression": false}, {"successfix": false, "name": "setUpClass (mistral_tempest_tests.tests.api.v2.test_workbooks.WorkbookTestsV2)", "value": "Mistral support is required.", "classname": "", "time": 0.0, "action": "skipped", "message": "", "type": "", "regression": false}, {"successfix": false, "name": "setUpClass (inspector_tempest_plugin.tests.test_basic.InspectorSmokeTest)", "value": "Ironic is not enabled.", "classname": "", "time": 0.0, "action": "skipped", "message": "", "type": "", "regression": false}, {"successfix": false, "name": "test_filter_port_tags[id-fc626f6b-5fcd-4688-88bf-7bf13ac6f079,smoke]", "value": "", "classname": "neutron.tests.tempest.api.test_tag.TagFilterPortTestJSON", "time": 1.094, "action": "passed", "message": "", "type": "", "regression": false}, {"successfix": false, "name": "test_port_tags[id-89f16085-1987-4460-90de-e8aeb9d63e57,smoke]", "value": "", "classname": "neutron.tests.tempest.api.test_tag.TagPortTestJSON", "time": 3.966, "action": "passed", "message": "", "type": "", "regression": false}, {"successfix": false, "name": "test_router_tags[id-ad41caf1-c8b9-4708-83f6-a7d27e900a4c,smoke]", "value": "", "classname": "neutron.tests.tempest.api.test_tag.TagRouterTestJSON", "time": 5.273, "action": "passed", "message": "", "type": "", "regression": false}]	0
1b536555-967f-4f51-bfe3-dc15513d86dc	2018-07-18 14:13:26.010313	2018-07-18 14:13:26.027723	Tempest	130	117	13	0	0	1308365	024e5e39-b694-4045-9f9f-150c18ddb440	49eaaf4d-3096-48a3-9384-ceff76c04288	[{"successfix": false, "name": "test_get_flavor[id-fdfdc380-7482-4e7e-99f4-3dbdbdf4b631,smoke]", "value": "", "classname": "tempest.api.compute.flavors.test_flavors.FlavorsV2TestJSON", "time": 0.53, "action": "passed", "message": "", "type": "", "regression": false}, {"successfix": false, "name": "test_list_flavors[id-9895db89-9866-408c-a6a4-15af00ce94da,smoke]", "value": "", "classname": "tempest.api.compute.flavors.test_flavors.FlavorsV2TestJSON", "time": 0.167, "action": "passed", "message": "", "type": "", "regression": false}, {"successfix": false, "name": "test_default_domain_exists[id-fd693ced-a1d7-4687-94ed-3b81620d3991,smoke]", "value": "", "classname": "tempest.api.identity.admin.v3.test_domains.DefaultDomainTestJSON", "time": 0.228, "action": "passed", "message": "", "type": "", "regression": false}, {"successfix": false, "name": "test_security_group_rules_create[id-14deeed5-7828-4262-b1d9-f92c1821f48a,network,smoke]", "value": "", "classname": "tempest.api.compute.security_groups.test_security_group_rules.SecurityGroupRulesTestJSON", "time": 4.78, "action": "passed", "message": "", "type": "", "regression": false}, {"successfix": false, "name": "test_create_update_get_service[id-b5c88893-5c7e-4431-ae0b-012001c2d546,smoke]", "value": "", "classname": "tempest.api.identity.admin.v3.test_services.ServicesTestJSON", "time": 1.302, "action": "passed", "message": "", "type": "", "regression": false}, {"successfix": false, "name": "test_security_group_rules_list[id-bbf6f4ee-adaa-42a9-b811-4b0ec034ea58,network,smoke]", "value": "", "classname": "tempest.api.compute.security_groups.test_security_group_rules.SecurityGroupRulesTestJSON", "time": 6.598, "action": "passed", "message": "", "type": "", "regression": false}, {"successfix": false, "name": "test_security_groups_create_list_delete[id-cbada7f0-7ed0-47fe-8177-dd937d1894f8,network,smoke]", "value": "", "classname": "tempest.api.compute.security_groups.test_security_groups.SecurityGroupsTestJSON", "time": 13.727, "action": "passed", "message": "", "type": "", "regression": false}, {"successfix": false, "name": "test_get_trusts_all[id-61695af0-bec6-4bda-bf9c-ef1ba914819e,smoke]", "value": "", "classname": "tempest.api.identity.admin.v3.test_trusts.TrustsV3TestJSON", "time": 6.427, "action": "passed", "message": "", "type": "", "regression": false}, {"successfix": false, "name": "test_api_media_types[id-71478a40-38bb-42fe-b3c9-34abd8899d58,smoke]", "value": "", "classname": "tempest.api.identity.v3.test_api_discovery.TestApiDiscovery", "time": 0.228, "action": "passed", "message": "", "type": "", "regression": false}, {"successfix": false, "name": "test_api_version_resources[id-e065df73-b03f-4ce1-80d5-06a4ba8bdf4b,smoke]", "value": "", "classname": "tempest.api.identity.v3.test_api_discovery.TestApiDiscovery", "time": 0.285, "action": "passed", "message": "", "type": "", "regression": false}, {"successfix": false, "name": "test_api_version_statuses[id-269f7038-9f70-4012-95ac-a6cbbda614ce,smoke]", "value": "", "classname": "tempest.api.identity.v3.test_api_discovery.TestApiDiscovery", "time": 0.289, "action": "passed", "message": "", "type": "", "regression": false}, {"successfix": false, "name": "test_list_servers[id-433c6a8f-5e66-4761-9ade-abeb313876c6,smoke]", "value": "", "classname": "tempest.api.compute.servers.test_create_server.ServersTestManualDisk", "time": 0.349, "action": "passed", "message": "", "type": "", "regression": false}, {"successfix": false, "name": "test_verify_server_details[id-1b1bc049-9df9-4ced-9ed0-7adacf27471a,smoke]", "value": "", "classname": "tempest.api.compute.servers.test_create_server.ServersTestManualDisk", "time": 0.001, "action": "passed", "message": "", "type": "", "regression": false}, {"successfix": false, "name": "test_list_show_extensions[id-cb3968d2-1819-4b4a-98b5-850bbdb9e14b,smoke]", "value": "", "classname": "tempest.api.network.test_extensions.ExtensionsTestJSON", "time": 7.746, "action": "passed", "message": "", "type": "", "regression": false}, {"successfix": false, "name": "test_add_remove_fixed_ip[id-dc0ee336-dadc-44c1-a0bf-a65093f6644f,network,smoke]", "value": "", "classname": "tempest.api.compute.servers.test_attach_interfaces.AttachInterfacesTestJSON", "time": 34.806, "action": "passed", "message": "", "type": "", "regression": false}, {"successfix": false, "name": "test_list_servers[id-8e40ef78-2f4d-4361-9ff8-b485ec760466,smoke]", "value": "", "classname": "tempest.api.compute.servers.test_create_server.ServersTestJSON", "time": 0.33, "action": "passed", "message": "", "type": "", "regression": false}, {"successfix": false, "name": "test_verify_server_details[id-4bda6d9b-5528-4622-b240-53815132a996,smoke]", "value": "", "classname": "tempest.api.compute.servers.test_create_server.ServersTestJSON", "time": 0.001, "action": "passed", "message": "", "type": "", "regression": false}, {"successfix": false, "name": "test_create_user[id-7c2c6ff9-c611-49fa-80cc-21ac158cc6cc,smoke]", "value": "", "classname": "tempest.api.identity.admin.v2.test_users.UsersTestJSON", "time": 2.243, "action": "passed", "message": "", "type": "", "regression": false}, {"successfix": false, "name": "test_credentials_create_get_update_delete[id-a1a79747-66b3-4eaf-a9db-9dfa7697536f,smoke]", "value": "", "classname": "tempest.api.identity.admin.v3.test_credentials.CredentialsTestJSON", "time": 2.711, "action": "passed", "message": "", "type": "", "regression": false}, {"successfix": false, "name": "test_create_floating_ip_specifying_a_fixed_ip_address[id-bd3a6a9f-7311-4d18-ad4c-e8ded08539a9,smoke]", "value": "", "classname": "tempest.api.network.test_floating_ips.FloatingIPTestJSON", "time": 8.971, "action": "passed", "message": "", "type": "", "regression": false}, {"successfix": false, "name": "test_create_list_show_update_delete_floating_ip[id-26b46236-67bf-4408-85fc-b4c725b76be6,smoke]", "value": "", "classname": "tempest.api.network.test_floating_ips.FloatingIPTestJSON", "time": 8.629, "action": "passed", "message": "", "type": "", "regression": false}, {"successfix": false, "name": "test_create_update_delete_domain[id-fe4b71ea-30bd-46a4-92a0-4bd073035da0,smoke]", "value": "", "classname": "tempest.api.identity.admin.v3.test_domains.DomainsTestJSON", "time": 1.835, "action": "passed", "message": "", "type": "", "regression": false}, {"successfix": false, "name": "test_list_services[id-ecf0d25c-5d5b-4f61-bfda-f1fe34e73e69,smoke]", "value": "", "classname": "tempest.api.identity.admin.v2.test_services.ServicesTestJSON", "time": 2.637, "action": "passed", "message": "", "type": "", "regression": false}, {"successfix": false, "name": "test_update_endpoint[id-b734ae9b-12f5-46cf-a3c0-5aacefd24c7d,smoke]", "value": "", "classname": "tempest.api.identity.admin.v3.test_endpoints.EndPointsTestJSON", "time": 1.112, "action": "passed", "message": "", "type": "", "regression": false}, {"successfix": false, "name": "test_role_create_update_show_list[id-31307a8d-1b1b-4bc7-9b51-3ab0fc1b11b7,smoke]", "value": "", "classname": "tempest.api.identity.admin.v3.test_roles.RolesV3TestJSON", "time": 1.299, "action": "passed", "message": "", "type": "", "regression": false}, {"successfix": false, "name": "test_group_users_add_list_delete[id-630bcaa7-51b5-42ca-97d5-dea08605dbbf,smoke]", "value": "", "classname": "tempest.api.identity.admin.v3.test_groups.GroupsV3TestJSON", "time": 8.005, "action": "passed", "message": "", "type": "", "regression": false}, {"successfix": false, "name": "test_reboot_server_hard[id-8767976e-986f-4e19-809c-577a6c83d760,smoke]", "value": "", "classname": "tempest.api.compute.servers.test_server_actions.ServerActionsTestJSON", "time": 8.141, "action": "passed", "message": "", "type": "", "regression": false}, {"successfix": false, "name": "test_api_media_types[id-2fc6822e-b5a8-42ed-967b-11d86e881ce3,smoke]", "value": "", "classname": "tempest.api.identity.v2.test_api_discovery.TestApiDiscovery", "time": 0.272, "action": "passed", "message": "", "type": "", "regression": false}, {"successfix": false, "name": "test_api_version_resources[id-f149a4b9-57fc-4fcd-afaf-714ad0c4b207,smoke]", "value": "", "classname": "tempest.api.identity.v2.test_api_discovery.TestApiDiscovery", "time": 0.214, "action": "passed", "message": "", "type": "", "regression": false}, {"successfix": false, "name": "test_api_version_statuses[id-32fc7d57-3d2e-4d6c-aa30-e7dfc6fdc6f3,smoke]", "value": "", "classname": "tempest.api.identity.v2.test_api_discovery.TestApiDiscovery", "time": 0.415, "action": "passed", "message": "", "type": "", "regression": false}, {"successfix": false, "name": "test_create_port_in_allowed_allocation_pools[id-95a7d063-6529-49aa-9cfb-36630ed9cea7,smoke]", "value": "", "classname": "tempest.api.network.test_ports.PortsIpV6TestJSON", "time": 16.342, "action": "passed", "message": "", "type": "", "regression": false}, {"successfix": false, "name": "test_delete_image[id-4da8b06d-67e1-444e-a1ad-674c5c33db36,smoke]", "value": "", "classname": "tempest.api.image.v2.test_images.BasicOperationsImagesTest", "time": 2.207, "action": "passed", "message": "", "type": "", "regression": false}, {"successfix": false, "name": "test_register_upload_get_image_file[id-ea3084e4-bde9-4be0-90ec-46b478db894c,smoke]", "value": "", "classname": "tempest.api.image.v2.test_images.BasicOperationsImagesTest", "time": 3.372, "action": "passed", "message": "", "type": "", "regression": false}, {"successfix": false, "name": "test_create_region_with_specific_id[id-2216947c-2075-42f2-879c-341dd2eaee42,smoke]", "value": "", "classname": "tempest.api.identity.admin.v3.test_regions.RegionsTestJSON", "time": 0.735, "action": "passed", "message": "", "type": "", "regression": false}, {"successfix": false, "name": "test_update_image[id-91237988-3948-4e81-a43f-e9e34383e6c7,smoke]", "value": "", "classname": "tempest.api.image.v2.test_images.BasicOperationsImagesTest", "time": 3.69, "action": "passed", "message": "", "type": "", "regression": false}, {"successfix": false, "name": "setUpClass (tempest.api.object_storage.test_account_quotas.AccountQuotasTest)", "value": "AccountQuotasTest skipped as swift is not available", "classname": "", "time": 0.0, "action": "skipped", "message": "", "type": "", "regression": false}, {"successfix": false, "name": "test_create_port_with_no_securitygroups[id-0d9894f5-97d7-4ca4-9342-d5571d3a9b21,smoke]", "value": "", "classname": "tempest.api.network.test_ports.PortsIpV6TestJSON", "time": 16.162, "action": "passed", "message": "", "type": "", "regression": false}, {"successfix": false, "name": "test_create_update_delete_port[id-a1229df6-4e4c-485d-a72b-2b0a8af05fdd,smoke]", "value": "", "classname": "tempest.api.network.test_ports.PortsIpV6TestJSON", "time": 3.367, "action": "passed", "message": "", "type": "", "regression": false}, {"successfix": false, "name": "test_list_ports[id-21666509-180b-4171-b567-6c54f38fc3d0,smoke]", "value": "", "classname": "tempest.api.network.test_ports.PortsIpV6TestJSON", "time": 0.198, "action": "passed", "message": "", "type": "", "regression": false}, {"successfix": false, "name": "test_show_port[id-1da7a454-f57a-4e67-8f9d-24bc7d280873,smoke]", "value": "", "classname": "tempest.api.network.test_ports.PortsIpV6TestJSON", "time": 0.151, "action": "passed", "message": "", "type": "", "regression": false}, {"successfix": false, "name": "test_bulk_create_delete_network[id-94720f48-34f9-403a-b87d-5cc1fcd132d7,smoke]", "value": "", "classname": "tempest.api.network.test_networks.BulkNetworkOpsIpV6Test", "time": 5.536, "action": "passed", "message": "", "type": "", "regression": false}, {"successfix": false, "name": "test_bulk_create_delete_port[id-bd93e7f0-247d-4192-aa1c-4bb81d57469d,smoke]", "value": "", "classname": "tempest.api.network.test_networks.BulkNetworkOpsIpV6Test", "time": 7.102, "action": "passed", "message": "", "type": "", "regression": false}, {"successfix": false, "name": "test_attach_detach_volume_to_instance[compute,id-fff42874-7db5-4487-a8e1-ddda5fb5288d,smoke]", "value": "", "classname": "tempest.api.volume.test_volumes_actions.VolumesV1ActionsTest", "time": 20.023, "action": "passed", "message": "", "type": "", "regression": false}, {"successfix": false, "name": "test_bulk_create_delete_subnet[id-7549d64e-4938-489d-96ba-016451660556,smoke]", "value": "", "classname": "tempest.api.network.test_networks.BulkNetworkOpsIpV6Test", "time": 12.11, "action": "passed", "message": "", "type": "", "regression": false}, {"successfix": false, "name": "test_list_server_addresses[id-b501abea-63da-4741-b62f-10426d2bd5c8,network,smoke]", "value": "", "classname": "tempest.api.compute.servers.test_server_addresses.ServerAddressesTestJSON", "time": 0.268, "action": "passed", "message": "", "type": "", "regression": false}, {"successfix": false, "name": "test_list_server_addresses_by_network[id-8dd9d0d9-a1f9-4207-bf01-33fbd9d0adfd,network,smoke]", "value": "", "classname": "tempest.api.compute.servers.test_server_addresses.ServerAddressesTestJSON", "time": 0.409, "action": "passed", "message": "", "type": "", "regression": false}, {"successfix": false, "name": "test_create_update_delete_policy[id-2fdb5e9b-2226-4b83-9576-7037943846e1,smoke]", "value": "", "classname": "tempest.api.identity.admin.v3.test_policies.PoliciesTestJSON", "time": 0.819, "action": "passed", "message": "", "type": "", "regression": false}, {"successfix": false, "name": "test_bulk_create_delete_network[id-dd90abb7-1a4e-48e3-a167-f277ec11108f,smoke]", "value": "", "classname": "tempest.api.network.test_networks.BulkNetworkOpsTest", "time": 5.8, "action": "passed", "message": "", "type": "", "regression": false}, {"successfix": false, "name": "test_attach_detach_volume_to_instance[compute,id-fff42874-7db5-4487-a8e1-ddda5fb5288d,smoke]", "value": "", "classname": "tempest.api.volume.test_volumes_actions.VolumesV2ActionsTest", "time": 18.366, "action": "passed", "message": "", "type": "", "regression": false}, {"successfix": false, "name": "test_bulk_create_delete_port[id-eeb7533f-fd53-411a-9289-fcb4258b7f45,smoke]", "value": "", "classname": "tempest.api.network.test_networks.BulkNetworkOpsTest", "time": 7.748, "action": "passed", "message": "", "type": "", "regression": false}, {"successfix": false, "name": "test_add_multiple_router_interfaces[id-142463a1-ed6a-4b9d-abe4-78569731c6f9,smoke]", "value": "", "classname": "tempest.api.network.test_routers.RoutersTest", "time": 42.241, "action": "passed", "message": "", "type": "", "regression": false}, {"successfix": false, "name": "test_bulk_create_delete_subnet[id-09aaf80c-4cde-43f0-80bb-cc7486133057,smoke]", "value": "", "classname": "tempest.api.network.test_networks.BulkNetworkOpsTest", "time": 5.665, "action": "passed", "message": "", "type": "", "regression": false}, {"successfix": false, "name": "test_volume_list[id-44f7b3e0-6373-4427-949f-68ab32d6e184,smoke]", "value": "", "classname": "tempest.api.volume.test_volumes_list.VolumesV1ListTestJSON", "time": 0.092, "action": "passed", "message": "", "type": "", "regression": false}, {"successfix": false, "name": "setUpClass (mistral_tempest_tests.tests.api.v2.test_actions.ActionTestsV2)", "value": "Mistral support is required.", "classname": "", "time": 0.0, "action": "skipped", "message": "", "type": "", "regression": false}, {"successfix": false, "name": "test_create_update_delete_network_subnet[id-983e1633-e577-415b-851d-635eb5025ec9,smoke]", "value": "", "classname": "tempest.api.network.test_networks.NetworksIpV6Test", "time": 15.892, "action": "passed", "message": "", "type": "", "regression": false}, {"successfix": false, "name": "test_external_network_visibility[id-4334ba1b-de5c-41e7-8511-0d0eeb5c285b,smoke]", "value": "", "classname": "tempest.api.network.test_networks.NetworksIpV6Test", "time": 0.797, "action": "passed", "message": "", "type": "", "regression": false}, {"successfix": false, "name": "test_list_networks[id-593e96ef-4d7e-47a3-8d5e-9cb6c1504acb,smoke]", "value": "", "classname": "tempest.api.network.test_networks.NetworksIpV6Test", "time": 0.832, "action": "passed", "message": "", "type": "", "regression": false}, {"successfix": false, "name": "test_list_subnets[id-4f3c4a81-2c76-4c27-8b4a-ec3c4ed80107,smoke]", "value": "", "classname": "tempest.api.network.test_networks.NetworksIpV6Test", "time": 0.6, "action": "passed", "message": "", "type": "", "regression": false}, {"successfix": false, "name": "test_show_network[id-4f278dab-1e1f-4126-8112-5c8d115ad62f,smoke]", "value": "", "classname": "tempest.api.network.test_networks.NetworksIpV6Test", "time": 0.283, "action": "passed", "message": "", "type": "", "regression": false}, {"successfix": false, "name": "test_show_subnet[id-a24dbec1-c9a5-4d36-a524-20033184f620,smoke]", "value": "", "classname": "tempest.api.network.test_networks.NetworksIpV6Test", "time": 0.229, "action": "passed", "message": "", "type": "", "regression": false}, {"successfix": false, "name": "test_create_rbac_policy_with_target_tenant_none[id-ff13925f-b235-413e-8ef3-1325d463add9,smoke]", "value": "", "classname": "neutron.tests.tempest.api.admin.test_shared_network_extension.RBACSharedNetworksTest", "time": 7.025, "action": "passed", "message": "", "type": "", "regression": false}, {"successfix": false, "name": "test_add_remove_router_interface_with_port_id[id-02693de1-7330-4857-9c77-b25c33607b35,smoke]", "value": "", "classname": "tempest.api.network.test_routers.RoutersTest", "time": 29.507, "action": "passed", "message": "", "type": "", "regression": false}, {"successfix": false, "name": "test_create_rbac_policy_with_target_tenant_too_long_id[id-693b66cd-3ada-41ac-886a-6cfee12f1b7b,smoke]", "value": "", "classname": "neutron.tests.tempest.api.admin.test_shared_network_extension.RBACSharedNetworksTest", "time": 5.082, "action": "passed", "message": "", "type": "", "regression": false}, {"successfix": false, "name": "test_network_only_visible_to_policy_target[id-7c621ce5-de0d-4274-8d89-02be7bd9e225,smoke]", "value": "", "classname": "neutron.tests.tempest.api.admin.test_shared_network_extension.RBACSharedNetworksTest", "time": 12.603, "action": "passed", "message": "", "type": "", "regression": false}, {"successfix": false, "name": "test_create_update_delete_network_subnet[id-b672a174-6ed4-4d0e-a0cd-404dda544c09,smoke]", "value": "", "classname": "tempest.api.network.test_networks.NetworksTest", "time": 9.87, "action": "passed", "message": "", "type": "", "regression": false}, {"successfix": false, "name": "test_external_network_visibility[id-403ab82d-bcdf-45e2-bddb-655b3a00a1f5,smoke]", "value": "", "classname": "tempest.api.network.test_networks.NetworksTest", "time": 0.803, "action": "passed", "message": "", "type": "", "regression": false}, {"successfix": false, "name": "test_list_networks[id-5daa85e7-5edf-4deb-992c-e0107fd19b2b,smoke]", "value": "", "classname": "tempest.api.network.test_networks.NetworksTest", "time": 0.342, "action": "passed", "message": "", "type": "", "regression": false}, {"successfix": false, "name": "test_list_subnets[id-f2c03a3a-b43b-4829-8251-6c693448c8c2,smoke]", "value": "", "classname": "tempest.api.network.test_networks.NetworksTest", "time": 0.203, "action": "passed", "message": "", "type": "", "regression": false}, {"successfix": false, "name": "test_show_network[id-9b922b8a-ef9d-4a26-bbbd-7c37ecfc7f21,smoke]", "value": "", "classname": "tempest.api.network.test_networks.NetworksTest", "time": 0.293, "action": "passed", "message": "", "type": "", "regression": false}, {"successfix": false, "name": "test_show_subnet[id-2207e5f2-2de1-46c5-954d-a2295e75ca2b,smoke]", "value": "", "classname": "tempest.api.network.test_networks.NetworksTest", "time": 0.436, "action": "passed", "message": "", "type": "", "regression": false}, {"successfix": false, "name": "test_add_remove_router_interface_with_subnet_id[id-9bd032b6-4292-4e4d-ab2e-0113fc638bfa,smoke]", "value": "", "classname": "tempest.api.network.test_routers.RoutersTest", "time": 29.382, "action": "passed", "message": "", "type": "", "regression": false}, {"successfix": false, "name": "test_add_multiple_router_interfaces[id-828bca65-e8e4-4e55-88a5-ce15333ee461,smoke]", "value": "", "classname": "tempest.api.network.test_routers.RoutersIpV6Test", "time": 44.825, "action": "passed", "message": "", "type": "", "regression": false}, {"successfix": false, "name": "test_filter_network_tags[id-574d99a6-0432-4379-a3d3-238e55547eb4,smoke]", "value": "", "classname": "neutron.tests.tempest.api.test_tag.TagFilterNetworkTestJSON", "time": 3.084, "action": "passed", "message": "", "type": "", "regression": false}, {"successfix": false, "name": "test_create_show_list_update_delete_router[id-a19c4c3c-490d-41fb-9ea6-a37c04b6db89,smoke]", "value": "", "classname": "tempest.api.network.test_routers.RoutersTest", "time": 21.941, "action": "passed", "message": "", "type": "", "regression": false}, {"successfix": false, "name": "test_create_port_in_allowed_allocation_pools[id-c6c55e41-f6e5-4cc7-b2af-9b7d863a4ac7,smoke]", "value": "", "classname": "tempest.api.network.test_ports.PortsTestJSON", "time": 16.602, "action": "passed", "message": "", "type": "", "regression": false}, {"successfix": false, "name": "test_add_remove_router_interface_with_port_id[id-ac58ceb1-0cb8-40ad-8a1d-3be5636dcd41,smoke]", "value": "", "classname": "tempest.api.network.test_routers.RoutersIpV6Test", "time": 28.079, "action": "passed", "message": "", "type": "", "regression": false}, {"successfix": false, "name": "test_create_port_with_no_securitygroups[id-8ca6d376-ceff-423b-9021-38aa76bd51c5,smoke]", "value": "", "classname": "tempest.api.network.test_ports.PortsTestJSON", "time": 22.243, "action": "passed", "message": "", "type": "", "regression": false}, {"successfix": false, "name": "test_create_update_delete_port[id-153838d9-8c65-439a-91a3-ff40e5b182ac,smoke]", "value": "", "classname": "tempest.api.network.test_ports.PortsTestJSON", "time": 4.372, "action": "passed", "message": "", "type": "", "regression": false}, {"successfix": false, "name": "test_list_ports[id-124ef885-6e91-482f-9789-9315db2e13ce,smoke]", "value": "", "classname": "tempest.api.network.test_ports.PortsTestJSON", "time": 0.18, "action": "passed", "message": "", "type": "", "regression": false}, {"successfix": false, "name": "test_filter_subnet_tags[id-06dcba8d-6ce5-4cb1-b733-d5bbbd94f019,smoke]", "value": "", "classname": "neutron.tests.tempest.api.test_tag.TagFilterSubnetTestJSON", "time": 2.984, "action": "passed", "message": "", "type": "", "regression": false}, {"successfix": false, "name": "test_show_port[id-5e82e447-cca1-4794-9f2b-14465f323645,smoke]", "value": "", "classname": "tempest.api.network.test_ports.PortsTestJSON", "time": 0.239, "action": "passed", "message": "", "type": "", "regression": false}, {"successfix": false, "name": "setUpClass (tempest.api.object_storage.test_container_services.ContainerTest)", "value": "ContainerTest skipped as swift is not available", "classname": "", "time": 0.0, "action": "skipped", "message": "", "type": "", "regression": false}, {"successfix": false, "name": "setUpClass (tempest.api.object_storage.test_object_services.ObjectTest)", "value": "ObjectTest skipped as swift is not available", "classname": "", "time": 0.0, "action": "skipped", "message": "", "type": "", "regression": false}, {"successfix": false, "name": "test_add_remove_router_interface_with_subnet_id[id-5a7184b5-447d-4513-bf0e-a6c020d70ad0,smoke]", "value": "", "classname": "tempest.api.network.test_routers.RoutersIpV6Test", "time": 32.366, "action": "passed", "message": "", "type": "", "regression": false}, {"successfix": false, "name": "test_volume_create_get_update_delete[id-3d3e4c03-dd47-4cdc-a3a0-381e91a7f3f3,smoke]", "value": "", "classname": "tempest.api.volume.test_volumes_get.VolumesV1GetTest", "time": 11.841, "action": "passed", "message": "", "type": "", "regression": false}, {"successfix": false, "name": "test_create_list_update_show_delete_security_group[id-4c69f27d-f2a9-429d-9b96-49d1d19ef222,smoke]", "value": "", "classname": "tempest.api.network.test_security_groups.SecGroupIPv6Test", "time": 4.133, "action": "passed", "message": "", "type": "", "regression": false}, {"successfix": false, "name": "test_create_show_delete_security_group_rule[id-1451d282-aa92-4c28-a716-e2745da75159,smoke]", "value": "", "classname": "tempest.api.network.test_security_groups.SecGroupIPv6Test", "time": 3.423, "action": "passed", "message": "", "type": "", "regression": false}, {"successfix": false, "name": "test_list_security_groups[id-44bcc753-6d7d-4b37-9982-51069eabf339,smoke]", "value": "", "classname": "tempest.api.network.test_security_groups.SecGroupIPv6Test", "time": 0.557, "action": "passed", "message": "", "type": "", "regression": false}, {"successfix": false, "name": "test_create_show_list_update_delete_router[id-704e170b-0e14-4af7-a57b-a4a0673cb9f3,smoke]", "value": "", "classname": "tempest.api.network.test_routers.RoutersIpV6Test", "time": 22.208, "action": "passed", "message": "", "type": "", "regression": false}, {"successfix": false, "name": "test_create_list_update_show_delete_security_group[id-21fb980a-4961-47db-b093-9f8d03cf80a0,smoke]", "value": "", "classname": "tempest.api.network.test_security_groups.SecGroupTest", "time": 4.147, "action": "passed", "message": "", "type": "", "regression": false}, {"successfix": false, "name": "test_create_show_delete_security_group_rule[id-8855809c-0f3b-43b6-ab14-1b2d70b8c2a4,smoke]", "value": "", "classname": "tempest.api.network.test_security_groups.SecGroupTest", "time": 4.038, "action": "passed", "message": "", "type": "", "regression": false}, {"successfix": false, "name": "test_list_security_groups[id-b3e0158d-853c-4283-9ff8-b349ff7b5988,smoke]", "value": "", "classname": "tempest.api.network.test_security_groups.SecGroupTest", "time": 0.122, "action": "passed", "message": "", "type": "", "regression": false}, {"successfix": false, "name": "test_volume_create_get_update_delete_from_image[id-86269e74-466d-4dca-a985-267715e6383c,image,smoke]", "value": "", "classname": "tempest.api.volume.test_volumes_get.VolumesV1GetTest", "time": 20.037, "action": "passed", "message": "", "type": "", "regression": false}, {"successfix": false, "name": "test_api_version_resources[id-714f1f2a-7479-4643-8648-b94f99361db6,smoke]", "value": "", "classname": "tempest.api.network.test_versions.NetworksApiDiscovery", "time": 0.007, "action": "passed", "message": "", "type": "", "regression": false}, {"successfix": false, "name": "setUpClass (tempest.api.object_storage.test_account_services.AccountTest)", "value": "AccountTest skipped as swift is not available", "classname": "", "time": 0.0, "action": "skipped", "message": "", "type": "", "regression": false}, {"successfix": false, "name": "test_filter_subnetpool_tags[id-8c090110-ef16-429f-bae7-298f72260331,smoke]", "value": "", "classname": "neutron.tests.tempest.api.test_tag.TagFilterSubnetpoolTestJSON", "time": 2.597, "action": "passed", "message": "", "type": "", "regression": false}, {"successfix": false, "name": "test_create_list_show_update_delete_subnetpools[id-b254c398-9a00-41f2-bcc4-4ea77e80d329,smoke]", "value": "", "classname": "tempest.api.network.test_subnetpools_extensions.SubnetPoolsTestJSON", "time": 5.519, "action": "passed", "message": "", "type": "", "regression": false}, {"successfix": false, "name": "setUpClass (tempest.api.object_storage.test_container_quotas.ContainerQuotasTest)", "value": "ContainerQuotasTest skipped as swift is not available", "classname": "", "time": 0.0, "action": "skipped", "message": "", "type": "", "regression": false}, {"successfix": false, "name": "test_subnet_tags[id-e25e9a6d-8c62-476f-9e80-b154154c5592,smoke]", "value": "", "classname": "neutron.tests.tempest.api.test_tag.TagSubnetTestJSON", "time": 11.662, "action": "passed", "message": "", "type": "", "regression": false}, {"successfix": false, "name": "test_resource_type_list[id-5785f96b-c0df-46dd-b6dd-21df0f4a1da6,smoke]", "value": "", "classname": "tempest.api.orchestration.stacks.test_resource_types.ResourceTypesTest", "time": 19.945, "action": "passed", "message": "", "type": "", "regression": false}, {"successfix": false, "name": "test_stack_crud_no_resources[id-8e7d74f2-3df1-4b05-8e4d-68c5b7f86a37,smoke]", "value": "", "classname": "tempest.api.orchestration.stacks.test_stacks.StacksTestJSON", "time": 9.221, "action": "passed", "message": "", "type": "", "regression": false}, {"successfix": false, "name": "test_stack_list_responds[id-0e4738ce-c2fc-46b9-9094-2671beec28e0,smoke]", "value": "", "classname": "tempest.api.orchestration.stacks.test_stacks.StacksTestJSON", "time": 0.102, "action": "passed", "message": "", "type": "", "regression": false}, {"successfix": false, "name": "test_resource_type_show[id-8eabfe15-503c-42b9-a638-c1915a2157b4,smoke]", "value": "", "classname": "tempest.api.orchestration.stacks.test_resource_types.ResourceTypesTest", "time": 31.777, "action": "passed", "message": "", "type": "", "regression": false}, {"successfix": false, "name": "test_resource_type_template[id-632142c4-acbb-4be8-8868-ae2aba552b0b,smoke]", "value": "", "classname": "tempest.api.orchestration.stacks.test_resource_types.ResourceTypesTest", "time": 0.064, "action": "passed", "message": "", "type": "", "regression": false}, {"successfix": false, "name": "test_volume_list[id-9b45285e-9792-4478-bb6f-47e903579ea1,smoke]", "value": "", "classname": "tempest.api.volume.test_volumes_list.VolumesV2ListTestJSON", "time": 0.115, "action": "passed", "message": "", "type": "", "regression": false}, {"successfix": false, "name": "test_network_basic_ops[compute,id-f323b3ba-82f8-4db7-8ea6-6a895869ec49,network,smoke]", "value": "", "classname": "tempest.scenario.test_network_basic_ops.TestNetworkBasicOps", "time": 164.319, "action": "passed", "message": "", "type": "", "regression": false}, {"successfix": false, "name": "test_get_deployment_list[id-d1c854cf-e78b-4d59-8c67-a1b6b2519b76,smoke]", "value": "", "classname": "tempest.api.orchestration.stacks.test_soft_conf.TestSoftwareConfig", "time": 5.874, "action": "passed", "message": "", "type": "", "regression": false}, {"successfix": false, "name": "test_get_deployment_metadata[id-bcf24d12-2d8d-4c41-b97d-d735d41405d9,smoke]", "value": "", "classname": "tempest.api.orchestration.stacks.test_soft_conf.TestSoftwareConfig", "time": 1.923, "action": "passed", "message": "", "type": "", "regression": false}, {"successfix": false, "name": "test_get_software_config[id-91018d8f-041a-407d-8fc1-ca10c533b8b8,smoke]", "value": "", "classname": "tempest.api.orchestration.stacks.test_soft_conf.TestSoftwareConfig", "time": 3.052, "action": "passed", "message": "", "type": "", "regression": false}, {"successfix": false, "name": "test_software_deployment_create_validate[id-72fde0da-6755-4344-9a0c-4b32924c813b,smoke]", "value": "", "classname": "tempest.api.orchestration.stacks.test_soft_conf.TestSoftwareConfig", "time": 1.98, "action": "passed", "message": "", "type": "", "regression": false}, {"successfix": false, "name": "test_software_deployment_update_no_metadata_change[id-52177087-213d-4fe1-8fe5-15c2a7c528e5,smoke]", "value": "", "classname": "tempest.api.orchestration.stacks.test_soft_conf.TestSoftwareConfig", "time": 1.24, "action": "passed", "message": "", "type": "", "regression": false}, {"successfix": false, "name": "test_software_deployment_update_with_metadata_change[id-49b47cdc-82db-4df2-8d0a-2ec39674e25a,smoke]", "value": "", "classname": "tempest.api.orchestration.stacks.test_soft_conf.TestSoftwareConfig", "time": 1.046, "action": "passed", "message": "", "type": "", "regression": false}, {"successfix": false, "name": "test_server_basic_ops[compute,id-7fff3fb3-91d8-4fd0-bd7d-0204f1f180ba,network,smoke]", "value": "", "classname": "tempest.scenario.test_server_basic_ops.TestServerBasicOps", "time": 40.67, "action": "passed", "message": "", "type": "", "regression": false}, {"successfix": false, "name": "setUpClass (mistral_tempest_tests.tests.api.v2.test_cron_triggers.CronTriggerTestsV2)", "value": "Mistral support is required.", "classname": "", "time": 0.0, "action": "skipped", "message": "", "type": "", "regression": false}, {"successfix": false, "name": "setUpClass (mistral_tempest_tests.tests.api.v2.test_tasks.TasksTestsV2)", "value": "Mistral support is required.", "classname": "", "time": 0.0, "action": "skipped", "message": "", "type": "", "regression": false}, {"successfix": false, "name": "setUpClass (mistral_tempest_tests.tests.api.v2.test_workflows.WorkflowTestsV2)", "value": "Mistral support is required.", "classname": "", "time": 0.0, "action": "skipped", "message": "", "type": "", "regression": false}, {"successfix": false, "name": "test_subnetpool_tags[id-d0880a81-0f80-4e28-b501-9eb658700007,smoke]", "value": "", "classname": "neutron.tests.tempest.api.test_tag.TagSubnetPoolTestJSON", "time": 4.442, "action": "passed", "message": "", "type": "", "regression": false}, {"successfix": false, "name": "test_volume_create_get_update_delete[id-71611f9e-bab4-4221-b7e6-c66f6339c2bd,smoke]", "value": "", "classname": "tempest.api.volume.test_volumes_get.VolumesV2GetTest", "time": 10.531, "action": "passed", "message": "", "type": "", "regression": false}, {"successfix": false, "name": "test_volume_create_get_update_delete_from_image[id-e4d768c7-c208-4d81-b8f7-357cac931a63,image,smoke]", "value": "", "classname": "tempest.api.volume.test_volumes_get.VolumesV2GetTest", "time": 16.721, "action": "passed", "message": "", "type": "", "regression": false}, {"successfix": false, "name": "setUpClass (tempest.scenario.test_server_multinode.TestServerMultinode)", "value": "Less than 2 compute nodes, skipping multinode tests.", "classname": "", "time": 0.0, "action": "skipped", "message": "", "type": "", "regression": false}, {"successfix": false, "name": "test_filter_router_tags[id-0c2e6d83-ae24-468d-8516-b7c5785bef0a,smoke]", "value": "", "classname": "neutron.tests.tempest.api.test_tag.TagFilterRouterTestJSON", "time": 2.531, "action": "passed", "message": "", "type": "", "regression": false}, {"successfix": false, "name": "test_volume_boot_pattern[compute,id-557cd2c2-4eb8-4dce-98be-f86765ff311b,image,smoke,volume]", "value": "", "classname": "tempest.scenario.test_volume_boot_pattern.TestVolumeBootPattern", "time": 158.856, "action": "passed", "message": "", "type": "", "regression": false}, {"successfix": false, "name": "test_network_tags[id-15c72621-1e2f-4e3b-9895-1af552272aa5,smoke]", "value": "", "classname": "neutron.tests.tempest.api.test_tag.TagNetworkTestJSON", "time": 5.626, "action": "passed", "message": "", "type": "", "regression": false}, {"successfix": false, "name": "test_volume_boot_pattern[compute,id-557cd2c2-4eb8-4dce-98be-f86765ff311b,image,smoke,volume]", "value": "", "classname": "tempest.scenario.test_volume_boot_pattern.TestVolumeBootPatternV2", "time": 139.931, "action": "passed", "message": "", "type": "", "regression": false}, {"successfix": false, "name": "setUpClass (mistral_tempest_tests.tests.api.v2.test_executions.ExecutionTestsV2)", "value": "Mistral support is required.", "classname": "", "time": 0.0, "action": "skipped", "message": "", "type": "", "regression": false}, {"successfix": false, "name": "setUpClass (mistral_tempest_tests.tests.api.v2.test_workbooks.WorkbookTestsV2)", "value": "Mistral support is required.", "classname": "", "time": 0.0, "action": "skipped", "message": "", "type": "", "regression": false}, {"successfix": false, "name": "setUpClass (inspector_tempest_plugin.tests.test_basic.InspectorSmokeTest)", "value": "Ironic is not enabled.", "classname": "", "time": 0.0, "action": "skipped", "message": "", "type": "", "regression": false}, {"successfix": false, "name": "test_filter_port_tags[id-fc626f6b-5fcd-4688-88bf-7bf13ac6f079,smoke]", "value": "", "classname": "neutron.tests.tempest.api.test_tag.TagFilterPortTestJSON", "time": 1.094, "action": "passed", "message": "", "type": "", "regression": false}, {"successfix": false, "name": "test_port_tags[id-89f16085-1987-4460-90de-e8aeb9d63e57,smoke]", "value": "", "classname": "neutron.tests.tempest.api.test_tag.TagPortTestJSON", "time": 3.966, "action": "passed", "message": "", "type": "", "regression": false}, {"successfix": false, "name": "test_router_tags[id-ad41caf1-c8b9-4708-83f6-a7d27e900a4c,smoke]", "value": "", "classname": "neutron.tests.tempest.api.test_tag.TagRouterTestJSON", "time": 5.273, "action": "passed", "message": "", "type": "", "regression": false}]	0
e3878b58-1222-4718-8de0-bc8a3cd606ff	2018-07-18 14:13:27.112531	2018-07-18 14:13:27.13802	Rally	16	16	0	0	0	1186390	c12208f2-9532-42dc-922a-794b72e2b0bf	5c67f325-d5c2-486f-b338-5da4261f5b15	[{"successfix": false, "name": "create_and_delete_ports", "value": "", "classname": "NeutronNetworks", "time": 70.72, "action": "passed", "message": "", "type": "", "regression": false}, {"successfix": false, "name": "create_and_delete_routers", "value": "", "classname": "NeutronNetworks", "time": 66.69, "action": "passed", "message": "", "type": "", "regression": false}, {"successfix": false, "name": "cinder_update_and_delete", "value": "", "classname": "Quotas", "time": 35.4, "action": "passed", "message": "", "type": "", "regression": false}, {"successfix": false, "name": "create_and_upload_volume_to_image", "value": "", "classname": "CinderVolumes", "time": 602.92, "action": "passed", "message": "", "type": "", "regression": false}, {"successfix": false, "name": "validate_glance", "value": "", "classname": "Authenticate", "time": 22.29, "action": "passed", "message": "", "type": "", "regression": false}, {"successfix": false, "name": "validate_neutron", "value": "", "classname": "Authenticate", "time": 21.39, "action": "passed", "message": "", "type": "", "regression": false}, {"successfix": false, "name": "keystone", "value": "", "classname": "Authenticate", "time": 16.26, "action": "passed", "message": "", "type": "", "regression": false}, {"successfix": false, "name": "create_and_delete_subnets", "value": "", "classname": "NeutronNetworks", "time": 26.35, "action": "passed", "message": "", "type": "", "regression": false}, {"successfix": false, "name": "nova_update_and_delete", "value": "", "classname": "Quotas", "time": 24.65, "action": "passed", "message": "", "type": "", "regression": false}, {"successfix": false, "name": "create_and_delete_networks", "value": "", "classname": "NeutronNetworks", "time": 17.92, "action": "passed", "message": "", "type": "", "regression": false}, {"successfix": false, "name": "create_delete_user", "value": "", "classname": "KeystoneBasic", "time": 20.56, "action": "passed", "message": "", "type": "", "regression": false}, {"successfix": false, "name": "create_and_delete_volume", "value": "", "classname": "CinderVolumes", "time": 146.93, "action": "passed", "message": "", "type": "", "regression": false}, {"successfix": false, "name": "create_update_and_delete_tenant", "value": "", "classname": "KeystoneBasic", "time": 21.23, "action": "passed", "message": "", "type": "", "regression": false}, {"successfix": false, "name": "validate_nova", "value": "", "classname": "Authenticate", "time": 18.35, "action": "passed", "message": "", "type": "", "regression": false}, {"successfix": false, "name": "create_and_extend_volume", "value": "", "classname": "CinderVolumes", "time": 54.1, "action": "passed", "message": "", "type": "", "regression": false}, {"successfix": false, "name": "validate_cinder", "value": "", "classname": "Authenticate", "time": 20.63, "action": "passed", "message": "", "type": "", "regression": false}]	0
71900ee7-58e0-4c3e-a308-264c09e2066a	2018-07-18 14:13:28.316532	2018-07-18 14:13:28.341977	Rally	16	15	0	1	0	1196390	024e5e39-b694-4045-9f9f-150c18ddb440	77409c2a-fa01-4721-a36c-b7f14bfc8a9a	[{"successfix": false, "name": "create_and_delete_ports", "value": "regression failure", "classname": "NeutronNetworks", "time": 80.72, "action": "failure", "message": "", "type": "", "regression": true}, {"successfix": false, "name": "create_and_delete_routers", "value": "", "classname": "NeutronNetworks", "time": 66.69, "action": "passed", "message": "", "type": "", "regression": false}, {"successfix": false, "name": "cinder_update_and_delete", "value": "", "classname": "Quotas", "time": 35.4, "action": "passed", "message": "", "type": "", "regression": false}, {"successfix": false, "name": "create_and_upload_volume_to_image", "value": "", "classname": "CinderVolumes", "time": 602.92, "action": "passed", "message": "", "type": "", "regression": false}, {"successfix": false, "name": "validate_glance", "value": "", "classname": "Authenticate", "time": 22.29, "action": "passed", "message": "", "type": "", "regression": false}, {"successfix": false, "name": "validate_neutron", "value": "", "classname": "Authenticate", "time": 21.39, "action": "passed", "message": "", "type": "", "regression": false}, {"successfix": false, "name": "keystone", "value": "", "classname": "Authenticate", "time": 16.26, "action": "passed", "message": "", "type": "", "regression": false}, {"successfix": false, "name": "create_and_delete_subnets", "value": "", "classname": "NeutronNetworks", "time": 26.35, "action": "passed", "message": "", "type": "", "regression": false}, {"successfix": false, "name": "nova_update_and_delete", "value": "", "classname": "Quotas", "time": 24.65, "action": "passed", "message": "", "type": "", "regression": false}, {"successfix": false, "name": "create_and_delete_networks", "value": "", "classname": "NeutronNetworks", "time": 17.92, "action": "passed", "message": "", "type": "", "regression": false}, {"successfix": false, "name": "create_delete_user", "value": "", "classname": "KeystoneBasic", "time": 20.56, "action": "passed", "message": "", "type": "", "regression": false}, {"successfix": false, "name": "create_and_delete_volume", "value": "", "classname": "CinderVolumes", "time": 146.93, "action": "passed", "message": "", "type": "", "regression": false}, {"successfix": false, "name": "create_update_and_delete_tenant", "value": "", "classname": "KeystoneBasic", "time": 21.23, "action": "passed", "message": "", "type": "", "regression": false}, {"successfix": false, "name": "validate_nova", "value": "", "classname": "Authenticate", "time": 18.35, "action": "passed", "message": "", "type": "", "regression": false}, {"successfix": false, "name": "create_and_extend_volume", "value": "", "classname": "CinderVolumes", "time": 54.1, "action": "passed", "message": "", "type": "", "regression": false}, {"successfix": false, "name": "validate_cinder", "value": "", "classname": "Authenticate", "time": 20.63, "action": "passed", "message": "", "type": "", "regression": false}]	1
\.


--
-- Data for Name: topic_tests; Type: TABLE DATA; Schema: public; Owner: dci
--

COPY topic_tests (topic_id, test_id) FROM stdin;
\.


--
-- Data for Name: topics; Type: TABLE DATA; Schema: public; Owner: dci
--

COPY topics (id, created_at, updated_at, etag, name, label, component_types, product_id, state, data, next_topic_id) FROM stdin;
04ee3d7a-9335-49e9-bc42-d68a9a053263	2018-07-18 14:12:46.627701	2018-07-18 14:12:46.627701	a19060e4f2a9bf31a153d40164f85ec0	OSP12	\N	["puddle"]	38ce41eb-557a-46a2-9204-531b3dcac402	active	{}	\N
2bc8911f-6bac-4d85-85c7-5654b65d4acb	2018-07-18 14:12:47.10932	2018-07-18 14:12:47.10932	3680659ec7b391ee1f9c67cd0adbb74d	OSP11	\N	["puddle"]	38ce41eb-557a-46a2-9204-531b3dcac402	active	{}	04ee3d7a-9335-49e9-bc42-d68a9a053263
9a73cedf-8a9a-4a31-a09a-4c8a6d46e7a1	2018-07-18 14:12:47.579161	2018-07-18 14:12:47.579161	12af6b9900b3f0cd3f7f9d43e5ed4623	OSP10	\N	["puddle"]	38ce41eb-557a-46a2-9204-531b3dcac402	active	{}	2bc8911f-6bac-4d85-85c7-5654b65d4acb
4b3540d6-234f-4435-954b-6bb9cdbf9a5e	2018-07-18 14:12:48.047405	2018-07-18 14:12:48.047405	7165ad481e9b51a3d34cb2b37d7f8b66	ansible-devel	\N	["snapshot_ansible"]	c22ecabf-f720-4e86-a380-07996743f770	active	{}	\N
0c38dfa5-6e7a-454d-9902-e02802594076	2018-07-18 14:12:48.53836	2018-07-18 14:12:48.53836	8ef1b48974bf7b98004cc1aef9feff12	ansible-2.4	\N	["snapshot_ansible"]	c22ecabf-f720-4e86-a380-07996743f770	active	{}	4b3540d6-234f-4435-954b-6bb9cdbf9a5e
1267f96c-f064-41ce-9e9b-6e2e8ae43c4e	2018-07-18 14:12:49.028114	2018-07-18 14:12:49.028114	f86e637ca31d7230c66b10b7bd5ecfe9	RHEL-8	\N	["Compose"]	1d740465-84ad-48c4-a90f-c933c4c6be56	active	{}	\N
e73df03e-c57e-48b3-912d-2b61a552fc7e	2018-07-18 14:12:49.518923	2018-07-18 14:12:49.518923	47187e9f4e24020a90811f00c0fab18a	RHEL-7	\N	["Compose"]	1d740465-84ad-48c4-a90f-c933c4c6be56	active	{}	1267f96c-f064-41ce-9e9b-6e2e8ae43c4e
\.


--
-- Data for Name: topics_teams; Type: TABLE DATA; Schema: public; Owner: dci
--

COPY topics_teams (topic_id, team_id) FROM stdin;
1267f96c-f064-41ce-9e9b-6e2e8ae43c4e	1ae8125c-732b-41ba-843c-e3c0fea8e868
e73df03e-c57e-48b3-912d-2b61a552fc7e	1ae8125c-732b-41ba-843c-e3c0fea8e868
e73df03e-c57e-48b3-912d-2b61a552fc7e	fbda671c-003b-460a-8d14-ebff1aeecb45
0c38dfa5-6e7a-454d-9902-e02802594076	2132fcbc-15fa-45f0-b16f-77ce3a375fc6
0c38dfa5-6e7a-454d-9902-e02802594076	c8185d8a-0f5b-4d57-ae8e-43bcbde43c27
4b3540d6-234f-4435-954b-6bb9cdbf9a5e	c8185d8a-0f5b-4d57-ae8e-43bcbde43c27
9a73cedf-8a9a-4a31-a09a-4c8a6d46e7a1	01ed0891-d32d-47cd-bbdd-31c09201013c
9a73cedf-8a9a-4a31-a09a-4c8a6d46e7a1	8a3bd725-8ece-4acc-9199-afe6c51afecc
9a73cedf-8a9a-4a31-a09a-4c8a6d46e7a1	ba30a049-ac32-4ec4-9ebd-40d35d8ae4cd
2bc8911f-6bac-4d85-85c7-5654b65d4acb	8a3bd725-8ece-4acc-9199-afe6c51afecc
2bc8911f-6bac-4d85-85c7-5654b65d4acb	ba30a049-ac32-4ec4-9ebd-40d35d8ae4cd
04ee3d7a-9335-49e9-bc42-d68a9a053263	8a3bd725-8ece-4acc-9199-afe6c51afecc
04ee3d7a-9335-49e9-bc42-d68a9a053263	ba30a049-ac32-4ec4-9ebd-40d35d8ae4cd
\.


--
-- Data for Name: user_remotecis; Type: TABLE DATA; Schema: public; Owner: dci
--

COPY user_remotecis (user_id, remoteci_id) FROM stdin;
\.


--
-- Data for Name: users; Type: TABLE DATA; Schema: public; Owner: dci
--

COPY users (id, created_at, updated_at, etag, name, sso_username, fullname, email, password, timezone, role_id, team_id, state) FROM stdin;
4b322f75-9ee8-421e-9197-1603cc26c6d3	2018-07-18 14:12:05.96449	2018-07-18 14:12:05.964499	72c3bb292dab64a66c8f467b104dfa73	admin	\N	Admin	admin@example.org	$6$rounds=656000$sEulN7OKJbpNVHhF$4filRsB2CG/bpoR7KskfFq/RAvuHSYroKEBsF2IGJ3Yppx8Vn7BHRs4c1ZJ4p6.o6Fo99WE7kmPqYpw20SLKD/	UTC	31562ebf-d8bc-48f6-bea8-a1719ead8d48	9d8f0aa9-3032-4906-94e6-13717f9e4929	active
dff08e3f-10d1-474c-aa61-87083bf3f590	2018-07-18 14:12:35.111283	2018-07-18 14:12:35.111283	e50f106a4a21ba5e949e124798abce11	ansible_po	\N	Ansible PO	ansible_po@example.org	$6$rounds=656000$GRmqHt25cj.DIeXQ$BWBf8vHXHoMJ2DneCRoD4iCfneAQ53Er37oDQ.lsrrEU99OXANm.W0KYTBmRGAFzxX/1Xq9hCeZUMpwogt.yp0	UTC	1e4a0b6b-58d5-4230-8c1a-6212f82ae3fb	c8185d8a-0f5b-4d57-ae8e-43bcbde43c27	active
1cac9ad6-aeab-44f2-ba43-6c694d6d8884	2018-07-18 14:12:36.048961	2018-07-18 14:12:36.048961	b2ab94a87bf58343cf7279c69be7dfb9	openstack_po	\N	OpenStack PO	openstack_po@example.org	$6$rounds=656000$vThLFXjd/M0GVfO.$.j1xFkipHuZHxOsENR9g3bIG6kD42ETWuwMKcRUJTSVeU3F1uyqAxK4Ucy4w3Opm1ynyIK9pcemaynxiuhq8Z.	UTC	1e4a0b6b-58d5-4230-8c1a-6212f82ae3fb	ba30a049-ac32-4ec4-9ebd-40d35d8ae4cd	active
d0d0b845-ecd8-4578-b28a-60d7b2453b66	2018-07-18 14:12:36.984871	2018-07-18 14:12:36.984871	ce8fb3813449496f94f9881a688d788e	rhel_po	\N	RHEL PO	rhel_po@example.org	$6$rounds=656000$Ebr6nFTOFoAtKMph$ZX/s1iRgv6cRMGIYQKkes7WLBMj10XJwKBddilDvY39F8.PxK3s7IEc7pbLHmyMOShpRry4nXMxr78RrYZg2M.	UTC	1e4a0b6b-58d5-4230-8c1a-6212f82ae3fb	1ae8125c-732b-41ba-843c-e3c0fea8e868	active
75797422-8111-4b4f-aafc-a6bbfe893f40	2018-07-18 14:12:37.91139	2018-07-18 14:12:37.91139	eef9cc34eb483b49c8fa87adef05ce4b	admin_cisco	\N	Admin Cisco	admin_cisco@example.org	$6$rounds=656000$lI1a41J8iZtDisbm$aGjFPpFClochU9blCiVRf.GnQDZiwlrqmY8XacqFeD.nG2ZIUtBOllvUw.DRbA4lMcC2Bm4eVtqVoj8UJsg2Z.	UTC	5d02f2e9-5007-485f-9d47-c2c64388231d	2132fcbc-15fa-45f0-b16f-77ce3a375fc6	active
4c9ac327-4ebe-4706-9ab2-a603c9155aa0	2018-07-18 14:12:38.818221	2018-07-18 14:12:38.818221	7d51732f53a0c2fe71961fec8340f84a	admin_hp	\N	Admin HP	admin_hp@example.org	$6$rounds=656000$TIvuzRs6eBRJe3Tv$Q5VgQV6xDGMAhEBkPcljaRMRBV/mtmWD.BYVSlxYH14JfgqpoNYV73kV/VrEvcWumI/pX6dlYJCyL6CnCHeI41	UTC	5d02f2e9-5007-485f-9d47-c2c64388231d	01ed0891-d32d-47cd-bbdd-31c09201013c	active
9361e6ce-425c-494f-b9dd-c7ed3ec6189b	2018-07-18 14:12:39.742046	2018-07-18 14:12:39.742046	ae11b32e03a0f41b20e28bdaec3d40ce	admin_dell	\N	Admin Dell	admin_dell@example.org	$6$rounds=656000$tV2.bUUhMSnAQmWf$PO78zH6Ndf6xg5bF55OSEYkn1MZ/wjM/0QckBYbXtA3GFy7jfp1k5oyzkvLeiai5ltA8l.3UYF8bIBrQuhlzf1	UTC	5d02f2e9-5007-485f-9d47-c2c64388231d	8a3bd725-8ece-4acc-9199-afe6c51afecc	active
0f9ab80e-953f-4563-ae5b-588e9cbbaddf	2018-07-18 14:12:40.654187	2018-07-18 14:12:40.654187	687783032a696d54fcf46507043246a1	user_cisco	\N	User Cisco	user_cisco@example.org	$6$rounds=656000$ezOW3lxmhiB3XEsf$vbxyeC9IUi.2jwzjVahVyG6FsH9UkqXdm4fX.759Fp4a3JJDgaHAHHbyf9qxjq.oIhMErNbL1zRAPvcZDZclo1	UTC	d825ecec-f909-47e7-a6e7-1dc78fe794c4	2132fcbc-15fa-45f0-b16f-77ce3a375fc6	active
ddf60750-97e0-425b-a404-893f46da7ea4	2018-07-18 14:12:41.576785	2018-07-18 14:12:41.576785	9701df8a558e3e6a29d474b39dd0dda8	user_hp	\N	User HP	user_hp@example.org	$6$rounds=656000$tgIXhm4aBeOiRcAD$e6NEmVniLMp8CIJl2u7YAJOASUzw0fsblt99aVcRDCF/x8Z4vTHYbmD0v43hbRWOTdnrjRvXdvyAUjbYaI/wk1	UTC	d825ecec-f909-47e7-a6e7-1dc78fe794c4	01ed0891-d32d-47cd-bbdd-31c09201013c	active
85805343-d494-422b-af9c-7e67b1a1671f	2018-07-18 14:12:42.483697	2018-07-18 14:12:42.483697	0eb5d592abee56f7ce7fe00ecd746fe8	user_dell	\N	User Dell	user_dell@example.org	$6$rounds=656000$A0ErAtUPTHFDZvlD$HMo7F/0USO5fDDRCsPAKZQzsIkAB.IpIKUKVAI3kRlnyRe38zp4ByD.O8T2bz2sD5DlMYDemMuFCovJI0l49q0	UTC	d825ecec-f909-47e7-a6e7-1dc78fe794c4	8a3bd725-8ece-4acc-9199-afe6c51afecc	active
0f9785a4-30a4-4822-9a10-5201d91964ba	2018-07-18 14:12:43.399355	2018-07-18 14:12:43.399355	5d07f56a41c627730a2cb09779046efe	admin_veritas	\N	Admin Veritas	admin_veritas@example.org	$6$rounds=656000$ibY4zOYxP0pPH6/B$T83zSuSxyrVVyRcazxGH1y491sadQTqJ5BMXurFchVM5jjpHRHHOJijytL6Edugwk4pZfb27grVYgPxZKTaS2/	UTC	5d02f2e9-5007-485f-9d47-c2c64388231d	fbda671c-003b-460a-8d14-ebff1aeecb45	active
776486c3-662a-463c-b6c6-d9c0d55de267	2018-07-18 14:12:44.283988	2018-07-18 14:12:44.283988	489fdcbc6f47ff43ee812972a6043f96	user_veritas	\N	User Veritas	user_veritas@example.org	$6$rounds=656000$gWvrnxsZHo40HSEW$7/.ediTewgGeI/9lasuQHKQFV1l.884V95xMDR2wGs6kByhCPG2yhbZKOxHyKUBoTTTq5TFumz7waV2BsUJwA1	UTC	d825ecec-f909-47e7-a6e7-1dc78fe794c4	fbda671c-003b-460a-8d14-ebff1aeecb45	active
\.


--
-- Name: alembic_version_pkc; Type: CONSTRAINT; Schema: public; Owner: dci; Tablespace: 
--

ALTER TABLE ONLY alembic_version
    ADD CONSTRAINT alembic_version_pkc PRIMARY KEY (version_num);


--
-- Name: component_files_pkey; Type: CONSTRAINT; Schema: public; Owner: dci; Tablespace: 
--

ALTER TABLE ONLY component_files
    ADD CONSTRAINT component_files_pkey PRIMARY KEY (id);


--
-- Name: components_issues_pkey; Type: CONSTRAINT; Schema: public; Owner: dci; Tablespace: 
--

ALTER TABLE ONLY components_issues
    ADD CONSTRAINT components_issues_pkey PRIMARY KEY (component_id, issue_id);


--
-- Name: components_pkey; Type: CONSTRAINT; Schema: public; Owner: dci; Tablespace: 
--

ALTER TABLE ONLY components
    ADD CONSTRAINT components_pkey PRIMARY KEY (id);


--
-- Name: counter_pkey; Type: CONSTRAINT; Schema: public; Owner: dci; Tablespace: 
--

ALTER TABLE ONLY counter
    ADD CONSTRAINT counter_pkey PRIMARY KEY (name);


--
-- Name: feeders_name_team_id_key; Type: CONSTRAINT; Schema: public; Owner: dci; Tablespace: 
--

ALTER TABLE ONLY feeders
    ADD CONSTRAINT feeders_name_team_id_key UNIQUE (name, team_id);


--
-- Name: feeders_pkey; Type: CONSTRAINT; Schema: public; Owner: dci; Tablespace: 
--

ALTER TABLE ONLY feeders
    ADD CONSTRAINT feeders_pkey PRIMARY KEY (id);


--
-- Name: files_pkey; Type: CONSTRAINT; Schema: public; Owner: dci; Tablespace: 
--

ALTER TABLE ONLY files
    ADD CONSTRAINT files_pkey PRIMARY KEY (id);


--
-- Name: issues_pkey; Type: CONSTRAINT; Schema: public; Owner: dci; Tablespace: 
--

ALTER TABLE ONLY issues
    ADD CONSTRAINT issues_pkey PRIMARY KEY (id);


--
-- Name: issues_url_key; Type: CONSTRAINT; Schema: public; Owner: dci; Tablespace: 
--

ALTER TABLE ONLY issues
    ADD CONSTRAINT issues_url_key UNIQUE (url);


--
-- Name: jobs_components_pkey; Type: CONSTRAINT; Schema: public; Owner: dci; Tablespace: 
--

ALTER TABLE ONLY jobs_components
    ADD CONSTRAINT jobs_components_pkey PRIMARY KEY (job_id, component_id);


--
-- Name: jobs_events_pkey; Type: CONSTRAINT; Schema: public; Owner: dci; Tablespace: 
--

ALTER TABLE ONLY jobs_events
    ADD CONSTRAINT jobs_events_pkey PRIMARY KEY (id);


--
-- Name: jobs_issues_pkey; Type: CONSTRAINT; Schema: public; Owner: dci; Tablespace: 
--

ALTER TABLE ONLY jobs_issues
    ADD CONSTRAINT jobs_issues_pkey PRIMARY KEY (job_id, issue_id);


--
-- Name: jobs_pkey; Type: CONSTRAINT; Schema: public; Owner: dci; Tablespace: 
--

ALTER TABLE ONLY jobs
    ADD CONSTRAINT jobs_pkey PRIMARY KEY (id);


--
-- Name: jobstates_pkey; Type: CONSTRAINT; Schema: public; Owner: dci; Tablespace: 
--

ALTER TABLE ONLY jobstates
    ADD CONSTRAINT jobstates_pkey PRIMARY KEY (id);


--
-- Name: logs_pkey; Type: CONSTRAINT; Schema: public; Owner: dci; Tablespace: 
--

ALTER TABLE ONLY logs
    ADD CONSTRAINT logs_pkey PRIMARY KEY (id);


--
-- Name: metas_pkey; Type: CONSTRAINT; Schema: public; Owner: dci; Tablespace: 
--

ALTER TABLE ONLY metas
    ADD CONSTRAINT metas_pkey PRIMARY KEY (id);


--
-- Name: permissions_label_key; Type: CONSTRAINT; Schema: public; Owner: dci; Tablespace: 
--

ALTER TABLE ONLY permissions
    ADD CONSTRAINT permissions_label_key UNIQUE (label);


--
-- Name: permissions_pkey; Type: CONSTRAINT; Schema: public; Owner: dci; Tablespace: 
--

ALTER TABLE ONLY permissions
    ADD CONSTRAINT permissions_pkey PRIMARY KEY (id);


--
-- Name: products_label_key; Type: CONSTRAINT; Schema: public; Owner: dci; Tablespace: 
--

ALTER TABLE ONLY products
    ADD CONSTRAINT products_label_key UNIQUE (label);


--
-- Name: products_pkey; Type: CONSTRAINT; Schema: public; Owner: dci; Tablespace: 
--

ALTER TABLE ONLY products
    ADD CONSTRAINT products_pkey PRIMARY KEY (id);


--
-- Name: rconfigurations_pkey; Type: CONSTRAINT; Schema: public; Owner: dci; Tablespace: 
--

ALTER TABLE ONLY rconfigurations
    ADD CONSTRAINT rconfigurations_pkey PRIMARY KEY (id);


--
-- Name: remoteci_tests_pkey; Type: CONSTRAINT; Schema: public; Owner: dci; Tablespace: 
--

ALTER TABLE ONLY remoteci_tests
    ADD CONSTRAINT remoteci_tests_pkey PRIMARY KEY (remoteci_id, test_id);


--
-- Name: remotecis_name_team_id_key; Type: CONSTRAINT; Schema: public; Owner: dci; Tablespace: 
--

ALTER TABLE ONLY remotecis
    ADD CONSTRAINT remotecis_name_team_id_key UNIQUE (name, team_id);


--
-- Name: remotecis_pkey; Type: CONSTRAINT; Schema: public; Owner: dci; Tablespace: 
--

ALTER TABLE ONLY remotecis
    ADD CONSTRAINT remotecis_pkey PRIMARY KEY (id);


--
-- Name: remotecis_rconfigurations_pkey; Type: CONSTRAINT; Schema: public; Owner: dci; Tablespace: 
--

ALTER TABLE ONLY remotecis_rconfigurations
    ADD CONSTRAINT remotecis_rconfigurations_pkey PRIMARY KEY (remoteci_id, rconfiguration_id);


--
-- Name: roles_label_key; Type: CONSTRAINT; Schema: public; Owner: dci; Tablespace: 
--

ALTER TABLE ONLY roles
    ADD CONSTRAINT roles_label_key UNIQUE (label);


--
-- Name: roles_permissions_pkey; Type: CONSTRAINT; Schema: public; Owner: dci; Tablespace: 
--

ALTER TABLE ONLY roles_permissions
    ADD CONSTRAINT roles_permissions_pkey PRIMARY KEY (role_id, permission_id);


--
-- Name: roles_pkey; Type: CONSTRAINT; Schema: public; Owner: dci; Tablespace: 
--

ALTER TABLE ONLY roles
    ADD CONSTRAINT roles_pkey PRIMARY KEY (id);


--
-- Name: teams_name_parent_id_key; Type: CONSTRAINT; Schema: public; Owner: dci; Tablespace: 
--

ALTER TABLE ONLY teams
    ADD CONSTRAINT teams_name_parent_id_key UNIQUE (name, parent_id);


--
-- Name: teams_pkey; Type: CONSTRAINT; Schema: public; Owner: dci; Tablespace: 
--

ALTER TABLE ONLY teams
    ADD CONSTRAINT teams_pkey PRIMARY KEY (id);


--
-- Name: tests_name_key; Type: CONSTRAINT; Schema: public; Owner: dci; Tablespace: 
--

ALTER TABLE ONLY tests
    ADD CONSTRAINT tests_name_key UNIQUE (name);


--
-- Name: tests_pkey; Type: CONSTRAINT; Schema: public; Owner: dci; Tablespace: 
--

ALTER TABLE ONLY tests
    ADD CONSTRAINT tests_pkey PRIMARY KEY (id);


--
-- Name: tests_results_pkey; Type: CONSTRAINT; Schema: public; Owner: dci; Tablespace: 
--

ALTER TABLE ONLY tests_results
    ADD CONSTRAINT tests_results_pkey PRIMARY KEY (id);


--
-- Name: topic_tests_pkey; Type: CONSTRAINT; Schema: public; Owner: dci; Tablespace: 
--

ALTER TABLE ONLY topic_tests
    ADD CONSTRAINT topic_tests_pkey PRIMARY KEY (topic_id, test_id);


--
-- Name: topics_name_key; Type: CONSTRAINT; Schema: public; Owner: dci; Tablespace: 
--

ALTER TABLE ONLY topics
    ADD CONSTRAINT topics_name_key UNIQUE (name);


--
-- Name: topics_pkey; Type: CONSTRAINT; Schema: public; Owner: dci; Tablespace: 
--

ALTER TABLE ONLY topics
    ADD CONSTRAINT topics_pkey PRIMARY KEY (id);


--
-- Name: topics_teams_pkey; Type: CONSTRAINT; Schema: public; Owner: dci; Tablespace: 
--

ALTER TABLE ONLY topics_teams
    ADD CONSTRAINT topics_teams_pkey PRIMARY KEY (topic_id, team_id);


--
-- Name: user_remotecis_pkey; Type: CONSTRAINT; Schema: public; Owner: dci; Tablespace: 
--

ALTER TABLE ONLY user_remotecis
    ADD CONSTRAINT user_remotecis_pkey PRIMARY KEY (user_id, remoteci_id);


--
-- Name: users_email_key; Type: CONSTRAINT; Schema: public; Owner: dci; Tablespace: 
--

ALTER TABLE ONLY users
    ADD CONSTRAINT users_email_key UNIQUE (email);


--
-- Name: users_name_key; Type: CONSTRAINT; Schema: public; Owner: dci; Tablespace: 
--

ALTER TABLE ONLY users
    ADD CONSTRAINT users_name_key UNIQUE (name);


--
-- Name: users_pkey; Type: CONSTRAINT; Schema: public; Owner: dci; Tablespace: 
--

ALTER TABLE ONLY users
    ADD CONSTRAINT users_pkey PRIMARY KEY (id);


--
-- Name: users_sso_username_key; Type: CONSTRAINT; Schema: public; Owner: dci; Tablespace: 
--

ALTER TABLE ONLY users
    ADD CONSTRAINT users_sso_username_key UNIQUE (sso_username);


--
-- Name: active_components_name_topic_id_key; Type: INDEX; Schema: public; Owner: dci; Tablespace: 
--

CREATE UNIQUE INDEX active_components_name_topic_id_key ON components USING btree (name, topic_id) WHERE (state = 'active'::states);


--
-- Name: component_files_component_id_idx; Type: INDEX; Schema: public; Owner: dci; Tablespace: 
--

CREATE INDEX component_files_component_id_idx ON component_files USING btree (component_id);


--
-- Name: components_issues_user_id_idx; Type: INDEX; Schema: public; Owner: dci; Tablespace: 
--

CREATE INDEX components_issues_user_id_idx ON components_issues USING btree (user_id);


--
-- Name: components_topic_id_idx; Type: INDEX; Schema: public; Owner: dci; Tablespace: 
--

CREATE INDEX components_topic_id_idx ON components USING btree (topic_id);


--
-- Name: feeders_team_id_idx; Type: INDEX; Schema: public; Owner: dci; Tablespace: 
--

CREATE INDEX feeders_team_id_idx ON feeders USING btree (team_id);


--
-- Name: files_job_id_idx; Type: INDEX; Schema: public; Owner: dci; Tablespace: 
--

CREATE INDEX files_job_id_idx ON files USING btree (job_id);


--
-- Name: files_jobstate_id_idx; Type: INDEX; Schema: public; Owner: dci; Tablespace: 
--

CREATE INDEX files_jobstate_id_idx ON files USING btree (jobstate_id);


--
-- Name: files_team_id_idx; Type: INDEX; Schema: public; Owner: dci; Tablespace: 
--

CREATE INDEX files_team_id_idx ON files USING btree (team_id);


--
-- Name: jobs_events_job_id_idx; Type: INDEX; Schema: public; Owner: dci; Tablespace: 
--

CREATE INDEX jobs_events_job_id_idx ON jobs_events USING btree (job_id);


--
-- Name: jobs_issues_user_id_idx; Type: INDEX; Schema: public; Owner: dci; Tablespace: 
--

CREATE INDEX jobs_issues_user_id_idx ON jobs_issues USING btree (user_id);


--
-- Name: jobs_previous_job_id_idx; Type: INDEX; Schema: public; Owner: dci; Tablespace: 
--

CREATE INDEX jobs_previous_job_id_idx ON jobs USING btree (previous_job_id);


--
-- Name: jobs_rconfiguration_id_idx; Type: INDEX; Schema: public; Owner: dci; Tablespace: 
--

CREATE INDEX jobs_rconfiguration_id_idx ON jobs USING btree (rconfiguration_id);


--
-- Name: jobs_remoteci_id_idx; Type: INDEX; Schema: public; Owner: dci; Tablespace: 
--

CREATE INDEX jobs_remoteci_id_idx ON jobs USING btree (remoteci_id);


--
-- Name: jobs_team_id_idx; Type: INDEX; Schema: public; Owner: dci; Tablespace: 
--

CREATE INDEX jobs_team_id_idx ON jobs USING btree (team_id);


--
-- Name: jobs_topic_id_idx; Type: INDEX; Schema: public; Owner: dci; Tablespace: 
--

CREATE INDEX jobs_topic_id_idx ON jobs USING btree (topic_id);


--
-- Name: jobs_update_previous_job_id_idx; Type: INDEX; Schema: public; Owner: dci; Tablespace: 
--

CREATE INDEX jobs_update_previous_job_id_idx ON jobs USING btree (update_previous_job_id);


--
-- Name: jobstates_job_id_idx; Type: INDEX; Schema: public; Owner: dci; Tablespace: 
--

CREATE INDEX jobstates_job_id_idx ON jobstates USING btree (job_id);


--
-- Name: jobstates_team_id_idx; Type: INDEX; Schema: public; Owner: dci; Tablespace: 
--

CREATE INDEX jobstates_team_id_idx ON jobstates USING btree (team_id);


--
-- Name: logs_team_id_idx; Type: INDEX; Schema: public; Owner: dci; Tablespace: 
--

CREATE INDEX logs_team_id_idx ON logs USING btree (team_id);


--
-- Name: logs_user_id_idx; Type: INDEX; Schema: public; Owner: dci; Tablespace: 
--

CREATE INDEX logs_user_id_idx ON logs USING btree (user_id);


--
-- Name: metas_job_id_idx; Type: INDEX; Schema: public; Owner: dci; Tablespace: 
--

CREATE INDEX metas_job_id_idx ON metas USING btree (job_id);


--
-- Name: rconfigurations_topic_id_idx; Type: INDEX; Schema: public; Owner: dci; Tablespace: 
--

CREATE INDEX rconfigurations_topic_id_idx ON rconfigurations USING btree (topic_id);


--
-- Name: remotecis_team_id_idx; Type: INDEX; Schema: public; Owner: dci; Tablespace: 
--

CREATE INDEX remotecis_team_id_idx ON remotecis USING btree (team_id);


--
-- Name: tests_results_file_id_idx; Type: INDEX; Schema: public; Owner: dci; Tablespace: 
--

CREATE INDEX tests_results_file_id_idx ON tests_results USING btree (file_id);


--
-- Name: tests_results_job_id_idx; Type: INDEX; Schema: public; Owner: dci; Tablespace: 
--

CREATE INDEX tests_results_job_id_idx ON tests_results USING btree (job_id);


--
-- Name: tests_team_id_idx; Type: INDEX; Schema: public; Owner: dci; Tablespace: 
--

CREATE INDEX tests_team_id_idx ON tests USING btree (team_id);


--
-- Name: topics_next_topic_id_idx; Type: INDEX; Schema: public; Owner: dci; Tablespace: 
--

CREATE INDEX topics_next_topic_id_idx ON topics USING btree (next_topic_id);


--
-- Name: topics_product_id_idx; Type: INDEX; Schema: public; Owner: dci; Tablespace: 
--

CREATE INDEX topics_product_id_idx ON topics USING btree (product_id);


--
-- Name: users_team_id_idx; Type: INDEX; Schema: public; Owner: dci; Tablespace: 
--

CREATE INDEX users_team_id_idx ON users USING btree (team_id);


--
-- Name: component_files_component_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: dci
--

ALTER TABLE ONLY component_files
    ADD CONSTRAINT component_files_component_id_fkey FOREIGN KEY (component_id) REFERENCES components(id) ON DELETE CASCADE;


--
-- Name: components_issues_component_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: dci
--

ALTER TABLE ONLY components_issues
    ADD CONSTRAINT components_issues_component_id_fkey FOREIGN KEY (component_id) REFERENCES components(id) ON DELETE CASCADE;


--
-- Name: components_issues_issue_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: dci
--

ALTER TABLE ONLY components_issues
    ADD CONSTRAINT components_issues_issue_id_fkey FOREIGN KEY (issue_id) REFERENCES issues(id) ON DELETE CASCADE;


--
-- Name: components_issues_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: dci
--

ALTER TABLE ONLY components_issues
    ADD CONSTRAINT components_issues_user_id_fkey FOREIGN KEY (user_id) REFERENCES users(id);


--
-- Name: components_topic_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: dci
--

ALTER TABLE ONLY components
    ADD CONSTRAINT components_topic_id_fkey FOREIGN KEY (topic_id) REFERENCES topics(id) ON DELETE CASCADE;


--
-- Name: feeders_role_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: dci
--

ALTER TABLE ONLY feeders
    ADD CONSTRAINT feeders_role_id_fkey FOREIGN KEY (role_id) REFERENCES roles(id) ON DELETE SET NULL;


--
-- Name: feeders_team_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: dci
--

ALTER TABLE ONLY feeders
    ADD CONSTRAINT feeders_team_id_fkey FOREIGN KEY (team_id) REFERENCES teams(id) ON DELETE CASCADE;


--
-- Name: files_job_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: dci
--

ALTER TABLE ONLY files
    ADD CONSTRAINT files_job_id_fkey FOREIGN KEY (job_id) REFERENCES jobs(id) ON DELETE CASCADE;


--
-- Name: files_jobstate_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: dci
--

ALTER TABLE ONLY files
    ADD CONSTRAINT files_jobstate_id_fkey FOREIGN KEY (jobstate_id) REFERENCES jobstates(id) ON DELETE CASCADE;


--
-- Name: files_team_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: dci
--

ALTER TABLE ONLY files
    ADD CONSTRAINT files_team_id_fkey FOREIGN KEY (team_id) REFERENCES teams(id) ON DELETE CASCADE;


--
-- Name: files_test_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: dci
--

ALTER TABLE ONLY files
    ADD CONSTRAINT files_test_id_fkey FOREIGN KEY (test_id) REFERENCES tests(id) ON DELETE CASCADE;


--
-- Name: jobs_components_component_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: dci
--

ALTER TABLE ONLY jobs_components
    ADD CONSTRAINT jobs_components_component_id_fkey FOREIGN KEY (component_id) REFERENCES components(id) ON DELETE CASCADE;


--
-- Name: jobs_components_job_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: dci
--

ALTER TABLE ONLY jobs_components
    ADD CONSTRAINT jobs_components_job_id_fkey FOREIGN KEY (job_id) REFERENCES jobs(id) ON DELETE CASCADE;


--
-- Name: jobs_issues_issue_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: dci
--

ALTER TABLE ONLY jobs_issues
    ADD CONSTRAINT jobs_issues_issue_id_fkey FOREIGN KEY (issue_id) REFERENCES issues(id) ON DELETE CASCADE;


--
-- Name: jobs_issues_job_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: dci
--

ALTER TABLE ONLY jobs_issues
    ADD CONSTRAINT jobs_issues_job_id_fkey FOREIGN KEY (job_id) REFERENCES jobs(id) ON DELETE CASCADE;


--
-- Name: jobs_issues_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: dci
--

ALTER TABLE ONLY jobs_issues
    ADD CONSTRAINT jobs_issues_user_id_fkey FOREIGN KEY (user_id) REFERENCES users(id);


--
-- Name: jobs_previous_job_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: dci
--

ALTER TABLE ONLY jobs
    ADD CONSTRAINT jobs_previous_job_id_fkey FOREIGN KEY (previous_job_id) REFERENCES jobs(id);


--
-- Name: jobs_rconfiguration_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: dci
--

ALTER TABLE ONLY jobs
    ADD CONSTRAINT jobs_rconfiguration_id_fkey FOREIGN KEY (rconfiguration_id) REFERENCES rconfigurations(id);


--
-- Name: jobs_remoteci_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: dci
--

ALTER TABLE ONLY jobs
    ADD CONSTRAINT jobs_remoteci_id_fkey FOREIGN KEY (remoteci_id) REFERENCES remotecis(id) ON DELETE CASCADE;


--
-- Name: jobs_team_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: dci
--

ALTER TABLE ONLY jobs
    ADD CONSTRAINT jobs_team_id_fkey FOREIGN KEY (team_id) REFERENCES teams(id) ON DELETE CASCADE;


--
-- Name: jobs_topic_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: dci
--

ALTER TABLE ONLY jobs
    ADD CONSTRAINT jobs_topic_id_fkey FOREIGN KEY (topic_id) REFERENCES topics(id) ON DELETE CASCADE;


--
-- Name: jobs_update_previous_job_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: dci
--

ALTER TABLE ONLY jobs
    ADD CONSTRAINT jobs_update_previous_job_id_fkey FOREIGN KEY (update_previous_job_id) REFERENCES jobs(id);


--
-- Name: jobstates_job_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: dci
--

ALTER TABLE ONLY jobstates
    ADD CONSTRAINT jobstates_job_id_fkey FOREIGN KEY (job_id) REFERENCES jobs(id) ON DELETE CASCADE;


--
-- Name: jobstates_team_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: dci
--

ALTER TABLE ONLY jobstates
    ADD CONSTRAINT jobstates_team_id_fkey FOREIGN KEY (team_id) REFERENCES teams(id) ON DELETE CASCADE;


--
-- Name: logs_team_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: dci
--

ALTER TABLE ONLY logs
    ADD CONSTRAINT logs_team_id_fkey FOREIGN KEY (team_id) REFERENCES teams(id) ON DELETE CASCADE;


--
-- Name: metas_job_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: dci
--

ALTER TABLE ONLY metas
    ADD CONSTRAINT metas_job_id_fkey FOREIGN KEY (job_id) REFERENCES jobs(id) ON DELETE CASCADE;


--
-- Name: products_team_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: dci
--

ALTER TABLE ONLY products
    ADD CONSTRAINT products_team_id_fkey FOREIGN KEY (team_id) REFERENCES teams(id) ON DELETE SET NULL;


--
-- Name: rconfigurations_topic_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: dci
--

ALTER TABLE ONLY rconfigurations
    ADD CONSTRAINT rconfigurations_topic_id_fkey FOREIGN KEY (topic_id) REFERENCES topics(id) ON DELETE CASCADE;


--
-- Name: remoteci_tests_remoteci_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: dci
--

ALTER TABLE ONLY remoteci_tests
    ADD CONSTRAINT remoteci_tests_remoteci_id_fkey FOREIGN KEY (remoteci_id) REFERENCES remotecis(id) ON DELETE CASCADE;


--
-- Name: remoteci_tests_test_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: dci
--

ALTER TABLE ONLY remoteci_tests
    ADD CONSTRAINT remoteci_tests_test_id_fkey FOREIGN KEY (test_id) REFERENCES tests(id) ON DELETE CASCADE;


--
-- Name: remotecis_rconfigurations_rconfiguration_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: dci
--

ALTER TABLE ONLY remotecis_rconfigurations
    ADD CONSTRAINT remotecis_rconfigurations_rconfiguration_id_fkey FOREIGN KEY (rconfiguration_id) REFERENCES rconfigurations(id) ON DELETE CASCADE;


--
-- Name: remotecis_rconfigurations_remoteci_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: dci
--

ALTER TABLE ONLY remotecis_rconfigurations
    ADD CONSTRAINT remotecis_rconfigurations_remoteci_id_fkey FOREIGN KEY (remoteci_id) REFERENCES remotecis(id) ON DELETE CASCADE;


--
-- Name: remotecis_role_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: dci
--

ALTER TABLE ONLY remotecis
    ADD CONSTRAINT remotecis_role_id_fkey FOREIGN KEY (role_id) REFERENCES roles(id) ON DELETE SET NULL;


--
-- Name: remotecis_team_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: dci
--

ALTER TABLE ONLY remotecis
    ADD CONSTRAINT remotecis_team_id_fkey FOREIGN KEY (team_id) REFERENCES teams(id) ON DELETE CASCADE;


--
-- Name: roles_permissions_permission_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: dci
--

ALTER TABLE ONLY roles_permissions
    ADD CONSTRAINT roles_permissions_permission_id_fkey FOREIGN KEY (permission_id) REFERENCES permissions(id) ON DELETE CASCADE;


--
-- Name: roles_permissions_role_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: dci
--

ALTER TABLE ONLY roles_permissions
    ADD CONSTRAINT roles_permissions_role_id_fkey FOREIGN KEY (role_id) REFERENCES roles(id) ON DELETE CASCADE;


--
-- Name: teams_parent_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: dci
--

ALTER TABLE ONLY teams
    ADD CONSTRAINT teams_parent_id_fkey FOREIGN KEY (parent_id) REFERENCES teams(id) ON DELETE SET NULL;


--
-- Name: tests_results_file_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: dci
--

ALTER TABLE ONLY tests_results
    ADD CONSTRAINT tests_results_file_id_fkey FOREIGN KEY (file_id) REFERENCES files(id) ON DELETE CASCADE;


--
-- Name: tests_results_job_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: dci
--

ALTER TABLE ONLY tests_results
    ADD CONSTRAINT tests_results_job_id_fkey FOREIGN KEY (job_id) REFERENCES jobs(id) ON DELETE CASCADE;


--
-- Name: tests_team_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: dci
--

ALTER TABLE ONLY tests
    ADD CONSTRAINT tests_team_id_fkey FOREIGN KEY (team_id) REFERENCES teams(id) ON DELETE CASCADE;


--
-- Name: topic_tests_test_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: dci
--

ALTER TABLE ONLY topic_tests
    ADD CONSTRAINT topic_tests_test_id_fkey FOREIGN KEY (test_id) REFERENCES tests(id) ON DELETE CASCADE;


--
-- Name: topic_tests_topic_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: dci
--

ALTER TABLE ONLY topic_tests
    ADD CONSTRAINT topic_tests_topic_id_fkey FOREIGN KEY (topic_id) REFERENCES topics(id) ON DELETE CASCADE;


--
-- Name: topics_next_topic_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: dci
--

ALTER TABLE ONLY topics
    ADD CONSTRAINT topics_next_topic_id_fkey FOREIGN KEY (next_topic_id) REFERENCES topics(id);


--
-- Name: topics_product_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: dci
--

ALTER TABLE ONLY topics
    ADD CONSTRAINT topics_product_id_fkey FOREIGN KEY (product_id) REFERENCES products(id);


--
-- Name: topics_teams_team_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: dci
--

ALTER TABLE ONLY topics_teams
    ADD CONSTRAINT topics_teams_team_id_fkey FOREIGN KEY (team_id) REFERENCES teams(id) ON DELETE CASCADE;


--
-- Name: topics_teams_topic_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: dci
--

ALTER TABLE ONLY topics_teams
    ADD CONSTRAINT topics_teams_topic_id_fkey FOREIGN KEY (topic_id) REFERENCES topics(id) ON DELETE CASCADE;


--
-- Name: user_remotecis_remoteci_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: dci
--

ALTER TABLE ONLY user_remotecis
    ADD CONSTRAINT user_remotecis_remoteci_id_fkey FOREIGN KEY (remoteci_id) REFERENCES remotecis(id) ON DELETE CASCADE;


--
-- Name: user_remotecis_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: dci
--

ALTER TABLE ONLY user_remotecis
    ADD CONSTRAINT user_remotecis_user_id_fkey FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE;


--
-- Name: users_role_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: dci
--

ALTER TABLE ONLY users
    ADD CONSTRAINT users_role_id_fkey FOREIGN KEY (role_id) REFERENCES roles(id) ON DELETE SET NULL;


--
-- Name: users_team_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: dci
--

ALTER TABLE ONLY users
    ADD CONSTRAINT users_team_id_fkey FOREIGN KEY (team_id) REFERENCES teams(id) ON DELETE CASCADE;


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

\connect postgres

SET default_transaction_read_only = off;

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
-- Name: postgres; Type: COMMENT; Schema: -; Owner: postgres
--

COMMENT ON DATABASE postgres IS 'default administrative connection database';


--
-- Name: plpgsql; Type: EXTENSION; Schema: -; Owner: 
--

CREATE EXTENSION IF NOT EXISTS plpgsql WITH SCHEMA pg_catalog;


--
-- Name: EXTENSION plpgsql; Type: COMMENT; Schema: -; Owner: 
--

COMMENT ON EXTENSION plpgsql IS 'PL/pgSQL procedural language';


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

\connect template1

SET default_transaction_read_only = off;

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
-- Name: template1; Type: COMMENT; Schema: -; Owner: postgres
--

COMMENT ON DATABASE template1 IS 'default template for new databases';


--
-- Name: plpgsql; Type: EXTENSION; Schema: -; Owner: 
--

CREATE EXTENSION IF NOT EXISTS plpgsql WITH SCHEMA pg_catalog;


--
-- Name: EXTENSION plpgsql; Type: COMMENT; Schema: -; Owner: 
--

COMMENT ON EXTENSION plpgsql IS 'PL/pgSQL procedural language';


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

--
-- PostgreSQL database cluster dump complete
--

