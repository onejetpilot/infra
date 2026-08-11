"""Эталонные решения модуля безопасности PostgreSQL."""

SOLUTIONS = {
1: ("""DO $$ BEGIN
 IF NOT EXISTS(SELECT 1 FROM pg_roles WHERE rolname='training_readers') THEN CREATE ROLE training_readers NOLOGIN; END IF;
 IF NOT EXISTS(SELECT 1 FROM pg_roles WHERE rolname='training_alice') THEN CREATE ROLE training_alice LOGIN PASSWORD 'Training_only_2026'; END IF;
END $$;
CREATE OR REPLACE VIEW training.sc_01 AS
SELECT rolname,rolcanlogin FROM pg_roles WHERE rolname IN ('training_readers','training_alice');""", "NOLOGIN-роль объединяет права, LOGIN-роль представляет пользователя."),
2: ("""DO $$ BEGIN IF NOT EXISTS(SELECT 1 FROM pg_roles WHERE rolname='training_connect') THEN CREATE ROLE training_connect NOLOGIN; END IF; END $$;
GRANT CONNECT ON DATABASE sql_train TO training_connect;
CREATE OR REPLACE VIEW training.sc_02 AS
SELECT datname,has_database_privilege('training_connect',datname,'CONNECT') AS can_connect FROM pg_database WHERE datname=current_database();""", "CONNECT разрешает подключение к базе, но не даёт доступ к её схемам и таблицам."),
3: ("""DO $$ BEGIN IF NOT EXISTS(SELECT 1 FROM pg_roles WHERE rolname='training_schema_user') THEN CREATE ROLE training_schema_user NOLOGIN; END IF; END $$;
GRANT USAGE ON SCHEMA staging TO training_schema_user;
CREATE OR REPLACE VIEW training.sc_03 AS
SELECT nspname,has_schema_privilege('training_schema_user',nspname,'USAGE') AS has_usage FROM pg_namespace WHERE nspname='staging';""", "USAGE разрешает находить объекты схемы, но не читать таблицы автоматически."),
4: ("""DO $$ BEGIN IF NOT EXISTS(SELECT 1 FROM pg_roles WHERE rolname='training_select') THEN CREATE ROLE training_select NOLOGIN; END IF; END $$;
GRANT USAGE ON SCHEMA staging TO training_select;
GRANT SELECT ON staging.orders TO training_select;
CREATE OR REPLACE VIEW training.sc_04 AS
SELECT has_table_privilege('training_select','staging.orders','SELECT') AS can_select;""", "Для чтения нужны USAGE схемы и SELECT конкретного объекта."),
5: ("""CREATE TABLE IF NOT EXISTS training.sc_people(id bigint PRIMARY KEY,name text,email text,salary numeric);
DO $$ BEGIN IF NOT EXISTS(SELECT 1 FROM pg_roles WHERE rolname='training_columns') THEN CREATE ROLE training_columns NOLOGIN; END IF; END $$;
GRANT SELECT(id,name) ON training.sc_people TO training_columns;
CREATE OR REPLACE VIEW training.sc_05 AS
SELECT column_name,has_column_privilege('training_columns','training.sc_people',column_name,'SELECT') AS can_select
FROM information_schema.columns WHERE table_schema='training' AND table_name='sc_people';""", "Колонные права скрывают email и salary, не создавая отдельную копию таблицы."),
6: ("""DO $$ BEGIN IF NOT EXISTS(SELECT 1 FROM pg_roles WHERE rolname='training_readonly') THEN CREATE ROLE training_readonly NOLOGIN; END IF; END $$;
GRANT CONNECT ON DATABASE sql_train TO training_readonly;
GRANT USAGE ON SCHEMA staging,mart TO training_readonly;
GRANT SELECT ON ALL TABLES IN SCHEMA staging,mart TO training_readonly;
CREATE OR REPLACE VIEW training.sc_06 AS
SELECT table_schema,table_name,privilege_type FROM information_schema.role_table_grants
WHERE grantee='training_readonly';""", "Групповая роль получает только чтение рабочих витрин и staging."),
7: ("""CREATE TABLE IF NOT EXISTS training.sc_load_target(id bigint PRIMARY KEY,payload jsonb,load_dttm timestamptz DEFAULT now());
DO $$ BEGIN IF NOT EXISTS(SELECT 1 FROM pg_roles WHERE rolname='training_loader') THEN CREATE ROLE training_loader NOLOGIN; END IF; END $$;
GRANT USAGE ON SCHEMA training TO training_loader;
GRANT SELECT,INSERT,UPDATE ON training.sc_load_target TO training_loader;
CREATE OR REPLACE VIEW training.sc_07 AS
SELECT privilege_type FROM information_schema.role_table_grants
WHERE grantee='training_loader' AND table_name='sc_load_target';""", "Загрузчик изменяет только целевую таблицу и не получает DELETE или DDL-права."),
8: ("""DO $$ BEGIN
 IF NOT EXISTS(SELECT 1 FROM pg_roles WHERE rolname='training_parent') THEN CREATE ROLE training_parent NOLOGIN; END IF;
 IF NOT EXISTS(SELECT 1 FROM pg_roles WHERE rolname='training_child') THEN CREATE ROLE training_child NOLOGIN; END IF;
END $$;
GRANT training_parent TO training_child;
CREATE OR REPLACE VIEW training.sc_08 AS
SELECT parent.rolname AS parent_role,child.rolname AS member_role
FROM pg_auth_members m JOIN pg_roles parent ON parent.oid=m.roleid JOIN pg_roles child ON child.oid=m.member
WHERE parent.rolname='training_parent' AND child.rolname='training_child';""", "Членство позволяет собирать права из групповых ролей вместо повторных GRANT."),
9: ("""DO $$ BEGIN IF NOT EXISTS(SELECT 1 FROM pg_roles WHERE rolname='training_reporter') THEN CREATE ROLE training_reporter NOLOGIN; END IF; END $$;
GRANT SELECT ON staging.orders TO training_reporter;
CREATE OR REPLACE VIEW training.sc_09 AS
SELECT 'training_reporter'::text AS role_name,has_table_privilege('training_reporter','staging.orders','SELECT') AS effective_select;""", "SET ROLE используют в отдельной проверочной сессии; представление показывает ожидаемое эффективное право."),
10: ("""REVOKE CREATE ON SCHEMA public FROM PUBLIC;
CREATE OR REPLACE VIEW training.sc_10 AS
SELECT nspname,has_schema_privilege('public',nspname,'CREATE') AS public_can_create
FROM pg_namespace WHERE nspname='public';""", "Отзыв CREATE у PUBLIC запрещает любому пользователю создавать объекты в общей схеме."),
11: ("""DO $$ BEGIN IF NOT EXISTS(SELECT 1 FROM pg_roles WHERE rolname='training_future_reader') THEN CREATE ROLE training_future_reader NOLOGIN; END IF; END $$;
ALTER DEFAULT PRIVILEGES IN SCHEMA training GRANT SELECT ON TABLES TO training_future_reader;
CREATE OR REPLACE VIEW training.sc_11 AS
SELECT defaclobjtype,defaclacl FROM pg_default_acl WHERE defaclnamespace='training'::regnamespace;""", "Default privileges действуют только на будущие объекты, создаваемые текущим владельцем."),
12: ("""CREATE TABLE IF NOT EXISTS training.sc_owned_object(id int);
ALTER TABLE training.sc_owned_object OWNER TO student;
CREATE OR REPLACE VIEW training.sc_12 AS
SELECT c.relname,r.rolname AS owner_name FROM pg_class c JOIN pg_roles r ON r.oid=c.relowner
WHERE c.oid='training.sc_owned_object'::regclass;""", "Владелец может менять объект и управлять его правами; это сильнее обычного GRANT."),
13: ("""CREATE OR REPLACE FUNCTION training.sc_order_count_invoker() RETURNS bigint
LANGUAGE sql SECURITY INVOKER STABLE AS $$ SELECT count(*) FROM staging.orders $$;
CREATE OR REPLACE VIEW training.sc_13 AS
SELECT p.proname,p.prosecdef FROM pg_proc p WHERE p.oid='training.sc_order_count_invoker()'::regprocedure;""", "SECURITY INVOKER выполняется с правами вызывающего пользователя."),
14: ("""CREATE OR REPLACE FUNCTION training.sc_order_count_definer() RETURNS bigint
LANGUAGE sql SECURITY DEFINER STABLE SET search_path=pg_catalog,staging
AS $$ SELECT count(*) FROM staging.orders $$;
REVOKE ALL ON FUNCTION training.sc_order_count_definer() FROM PUBLIC;
CREATE OR REPLACE VIEW training.sc_14 AS
SELECT p.proname,p.prosecdef FROM pg_proc p WHERE p.oid='training.sc_order_count_definer()'::regprocedure;""", "SECURITY DEFINER использует права владельца, поэтому EXECUTE ограничивается явно."),
15: ("""CREATE OR REPLACE FUNCTION training.sc_safe_count() RETURNS bigint
LANGUAGE sql SECURITY DEFINER STABLE SET search_path=pg_catalog
AS $$ SELECT count(*) FROM staging.orders $$;
CREATE OR REPLACE VIEW training.sc_15 AS
SELECT proname,proconfig FROM pg_proc WHERE oid='training.sc_safe_count()'::regprocedure;""", "Фиксированный search_path и квалифицированные имена защищают definer-функцию от подмены объектов."),
16: ("""CREATE OR REPLACE FUNCTION training.sc_find_order(p_order_id text) RETURNS TABLE(order_id text,order_status text)
LANGUAGE sql SECURITY INVOKER STABLE AS $$
 SELECT o.order_id,o.order_status FROM staging.orders o WHERE o.order_id=p_order_id
$$;
CREATE OR REPLACE VIEW training.sc_16 AS
SELECT proname,proargnames FROM pg_proc WHERE oid='training.sc_find_order(text)'::regprocedure;""", "Параметр функции передаётся отдельно от SQL-текста и не допускает SQL injection."),
17: ("""CREATE TABLE IF NOT EXISTS training.sc_tenant_data(tenant_name text NOT NULL,id bigint NOT NULL,payload text,PRIMARY KEY(tenant_name,id));
ALTER TABLE training.sc_tenant_data ENABLE ROW LEVEL SECURITY;
CREATE OR REPLACE VIEW training.sc_17 AS
SELECT relname,relrowsecurity FROM pg_class WHERE oid='training.sc_tenant_data'::regclass;""", "ENABLE RLS включает применение политик к обычным пользователям."),
18: ("""CREATE TABLE IF NOT EXISTS training.sc_user_rows(owner_name text NOT NULL,id bigint PRIMARY KEY,payload text);
ALTER TABLE training.sc_user_rows ENABLE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS sc_owner_read ON training.sc_user_rows;
CREATE POLICY sc_owner_read ON training.sc_user_rows FOR SELECT USING(owner_name=current_user);
CREATE OR REPLACE VIEW training.sc_18 AS
SELECT policyname,cmd,qual FROM pg_policies WHERE schemaname='training' AND tablename='sc_user_rows';""", "USING оставляет пользователю только принадлежащие ему строки."),
19: ("""DROP POLICY IF EXISTS sc_owner_write ON training.sc_user_rows;
CREATE POLICY sc_owner_write ON training.sc_user_rows FOR INSERT WITH CHECK(owner_name=current_user);
CREATE OR REPLACE VIEW training.sc_19 AS
SELECT policyname,cmd,with_check FROM pg_policies WHERE schemaname='training' AND tablename='sc_user_rows';""", "WITH CHECK проверяет новые данные и запрещает записывать строку от имени другого пользователя."),
20: ("""ALTER TABLE training.sc_user_rows FORCE ROW LEVEL SECURITY;
CREATE OR REPLACE VIEW training.sc_20 AS
SELECT relname,relrowsecurity,relforcerowsecurity FROM pg_class WHERE oid='training.sc_user_rows'::regclass;""", "FORCE заставляет владельца таблицы также подчиняться RLS, кроме суперпользовательского обхода."),
21: ("""CREATE OR REPLACE VIEW training.sc_orders_public AS
SELECT order_id,order_status,purchased_at FROM staging.orders;
REVOKE ALL ON training.sc_orders_public FROM PUBLIC;
DO $$ BEGIN IF NOT EXISTS(SELECT 1 FROM pg_roles WHERE rolname='training_view_reader') THEN CREATE ROLE training_view_reader NOLOGIN; END IF; END $$;
GRANT SELECT ON training.sc_orders_public TO training_view_reader;
CREATE OR REPLACE VIEW training.sc_21 AS
SELECT grantee,privilege_type FROM information_schema.role_table_grants WHERE table_schema='training' AND table_name='sc_orders_public';""", "Представление служит стабильным интерфейсом и открывает только нужные колонки."),
22: ("""CREATE OR REPLACE VIEW training.sc_safe_orders WITH (security_barrier=true) AS
SELECT order_id,order_status,purchased_at FROM staging.orders WHERE order_status<>'canceled';
CREATE OR REPLACE VIEW training.sc_22 AS
SELECT relname,reloptions FROM pg_class WHERE oid='training.sc_safe_orders'::regclass;""", "security_barrier ограничивает небезопасное проталкивание пользовательских предикатов через view."),
23: ("""CREATE OR REPLACE VIEW training.sc_masked_people AS
SELECT id,name,CASE WHEN email IS NULL THEN NULL ELSE regexp_replace(email,'(^.).*(@.*$)','\\1***\\2') END AS email,
       NULL::numeric AS salary FROM training.sc_people;
CREATE OR REPLACE VIEW training.sc_23 AS SELECT * FROM training.sc_masked_people;""", "Маскирующее представление скрывает salary и оставляет минимум email для распознавания."),
24: ("""CREATE TABLE IF NOT EXISTS training.sc_ddl_audit(event_time timestamptz DEFAULT clock_timestamp(),username text,command_tag text,object_identity text);
CREATE OR REPLACE FUNCTION training.sc_capture_ddl() RETURNS event_trigger LANGUAGE plpgsql AS $$
BEGIN INSERT INTO training.sc_ddl_audit(username,command_tag,object_identity)
 SELECT session_user,command_tag,object_identity FROM pg_event_trigger_ddl_commands(); END $$;
DROP EVENT TRIGGER IF EXISTS sc_ddl_audit_trigger;
CREATE EVENT TRIGGER sc_ddl_audit_trigger ON ddl_command_end EXECUTE FUNCTION training.sc_capture_ddl();
CREATE OR REPLACE VIEW training.sc_24 AS SELECT * FROM training.sc_ddl_audit;""", "Event trigger записывает завершённые DDL-команды в отдельный журнал."),
25: ("""CREATE OR REPLACE VIEW training.sc_25 AS
SELECT usename,application_name,client_addr,backend_start,state
FROM pg_stat_activity WHERE datname=current_database();""", "pg_stat_activity показывает текущие подключения; долгую историю входов следует собирать из серверного журнала."),
26: ("""DO $$ BEGIN IF NOT EXISTS(SELECT 1 FROM pg_roles WHERE rolname='training_limited') THEN CREATE ROLE training_limited NOLOGIN; END IF; END $$;
ALTER ROLE training_limited SET statement_timeout='30s';
ALTER ROLE training_limited SET lock_timeout='5s';
ALTER ROLE training_limited SET idle_in_transaction_session_timeout='60s';
CREATE OR REPLACE VIEW training.sc_26 AS
SELECT rolname,rolconfig FROM pg_roles WHERE rolname='training_limited';""", "Таймауты ограничивают долгие запросы, ожидание блокировок и забытые транзакции."),
27: ("""REVOKE TEMPORARY ON DATABASE sql_train FROM training_limited;
CREATE OR REPLACE VIEW training.sc_27 AS
SELECT has_database_privilege('training_limited',current_database(),'TEMP') AS can_create_temp;""", "TEMP — отдельное право базы; его отзыв ограничивает создание временных объектов."),
28: ("""REVOKE ALL ON training.sc_load_target FROM training_loader;
GRANT SELECT,INSERT ON training.sc_load_target TO training_loader;
CREATE OR REPLACE VIEW training.sc_28 AS
SELECT privilege_type FROM information_schema.role_table_grants
WHERE grantee='training_loader' AND table_name='sc_load_target';""", "REVOKE удаляет прежние права, после чего выдаётся более узкий набор."),
29: ("""CREATE OR REPLACE VIEW training.sc_29 AS
WITH roles(role_name) AS (VALUES('training_readonly'),('training_loader'),('training_limited')),
objects(object_name) AS (VALUES('staging.orders'),('training.sc_load_target'),('training.sc_people'))
SELECT role_name,object_name,
 has_table_privilege(role_name,object_name,'SELECT') AS can_select,
 has_table_privilege(role_name,object_name,'INSERT') AS can_insert,
 has_table_privilege(role_name,object_name,'UPDATE') AS can_update,
 has_table_privilege(role_name,object_name,'DELETE') AS can_delete
FROM roles CROSS JOIN objects;""", "Матрица показывает как разрешённые, так и запрещённые операции для каждой роли и таблицы."),
30: ("""DO $$ BEGIN
 IF NOT EXISTS(SELECT 1 FROM pg_roles WHERE rolname='training_app_read') THEN CREATE ROLE training_app_read NOLOGIN; END IF;
 IF NOT EXISTS(SELECT 1 FROM pg_roles WHERE rolname='training_app_write') THEN CREATE ROLE training_app_write NOLOGIN; END IF;
 IF NOT EXISTS(SELECT 1 FROM pg_roles WHERE rolname='training_app_user') THEN CREATE ROLE training_app_user LOGIN PASSWORD 'Training_app_2026'; END IF;
END $$;
GRANT CONNECT ON DATABASE sql_train TO training_app_user;
GRANT USAGE ON SCHEMA training TO training_app_read,training_app_write;
GRANT SELECT ON training.sc_masked_people,training.sc_orders_public TO training_app_read;
GRANT SELECT,INSERT ON training.sc_load_target TO training_app_write;
GRANT training_app_read,training_app_write TO training_app_user;
CREATE OR REPLACE VIEW training.sc_30 AS
SELECT parent.rolname AS granted_role,member.rolname AS member_role
FROM pg_auth_members m JOIN pg_roles parent ON parent.oid=m.roleid JOIN pg_roles member ON member.oid=m.member
WHERE member.rolname='training_app_user';""", "Пользователь получает композицию минимальных read/write-ролей, а не прямые широкие права."),
}
