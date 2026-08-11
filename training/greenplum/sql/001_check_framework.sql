CREATE SCHEMA IF NOT EXISTS greenplum_training;

CREATE TABLE IF NOT EXISTS greenplum_training.task_tests (
    module_name text NOT NULL, task_no integer NOT NULL, test_no integer NOT NULL,
    test_name text NOT NULL, actual_sql text NOT NULL, expected_sql text NOT NULL
) DISTRIBUTED REPLICATED;

CREATE TABLE IF NOT EXISTS greenplum_training.check_history (
    check_id bigserial, checked_at timestamptz NOT NULL DEFAULT clock_timestamp(),
    module_name text NOT NULL, task_no integer NOT NULL,
    tests_passed integer NOT NULL, tests_total integer NOT NULL
) DISTRIBUTED BY (module_name, task_no);

CREATE OR REPLACE FUNCTION greenplum_training.run_checks(p_module_name text, p_task_no integer)
RETURNS TABLE(test_no integer, test_name text, status text, expected text, actual text, error_message text)
LANGUAGE plpgsql VOLATILE AS $$
DECLARE t record; av text; ev text; passed integer := 0; total integer := 0;
BEGIN
  FOR t IN SELECT * FROM greenplum_training.task_tests
           WHERE module_name=p_module_name AND task_no=p_task_no ORDER BY test_no
  LOOP
    total := total + 1; av := NULL; ev := NULL;
    BEGIN
      EXECUTE t.expected_sql INTO ev; EXECUTE t.actual_sql INTO av;
      IF av IS NOT DISTINCT FROM ev THEN
        passed := passed + 1;
        RETURN QUERY SELECT t.test_no,t.test_name,'PASS'::text,ev,av,NULL::text;
      ELSE
        RETURN QUERY SELECT t.test_no,t.test_name,'FAIL'::text,ev,av,NULL::text;
      END IF;
    EXCEPTION WHEN OTHERS THEN
      RETURN QUERY SELECT t.test_no,t.test_name,'ERROR'::text,ev,av,SQLERRM::text;
    END;
  END LOOP;
  IF total=0 THEN RAISE EXCEPTION 'No tests registered for module %, task %',p_module_name,p_task_no; END IF;
  INSERT INTO greenplum_training.check_history(module_name,task_no,tests_passed,tests_total)
  VALUES(p_module_name,p_task_no,passed,total);
END $$;

CREATE OR REPLACE VIEW greenplum_training.progress AS
SELECT module_name,task_no,checked_at,tests_passed,tests_total,
       tests_passed=tests_total AS completed
FROM (
  SELECT *,row_number() OVER(PARTITION BY module_name,task_no ORDER BY checked_at DESC,check_id DESC) rn
  FROM greenplum_training.check_history
) h WHERE rn=1;
