--
-- PostgreSQL database dump
--
-- pg_dump -st indego indego > indego.sql
---
-- Dumped from database version 12.2 (Ubuntu 12.2-4)
-- Dumped by pg_dump version 12.2 (Ubuntu 12.2-4)

SET statement_timeout = 0;
SET lock_timeout = 0;
SET idle_in_transaction_session_timeout = 0;
SET client_encoding = 'UTF8';
SET standard_conforming_strings = on;
SELECT pg_catalog.set_config('search_path', '', false);
SET check_function_bodies = false;
SET xmloption = content;
SET client_min_messages = warning;
SET row_security = off;

SET default_tablespace = '';

SET default_table_access_method = heap;

--
-- Name: indego; Type: TABLE; Schema: public; Owner: indego
--

CREATE TABLE public.indego (
    added timestamp with time zone DEFAULT now() NOT NULL,
    data jsonb
);


ALTER TABLE public.indego OWNER TO indego;

--
-- Name: indego indego_pkey; Type: CONSTRAINT; Schema: public; Owner: indego
--

ALTER TABLE ONLY public.indego
    ADD CONSTRAINT indego_pkey PRIMARY KEY (added);


--
-- PostgreSQL database dump complete
--

