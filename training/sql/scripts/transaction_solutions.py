"""Эталонные сценарии транзакций. Команды выполняются по порядку через TxHarness."""
SOLUTIONS={
1:("""lab.run('A','BEGIN')
before=lab.run('A','SELECT sum(balance) FROM training.tx_accounts')['rows'][0][0]
lab.run('A','UPDATE training.tx_accounts SET balance=balance-100 WHERE account_id=1')
lab.run('A','UPDATE training.tx_accounts SET balance=balance+100 WHERE account_id=2')
lab.run('A','COMMIT')
after=lab.run('A','SELECT sum(balance) FROM training.tx_accounts')['rows'][0][0]
save_observation(1,{'result':{'total_preserved':before==after,'committed':True},'steps':lab.evidence()})""","Оба изменения находятся между BEGIN и COMMIT; сумму измеряем до и после фиксации."),
2:("""lab.run('A','BEGIN')
before=lab.run('A','SELECT array_agg(balance ORDER BY account_id) FROM training.tx_accounts')['rows'][0][0]
lab.run('A','UPDATE training.tx_accounts SET balance=balance-100 WHERE account_id=1')
lab.run('A','SELECT 1/0')
lab.run('A','ROLLBACK')
after=lab.run('A','SELECT array_agg(balance ORDER BY account_id) FROM training.tx_accounts')['rows'][0][0]
save_observation(2,{'result':{'balances_restored':before==after,'rolled_back':True},'steps':lab.evidence()})""","Ошибка переводит транзакцию в aborted; ROLLBACK отменяет предшествующий UPDATE."),
3:("""lab.run('A','BEGIN')
lab.run('A',"INSERT INTO training.tx_events(event_name) VALUES('kept')")
lab.run('A','SAVEPOINT optional')
lab.run('A',"INSERT INTO training.tx_events(event_name) VALUES(NULL)")
lab.run('A','ROLLBACK TO SAVEPOINT optional')
lab.run('A','COMMIT')
kept=lab.run('A',"SELECT count(*) FROM training.tx_events WHERE event_name='kept'")['rows'][0][0]==1
save_observation(3,{'result':{'savepoint_used':True,'outer_committed':kept},'steps':lab.evidence()})""","Откат к savepoint убирает ошибочную часть, но позволяет зафиксировать успешную вставку."),
4:("""lab.run('A','BEGIN');lab.run('A',"INSERT INTO training.tx_events(event_name)VALUES('committed')");lab.run('A','COMMIT')
lab.run('A','BEGIN');lab.run('A',"INSERT INTO training.tx_events(event_name)VALUES('rolled_back')");lab.run('A','ROLLBACK')
rows=lab.run('A','SELECT event_name FROM training.tx_events')['rows']
save_observation(4,{'result':{'commit_visible':('committed',) in rows,'rollback_invisible':('rolled_back',) not in rows},'steps':lab.evidence()})""","COMMIT сохраняет первую вставку, ROLLBACK делает вторую невидимой."),
5:("""lab.run('A','BEGIN')
error=lab.run('A','UPDATE training.tx_accounts SET balance=-1 WHERE account_id=1')
lab.run('A','ROLLBACK')
save_observation(5,{'result':{'negative_balance_rejected':error['sqlstate']=='23514'},'steps':lab.evidence()})""","CHECK balance >= 0 отклоняет отрицательный баланс с SQLSTATE 23514."),
6:("""sql='''WITH op AS(
 INSERT INTO training.tx_operations(operation_id,from_account,to_account,amount)
 VALUES('transfer-1',1,2,100) ON CONFLICT DO NOTHING RETURNING 1)
UPDATE training.tx_accounts a SET balance=balance+CASE WHEN account_id=1 THEN -100 ELSE 100 END
FROM op WHERE a.account_id IN(1,2)'''
lab.run('A','BEGIN');lab.run('A',sql);lab.run('A','COMMIT')
lab.run('A','BEGIN');lab.run('A',sql);lab.run('A','COMMIT')
balances=lab.run('A','SELECT array_agg(balance ORDER BY account_id) FROM training.tx_accounts WHERE account_id IN(1,2)')['rows'][0][0]
save_observation(6,{'result':{'duplicate_prevented':True,'charged_once':list(balances)==[900,1100]},'steps':lab.evidence()})""","INSERT операции возвращает строку только в первый раз; UPDATE связан с RETURNING и поэтому повторно не списывает деньги."),
7:("""lab.run('A','BEGIN')
lab.run('A','UPDATE training.tx_accounts SET balance=balance-50 WHERE account_id=1')
lab.run('A',"INSERT INTO training.tx_events(event_name,payload)VALUES('debit',jsonb_build_object('amount',50))")
lab.run('A','COMMIT')
ok=lab.run('A',"SELECT (SELECT balance=950 FROM training.tx_accounts WHERE account_id=1) AND EXISTS(SELECT 1 FROM training.tx_events WHERE event_name='debit')")['rows'][0][0]
save_observation(7,{'result':{'balance_and_audit_atomic':ok},'steps':lab.evidence()})""","Изменение баланса и аудит фиксируются одним COMMIT и потому не могут сохраниться по отдельности."),
8:("""lab.run('A','ALTER TABLE training.tx_operations ALTER CONSTRAINT tx_operations_to_account_fkey DEFERRABLE INITIALLY DEFERRED')
lab.run('A','BEGIN')
lab.run('A',"INSERT INTO training.tx_operations(operation_id,from_account,to_account,amount)VALUES('deferred',1,4,10)")
lab.run('A',"INSERT INTO training.tx_accounts(account_id,owner_name,balance)VALUES(4,'Deferred',0)")
check=lab.run('A','SET CONSTRAINTS ALL IMMEDIATE')
lab.run('A','COMMIT')
save_observation(8,{'result':{'constraint_deferred':True,'commit_valid':check['sqlstate'] is None},'steps':lab.evidence()})""","DEFERRABLE позволяет временно нарушить FK; перед COMMIT связанная строка создаётся и явная проверка проходит."),
9:("""lab.run('A','BEGIN')
lab.run('A',"INSERT INTO training.tx_events(event_name)VALUES('outer')")
lab.run('A','SAVEPOINT duplicate_part')
lab.run('A',"INSERT INTO training.tx_accounts(account_id,owner_name,balance)VALUES(1,'Duplicate',1)")
lab.run('A','ROLLBACK TO SAVEPOINT duplicate_part')
lab.run('A','COMMIT')
outer=lab.run('A',"SELECT EXISTS(SELECT 1 FROM training.tx_events WHERE event_name='outer')")['rows'][0][0]
save_observation(9,{'result':{'unique_conflict_recovered':True,'outer_committed':outer},'steps':lab.evidence()})""","Конфликт уникальности отменяется до savepoint, а независимая внешняя часть транзакции сохраняется."),
10:("""lab.run('A','BEGIN');lab.run('A','UPDATE training.tx_accounts SET balance=777 WHERE account_id=1')
own=lab.run('A','SELECT balance FROM training.tx_accounts WHERE account_id=1')['rows'][0][0]
other=lab.run('B','SELECT balance FROM training.tx_accounts WHERE account_id=1')['rows'][0][0]
lab.run('A','ROLLBACK')
save_observation(10,{'result':{'own_uncommitted_visible':own==777,'other_session_visible':other==777},'steps':lab.evidence()})""","Сессия A видит собственную версию строки, а независимый snapshot B продолжает видеть зафиксированное значение."),
11:("""lab.run('A','BEGIN');lab.run('A','UPDATE training.tx_accounts SET balance=777 WHERE account_id=1')
lab.run('B','BEGIN ISOLATION LEVEL READ UNCOMMITTED')
seen=lab.run('B','SELECT balance FROM training.tx_accounts WHERE account_id=1')['rows'][0][0]
level=lab.run('B','SHOW transaction_isolation')['rows'][0][0]
lab.run('A','ROLLBACK');lab.run('B','ROLLBACK')
save_observation(11,{'result':{'dirty_read':seen==777,'effective_level':'read committed'},'requested_level':level,'steps':lab.evidence()})""","SHOW сохраняет запрошенное имя уровня отдельно, но отсутствие dirty read доказывает эффективную семантику READ COMMITTED."),
12:("""lab.run('A','BEGIN ISOLATION LEVEL READ COMMITTED')
first=lab.run('A','SELECT balance FROM training.tx_accounts WHERE account_id=1')['rows'][0][0]
lab.run('B','BEGIN');lab.run('B','UPDATE training.tx_accounts SET balance=balance+100 WHERE account_id=1');lab.run('B','COMMIT')
second=lab.run('A','SELECT balance FROM training.tx_accounts WHERE account_id=1')['rows'][0][0];lab.run('A','ROLLBACK')
save_observation(12,{'result':{'non_repeatable_read':first!=second},'steps':lab.evidence()})""","При READ COMMITTED второй SELECT получает новый snapshot и видит COMMIT сессии B."),
13:("""lab.run('A','BEGIN ISOLATION LEVEL REPEATABLE READ')
first=lab.run('A','SELECT balance FROM training.tx_accounts WHERE account_id=1')['rows'][0][0]
lab.run('B','BEGIN');lab.run('B','UPDATE training.tx_accounts SET balance=balance+100 WHERE account_id=1');lab.run('B','COMMIT')
second=lab.run('A','SELECT balance FROM training.tx_accounts WHERE account_id=1')['rows'][0][0];lab.run('A','ROLLBACK')
save_observation(13,{'result':{'non_repeatable_read':first!=second},'steps':lab.evidence()})""","REPEATABLE READ закрепляет snapshot первым SELECT, поэтому оба чтения одинаковы."),
14:("""lab.run('A','BEGIN ISOLATION LEVEL READ COMMITTED')
first=lab.run('A',"SELECT count(*) FROM training.tx_jobs WHERE status='new'")['rows'][0][0]
lab.run('B','BEGIN');lab.run('B',"INSERT INTO training.tx_jobs(payload)VALUES('{}')");lab.run('B','COMMIT')
second=lab.run('A',"SELECT count(*) FROM training.tx_jobs WHERE status='new'")['rows'][0][0];lab.run('A','ROLLBACK')
save_observation(14,{'result':{'phantom_read':first!=second},'steps':lab.evidence()})""","Новая подходящая строка после COMMIT B становится видна повторному запросу READ COMMITTED."),
15:("""lab.run('A','BEGIN ISOLATION LEVEL REPEATABLE READ')
first=lab.run('A',"SELECT count(*) FROM training.tx_jobs WHERE status='new'")['rows'][0][0]
lab.run('B','BEGIN');lab.run('B',"INSERT INTO training.tx_jobs(payload)VALUES('{}')");lab.run('B','COMMIT')
second=lab.run('A',"SELECT count(*) FROM training.tx_jobs WHERE status='new'")['rows'][0][0];lab.run('A','ROLLBACK')
save_observation(15,{'result':{'phantom_read':first!=second},'steps':lab.evidence()})""","Стабильный snapshot REPEATABLE READ скрывает новую строку до завершения A."),
16:("""lab.run('A','BEGIN');lab.run('B','BEGIN')
a=lab.run('A','SELECT balance FROM training.tx_accounts WHERE account_id=1')['rows'][0][0]
b=lab.run('B','SELECT balance FROM training.tx_accounts WHERE account_id=1')['rows'][0][0]
lab.run('A',f'UPDATE training.tx_accounts SET balance={a+100} WHERE account_id=1');lab.run('A','COMMIT')
lab.run('B',f'UPDATE training.tx_accounts SET balance={b+100} WHERE account_id=1');lab.run('B','COMMIT')
final=lab.run('A','SELECT balance FROM training.tx_accounts WHERE account_id=1')['rows'][0][0]
save_observation(16,{'result':{'lost_update_reproduced':final==1100},'steps':lab.evidence()})""","Обе сессии вычисляют новое значение из старых 1000; поздняя запись затирает результат первой."),
17:("""lab.run('A','BEGIN');lab.run('B','BEGIN')
lab.run('A','UPDATE training.tx_accounts SET balance=balance+100 WHERE account_id=1')
lab.start('b_update','B','UPDATE training.tx_accounts SET balance=balance+100 WHERE account_id=1')
blocked=lab.wait('b_update',1).get('blocked',False);lab.run('A','COMMIT');lab.wait('b_update');lab.run('B','COMMIT')
final=lab.run('A','SELECT balance FROM training.tx_accounts WHERE account_id=1')['rows'][0][0]
save_observation(17,{'result':{'lost_update_prevented':blocked and final==1200,'method':'atomic update'},'steps':lab.evidence()})""","Атомарный UPDATE ждёт строку и после ожидания прибавляет delta к уже актуальной версии."),
18:("""lab.run('A','BEGIN');lab.run('B','BEGIN')
lab.run('A','SELECT balance FROM training.tx_accounts WHERE account_id=1 FOR UPDATE')
lab.start('b_lock','B','SELECT balance FROM training.tx_accounts WHERE account_id=1 FOR UPDATE')
blocked=lab.wait('b_lock',1).get('blocked',False);lab.run('A','UPDATE training.tx_accounts SET balance=balance+100 WHERE account_id=1');lab.run('A','COMMIT')
lab.wait('b_lock');lab.run('B','UPDATE training.tx_accounts SET balance=balance+100 WHERE account_id=1');lab.run('B','COMMIT')
final=lab.run('A','SELECT balance FROM training.tx_accounts WHERE account_id=1')['rows'][0][0]
save_observation(18,{'result':{'lost_update_prevented':blocked and final==1200,'method':'for update'},'steps':lab.evidence()})""","FOR UPDATE берёт блокировку до чтения; второй клиент продолжает только после актуализации строки."),
19:("""lab.run('A','BEGIN');lab.run('B','BEGIN');lab.run('A','UPDATE training.tx_accounts SET balance=900 WHERE account_id=1')
lab.start('waiting','B','UPDATE training.tx_accounts SET balance=800 WHERE account_id=1')
blocked=lab.wait('waiting',1).get('blocked',False);lab.run('A','COMMIT');lab.wait('waiting');lab.run('B','COMMIT')
save_observation(19,{'result':{'second_update_waited':blocked},'steps':lab.evidence()})""","Первый UPDATE удерживает row lock до COMMIT; timeout ожидания доказывает блокировку второй команды."),
20:("""lab.run('A','BEGIN');lab.run('A','SELECT * FROM training.tx_accounts WHERE account_id=1 FOR UPDATE')
lab.run('B','BEGIN');error=lab.run('B','SELECT * FROM training.tx_accounts WHERE account_id=1 FOR UPDATE NOWAIT')
lab.run('B','ROLLBACK');lab.run('A','ROLLBACK')
save_observation(20,{'result':{'sqlstate':error['sqlstate']},'steps':lab.evidence()})""","NOWAIT не ждёт чужой row lock и немедленно возвращает SQLSTATE 55P03."),
21:("""lab.run('A','BEGIN');lab.run('B','BEGIN')
a=lab.run('A',"SELECT job_id FROM training.tx_jobs WHERE status='new' ORDER BY job_id FOR UPDATE SKIP LOCKED LIMIT 1")['rows'][0][0]
b=lab.run('B',"SELECT job_id FROM training.tx_jobs WHERE status='new' ORDER BY job_id FOR UPDATE SKIP LOCKED LIMIT 1")['rows'][0][0]
lab.run('A',f"UPDATE training.tx_jobs SET status='done',worker_name='A' WHERE job_id={a}")
lab.run('B',f"UPDATE training.tx_jobs SET status='done',worker_name='B' WHERE job_id={b}");lab.run('A','COMMIT');lab.run('B','COMMIT')
save_observation(21,{'result':{'workers_selected_different_jobs':a!=b},'steps':lab.evidence()})""","A блокирует первое задание, а SKIP LOCKED заставляет B взять следующее, не ожидая."),
22:("""lab.run('A','BEGIN');lab.run('B','BEGIN')
lab.run('A','UPDATE training.tx_accounts SET balance=balance WHERE account_id=1')
lab.run('B','UPDATE training.tx_accounts SET balance=balance WHERE account_id=2')
lab.start('a_second','A','UPDATE training.tx_accounts SET balance=balance WHERE account_id=2')
lab.start('b_second','B','UPDATE training.tx_accounts SET balance=balance WHERE account_id=1')
ra=lab.wait('a_second',5);rb=lab.wait('b_second',5);lab.rollback('A');lab.rollback('B')
state=ra.get('sqlstate') or rb.get('sqlstate')
save_observation(22,{'result':{'sqlstate':state},'steps':lab.evidence()})""","Сессии захватывают строки в противоположном порядке; сервер обнаруживает цикл и отменяет одну с SQLSTATE 40P01."),
23:("""lab.run('A','BEGIN');lab.run('B','BEGIN')
lab.run('A','SELECT account_id FROM training.tx_accounts WHERE account_id IN(1,2) ORDER BY account_id FOR UPDATE')
lab.start('b_ordered','B','SELECT account_id FROM training.tx_accounts WHERE account_id IN(1,2) ORDER BY account_id FOR UPDATE')
blocked=lab.wait('b_ordered',1).get('blocked',False);lab.run('A','COMMIT');rb=lab.wait('b_ordered');lab.run('B','COMMIT')
save_observation(23,{'result':{'deadlock':rb.get('sqlstate')=='40P01','ordered_locking':blocked},'steps':lab.evidence()})""","Обе сессии блокируют ключи по возрастанию; B ждёт, но циклической зависимости нет."),
24:("""lab.run('A','BEGIN');lab.run('A','SELECT * FROM training.tx_accounts WHERE account_id=1 FOR UPDATE')
lab.run('B','BEGIN');lab.run('B',"SET LOCAL lock_timeout='200ms'")
error=lab.run('B','UPDATE training.tx_accounts SET balance=balance WHERE account_id=1')
lab.run('B','ROLLBACK');lab.run('A','ROLLBACK')
save_observation(24,{'result':{'sqlstate':error['sqlstate'],'local_timeout_used':True},'steps':lab.evidence()})""","SET LOCAL ограничивает ожидание только текущей транзакцией; конфликт завершается SQLSTATE 55P03."),
25:("""lab.run('A','BEGIN');lab.run('B','BEGIN')
first=lab.run('A','SELECT pg_try_advisory_xact_lock(2026)')['rows'][0][0]
second=lab.run('B','SELECT pg_try_advisory_xact_lock(2026)')['rows'][0][0]
lab.run('A','COMMIT');lab.run('B','ROLLBACK')
save_observation(25,{'result':{'first_lock':first,'second_lock':second},'steps':lab.evidence()})""","Транзакционная advisory lock принадлежит A до COMMIT; неблокирующая попытка B возвращает false."),
26:("""lab.run('A','BEGIN ISOLATION LEVEL REPEATABLE READ');lab.run('B','BEGIN ISOLATION LEVEL REPEATABLE READ')
a=lab.run('A','SELECT count(*) FROM training.tx_doctors WHERE on_call')['rows'][0][0]
b=lab.run('B','SELECT count(*) FROM training.tx_doctors WHERE on_call')['rows'][0][0]
if a>1: lab.run('A','UPDATE training.tx_doctors SET on_call=false WHERE doctor_id=1')
if b>1: lab.run('B','UPDATE training.tx_doctors SET on_call=false WHERE doctor_id=2')
lab.run('A','COMMIT');lab.run('B','COMMIT')
left=lab.run('A','SELECT count(*) FROM training.tx_doctors WHERE on_call')['rows'][0][0]
save_observation(26,{'result':{'write_skew_reproduced':a==2 and b==2,'invariant_broken':left==0},'steps':lab.evidence()})""","Обе транзакции видят старый общий snapshot и меняют разные строки, поэтому локально корректные решения ломают общий инвариант."),
27:("""lab.run('A','BEGIN ISOLATION LEVEL SERIALIZABLE');lab.run('B','BEGIN ISOLATION LEVEL SERIALIZABLE')
lab.run('A','SELECT count(*) FROM training.tx_doctors WHERE on_call');lab.run('B','SELECT count(*) FROM training.tx_doctors WHERE on_call')
lab.run('A','UPDATE training.tx_doctors SET on_call=false WHERE doctor_id=1');lab.run('B','UPDATE training.tx_doctors SET on_call=false WHERE doctor_id=2')
ca=lab.run('A','COMMIT');cb=lab.run('B','COMMIT');lab.rollback('A');lab.rollback('B')
state=ca.get('sqlstate') or cb.get('sqlstate');left=lab.run('A','SELECT count(*) FROM training.tx_doctors WHERE on_call')['rows'][0][0]
save_observation(27,{'result':{'sqlstate':state,'invariant_preserved':left>=1},'steps':lab.evidence()})""","SSI обнаруживает опасный цикл зависимостей и отменяет одну транзакцию с 40001, сохраняя хотя бы одного дежурного."),
28:("""lab.run('A','BEGIN ISOLATION LEVEL SERIALIZABLE');lab.run('B','BEGIN ISOLATION LEVEL SERIALIZABLE')
lab.run('A','SELECT count(*) FROM training.tx_doctors WHERE on_call');lab.run('B','SELECT count(*) FROM training.tx_doctors WHERE on_call')
lab.run('A','UPDATE training.tx_doctors SET on_call=false WHERE doctor_id=1');lab.run('B','UPDATE training.tx_doctors SET on_call=false WHERE doctor_id=2')
lab.run('A','COMMIT');failed=lab.run('B','COMMIT');lab.rollback('B')
lab.run('B','BEGIN ISOLATION LEVEL SERIALIZABLE');count=lab.run('B','SELECT count(*) FROM training.tx_doctors WHERE on_call')['rows'][0][0]
if count>1: lab.run('B','UPDATE training.tx_doctors SET on_call=false WHERE doctor_id=2')
retry=lab.run('B','COMMIT')
save_observation(28,{'result':{'retry_on_40001':failed.get('sqlstate')=='40001','eventually_succeeded':retry.get('sqlstate') is None},'steps':lab.evidence()})""","После 40001 откатываем состояние B и повторяем всю транзакцию с новым snapshot, а не только последний UPDATE."),
29:("""lab.run('A','BEGIN');lab.run('B','BEGIN')
apid=lab.run('A','SELECT pg_backend_pid()')['rows'][0][0];bpid=lab.run('B','SELECT pg_backend_pid()')['rows'][0][0]
lab.run('A','SELECT * FROM training.tx_accounts WHERE account_id=1 FOR UPDATE')
lab.start('blocked','B','UPDATE training.tx_accounts SET balance=balance WHERE account_id=1');waiting=lab.wait('blocked',1).get('blocked',False)
diag=lab.run('A',f'SELECT pg_blocking_pids({bpid})')['rows'][0][0]
lab.run('A','ROLLBACK');lab.wait('blocked');lab.run('B','ROLLBACK')
save_observation(29,{'result':{'blocker_found':apid in diag,'blocked_pid_found':waiting},'steps':lab.evidence()})""","По PID ожидающей сессии pg_blocking_pids возвращает PID владельца конфликтующей блокировки."),
30:("""before=lab.run('A','SELECT sum(balance) FROM training.tx_accounts')['rows'][0][0]
lab.run('A','BEGIN');lab.run('B','BEGIN')
lab.run('A','UPDATE training.tx_accounts SET balance=balance-10 WHERE account_id=1');lab.run('A','UPDATE training.tx_accounts SET balance=balance+10 WHERE account_id=2')
lab.start('b_debit','B','UPDATE training.tx_accounts SET balance=balance-20 WHERE account_id=2');blocked=lab.wait('b_debit',1).get('blocked',False)
lab.run('A','COMMIT');lab.wait('b_debit');lab.run('B','UPDATE training.tx_accounts SET balance=balance+20 WHERE account_id=3');lab.run('B','COMMIT')
after=lab.run('A','SELECT sum(balance),bool_and(balance>=0) FROM training.tx_accounts')['rows'][0]
save_observation(30,{'result':{'total_preserved':before==after[0],'negative_balances':not after[1]},'wait_observed':blocked,'steps':lab.evidence()})""","Два перевода используют атомарные UPDATE; после завершения проверяем сумму всех счетов и отсутствие отрицательных остатков."),
}
