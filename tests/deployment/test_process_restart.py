import os,socket,subprocess,sys,time
from contextlib import contextmanager
from pathlib import Path
import httpx,pytest
ROOT=Path(__file__).parents[2]
def port():
    with socket.socket() as s:s.bind(('127.0.0.1',0));return s.getsockname()[1]
def call(method,url,**kw):
    with httpx.Client(trust_env=False) as c:return c.request(method,url,**kw)
@contextmanager
def service(root,p):
    env=os.environ.copy();env['WORKFLOW_DATABASE_URL']=f"sqlite:///{root/'workflow.db'}"
    proc=subprocess.Popen([sys.executable,'-m','uvicorn','app.main:app','--host','127.0.0.1','--port',str(p)],cwd=ROOT,env=env,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True);url=f'http://127.0.0.1:{p}'
    try:
        for _ in range(200):
            try:
                if call('GET',url+'/',timeout=.3).status_code==200:break
            except httpx.TransportError:time.sleep(.05)
        else:raise AssertionError('service did not start')
        yield url
    finally:proc.terminate();proc.wait(timeout=5)
def payload(mode):return dict(requester_name='Alex Morgan',department='Operations',item_or_service='Office chairs',supplier='Supply Co',amount='1200.50',currency='EUR',business_justification='Replace unsafe and damaged office seating.',required_date='2099-09-01',execution_mode=mode,demonstration_scenario='standard')
@pytest.mark.parametrize('mode',('orchestration','choreography'))
def test_waiting_run_survives_real_process_restart(tmp_path,mode):
    p=port()
    with service(tmp_path,p) as url:
        waiting=call('POST',url+'/api/requests',json=payload(mode),timeout=10).json();assert waiting['purchase_request_state']=='PENDING_APPROVAL'
    assert (tmp_path/'workflow.db').exists()
    with service(tmp_path,p) as url:
        restored=call('GET',url+f"/api/runs/{waiting['run_id']}",timeout=10).json()
        result=call('POST',url+f"/api/approvals/{waiting['work_item_id']}/decision",json={'choice':'APPROVE','expected_state_version':restored['state_version']},timeout=10).json()['run']
        assert result['run_id']==waiting['run_id'] and result['purchase_request_state']=='AUTHORIZED'
