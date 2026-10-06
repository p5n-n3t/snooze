"""Documented LightSprint operations. Ambiguous launches are never retried here."""
import re
from snooze.adapters.base import BaseAdapter, OPERATIONS, UnsupportedOperation
from snooze.transport import normalize_status


def identifier(value):
    if not isinstance(value, str) or not re.fullmatch(r'[A-Za-z0-9_-]{1,160}', value): raise ValueError('Invalid provider identifier')
    return value


class LightSprintAdapter(BaseAdapter):
    def __init__(self, config, transport):
        self.config = config
        self.transport = transport

    def capabilities(self):
        result = super().capabilities()
        if self.config.get('mcp_key'):
            result['observe'] = {'supported': True, 'reason': None}
        for op in self.config.get('verified_operations', []):
            if op in ('resume', 'cancel'): result[op] = {'supported': True, 'reason': None}
        if self.config.get('stack_id') and self.config.get('launch_verified') and self.config.get('models'):
            result['launch'] = {'supported': True, 'reason': None}
        result['collect']['reason'] = 'Configure a verified artifact collector; provider idle alone is not output.'
        result['reconcile']['reason'] = 'Provider launch lookup by idempotency key is unverified; manual reconciliation required.'
        return result

    def observe(self, session_id):
        self.require('observe')
        return normalize_status(self.transport.request(self.config['mcp_key'], 'GET', f'/api/agent-sessions/{identifier(session_id)}/status'))

    def launch(self, task, attempt):
        self.require('launch')
        requested_model = task.requirements.get('model')
        effort = task.requirements.get('effort', 'low')
        if requested_model not in self.config['models'] or effort not in self.config.get('efforts', ['low']):
            raise UnsupportedOperation('Requested model/effort is not verified for this account')
        key = self.config['mcp_key']
        created = self.transport.request(key, 'POST', '/api/tasks', {'title': 'Snooze ' + task.id, 'scope': 'stack', 'stackId': identifier(self.config['stack_id'])})
        provider_id = identifier(created.get('task', {}).get('id'))
        # Task creation is durable; record the remote ID for any later ambiguity.
        self.transport.request(key, 'PATCH', '/api/tasks/' + provider_id, {'description': attempt.get('instructions', ''), 'complexity': 'low'})
        result = self.transport.request(key, 'POST', f'/api/tasks/{provider_id}/lightsprint-agents/codex',
                                        {'model': requested_model, 'reasoningEffort': effort, 'autoMerge': False})
        sid = identifier(result.get('id'))
        return {'session_id': sid, 'state': 'running', 'provider_task_id': provider_id, 'branch': result.get('branchName'), 'requested_model': requested_model, 'requested_effort': effort}

    def resume(self, session_id, attempt):
        self.require('resume')
        self.transport.request(self.config['mcp_key'], 'POST', f'/api/agent-sessions/{identifier(session_id)}/chat', {'content': attempt.get('instructions', '')})
        return {'state': 'pending', 'session_id': session_id}

    def cancel(self, session_id):
        self.require('cancel')
        self.transport.request(self.config['mcp_key'], 'POST', f'/api/agent-sessions/{identifier(session_id)}/cancel', {})
        return {'state': 'pending', 'session_id': session_id}
