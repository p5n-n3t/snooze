"""Small scoped MCP facade and stdio transport for registered coordinators."""
import hmac
import json
from dataclasses import asdict
from snooze.events import EventFeed
from snooze.outbox import Outbox


class MCPFacade:
    def __init__(self,repository,control,token,projects):
        self.repo=repository;self.control=control;self.token=token;self.projects=tuple(projects)
        self.outbox=Outbox(repository)

    def call(self,tool,arguments,token):
        if not isinstance(token,str) or not hmac.compare_digest(token,self.token):raise PermissionError('Authentication required')
        project=arguments.get('project')
        if project not in self.projects:raise PermissionError('Project is outside registered scope')
        if tool=='events':return EventFeed(self.repo).read(project,arguments.get('after',0),arguments.get('limit',100))
        if tool=='incidents':return {'deliveries':self.outbox.list(project),'mode':'inbox-only'}
        if tool=='tasks':
            from snooze.control_views import task_row
            return {'tasks':[task_row(t) for t in self.repo.list(project)[:100]]}
        if tool=='task' and self.control:
            from snooze.control_views import managed_task_detail
            return managed_task_detail(self.control,project,arguments.get('task_id'))
        if tool=='control' and self.control:
            return asdict(self.control.apply(project,'mcp-coordinator',arguments['action'],arguments['target_id'],arguments.get('values',{}),arguments['expected_revision']))
        if tool=='register':
            self.outbox.register_coordinator(arguments['coordinator_id'],[project]);return {'registered':True}
        if tool=='acknowledge':return {'acknowledged':self.outbox.acknowledge(arguments['delivery_id'],arguments['coordinator_id'])}
        raise ValueError('Unknown/unsupported Snooze tool')

    def rpc(self,message):
        id=message.get('id');method=message.get('method')
        if method=='notifications/initialized':return None
        try:
            if method=='initialize':result={'protocolVersion':'2025-03-26','capabilities':{'tools':{}},'serverInfo':{'name':'snooze','version':'0.2.0'}}
            elif method=='tools/list':
                result={'tools':[{'name':'snooze_'+name,'description':'Scoped Snooze '+name,'inputSchema':{'type':'object','properties':{'project':{'type':'string'}},'required':['project'],'additionalProperties':True}} for name in ('events','incidents','tasks','task','control','register','acknowledge')]}
            elif method=='tools/call':
                params=message['params'];name=params['name']
                if not name.startswith('snooze_'):raise ValueError('Unknown tool')
                value=self.call(name[7:],params.get('arguments',{}),self.token)
                result={'content':[{'type':'text','text':json.dumps(value)}]}
            else:raise ValueError('Unsupported method')
            return {'jsonrpc':'2.0','id':id,'result':result}
        except (ValueError,KeyError,PermissionError,TypeError):
            return {'jsonrpc':'2.0','id':id,'error':{'code':-32602,'message':'Invalid or unauthorized Snooze request'}}

    def serve_stdio(self,input_stream,output_stream):
        for line in input_stream:
            if len(line)>65536:continue
            try:response=self.rpc(json.loads(line))
            except (ValueError,TypeError):response={'jsonrpc':'2.0','id':None,'error':{'code':-32700,'message':'Parse error'}}
            if response is not None:output_stream.write(json.dumps(response)+'\n');output_stream.flush()
