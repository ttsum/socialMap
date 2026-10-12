import json
import re
import statistics
import time
from datetime import datetime, timezone
from pathlib import Path

from activities.services import activity_day, activity_period, recommend_with_meta
from .service import parse_query_with_meta
from .provider import GLMProvider


PROMPT_VERSION = 'intent-v2'
CORE_FIELDS = ('people', 'day', 'period', 'maxDistanceKm', 'budgetPerPerson', 'city')
PREFERENCE_FIELDS = ('preferences', 'uncertainFields')
NUMERALS = {'一': 1, '两': 2, '二': 2, '三': 3, '四': 4, '五': 5, '六': 6, '七': 7, '八': 8, '九': 9, '十': 10}


def _number(value):
    if value in NUMERALS:
        return NUMERALS[value]
    return float(value) if '.' in value else int(value)


class RuleMockProvider:
    """Deterministic baseline provider used to separate pipeline regressions from model variance."""

    def __init__(self):
        self.last_meta = {
            'model': 'mock-rule-v1',
            'promptVersion': PROMPT_VERSION,
            'latencyMs': 0,
            'fallbackUsed': False,
        }

    def complete_json(self, messages):
        query = str(messages[-1].get('content') or '').strip()
        companion = re.search(r'(?:和|带上|带)?([一二两三四五六七八九十\d]+)(?:位|个)朋友', query)
        total = re.search(r'(?:一共|共|我们)?([一二两三四五六七八九十\d]+)(?:个人|人)', query)
        distance = re.search(r'([一二两三四五六七八九十\d.]+)\s*(?:公里|千米|km)', query, re.I)
        budget = re.search(r'(?:人均|预算)[^\d]{0,6}(\d+(?:\.\d+)?)\s*(?:元|块)?', query)
        people = _number(companion.group(1)) + 1 if companion else _number(total.group(1)) if total else 1
        if '周日' in query or '星期日' in query or '星期天' in query:
            day = '周日'
        elif '周六' in query or '星期六' in query:
            day = '周六'
        else:
            day = '不限'
        if '下午' in query:
            period = '下午'
        elif '晚上' in query or '晚间' in query:
            period = '晚上'
        elif '上午' in query or '早上' in query:
            period = '上午'
        else:
            period = '不限'
        preferences = [name for name in ('安静', '热闹', '徒步', '散步', '桌游', '观影', '咖啡', '阅读') if name in query]
        if '看电影' in query and '观影' not in preferences:
            preferences.append('观影')
        if '朋友' in query:
            preferences.append('朋友聚会')
        if '不想爬山' in query:
            preferences = [x for x in preferences if x != '徒步']
        if '除了观影' in query:
            preferences = [x for x in preferences if x != '观影']
        if '免费' in query:
            budget_value = 0
        else:
            budget_value = float(budget.group(1)) if budget else 100
        distance_value = _number(distance.group(1)) if distance else 5
        uncertain = []
        if day == '不限' or '下周末' in query or any(x in query for x in ('今天', '明天', '后天')):
            uncertain.append('day')
        if period == '不限':
            uncertain.append('period')
        if not distance:
            uncertain.append('maxDistanceKm')
        if not budget and '免费' not in query:
            uncertain.append('budgetPerPerson')
        if any(x in query for x in ('不要太吵', '最好近一点', '别太高', '人少一点', '除了观影')):
            if 'preferences' not in uncertain and ('人少一点' in query or '除了观影' in query):
                uncertain.append('preferences')
        raw = {
            'query': query,
            'people': people,
            'day': day,
            'period': period,
            'maxDistanceKm': distance_value,
            'budgetPerPerson': budget_value,
            'preferences': preferences,
            'city': '长沙',
            'notes': [],
            'uncertainFields': uncertain,
        }
        return raw, 'mock-rule-v1'


def _equal(field, expected, actual):
    if field in ('maxDistanceKm', 'budgetPerPerson'):
        try:
            return abs(float(expected) - float(actual)) <= 0.001
        except (TypeError, ValueError):
            return False
    return expected == actual


def _f1(expected, actual):
    expected = set(expected or [])
    actual = set(actual or [])
    if not expected and not actual:
        return 1.0
    if not expected or not actual:
        return 0.0
    precision = len(expected & actual) / len(actual)
    recall = len(expected & actual) / len(expected)
    return 2 * precision * recall / (precision + recall) if precision + recall else 0.0


def _percent(value, total):
    return round(value / total, 4) if total else 0.0


def _recommendation_safety(intent):
    items, metadata, meta = recommend_with_meta(intent)
    hard_violations = []
    grounding_violations = []
    for item in items:
        group = getattr(item, 'group', None)
        joined = group.members.count() + sum(member.seats for member in group.memberships.all()) if group else 0
        if item.city != intent['city'] or item.price_per_person > intent['budgetPerPerson'] or item.distance_km > intent['maxDistanceKm']:
            hard_violations.append({'id': item.id, 'reason': 'city/budget/distance'})
        if item.capacity - joined < intent['people']:
            hard_violations.append({'id': item.id, 'reason': 'capacity'})
        if intent['day'] != '不限' and activity_day(item.start_time) != intent['day']:
            hard_violations.append({'id': item.id, 'reason': 'day'})
        if intent['period'] != '不限' and activity_period(item.start_time) != intent['period']:
            hard_violations.append({'id': item.id, 'reason': 'period'})
        reason = metadata[item.id]['reason']
        price = '免费' if item.price_per_person == 0 else '¥%s/人' % item.price_per_person.normalize()
        if str(item.distance_km) not in reason or price not in reason or str(intent['people']) not in reason:
            grounding_violations.append({'id': item.id, 'reason': 'ungrounded_reason'})
    return {
        'candidateCount': meta['candidateCount'],
        'matchedCount': meta['matchedCount'],
        'hardFilterViolations': hard_violations,
        'groundingViolations': grounding_violations,
    }


def evaluate(dataset_path, provider_name='mock', limit=None):
    cases = json.loads(Path(dataset_path).read_text(encoding='utf-8'))
    if limit:
        cases = cases[:limit]
    provider = RuleMockProvider() if provider_name == 'mock' else GLMProvider()
    field_hits = {field: 0 for field in CORE_FIELDS}
    field_total = {field: 0 for field in CORE_FIELDS}
    preference_scores = []
    uncertain_hits = 0
    uncertain_total = 0
    expected_errors = 0
    error_hits = 0
    failures = []
    latencies = []
    safety = []
    completed_cases = 0
    provider_errors = 0

    for case in cases:
        expected = case.get('expected', {})
        started = time.perf_counter()
        try:
            intent, meta = parse_query_with_meta(case['query'], provider=provider)
            error = None
        except Exception as exc:  # Provider and validation errors are part of the evaluation result.
            intent, meta, error = None, getattr(provider, 'last_meta', {}), str(exc)
        elapsed = round((time.perf_counter() - started) * 1000)
        latencies.append(elapsed)
        if expected.get('error'):
            expected_errors += 1
            if error:
                error_hits += 1
            else:
                failures.append({'id': case['id'], 'kind': 'expected_error_missing', 'predicted': intent})
            continue
        if error:
            provider_errors += 1
            failures.append({'id': case['id'], 'kind': 'unexpected_error', 'error': error})
            continue
        completed_cases += 1
        for field in CORE_FIELDS:
            field_total[field] += 1
            if _equal(field, expected.get(field), intent.get(field)):
                field_hits[field] += 1
            else:
                failures.append({'id': case['id'], 'kind': 'field_mismatch', 'field': field, 'expected': expected.get(field), 'predicted': intent.get(field)})
        preference_scores.append(_f1(expected.get('preferences'), intent.get('preferences')))
        expected_uncertain = set(expected.get('uncertainFields') or [])
        actual_uncertain = set(intent.get('uncertainFields') or [])
        uncertain_total += len(expected_uncertain)
        uncertain_hits += len(expected_uncertain & actual_uncertain)
        if expected_uncertain != actual_uncertain:
            failures.append({'id': case['id'], 'kind': 'uncertain_fields', 'expected': sorted(expected_uncertain), 'predicted': sorted(actual_uncertain)})
        try:
            safety.append(_recommendation_safety(intent))
        except Exception as exc:
            failures.append({'id': case['id'], 'kind': 'recommendation_eval_error', 'error': str(exc)})

    flat_latencies = sorted(latencies)
    p95_index = min(len(flat_latencies) - 1, max(0, int(len(flat_latencies) * 0.95) - 1)) if flat_latencies else 0
    hard_filter_violations = sum(len(item['hardFilterViolations']) for item in safety)
    grounding_violations = sum(len(item['groundingViolations']) for item in safety)
    return {
        'provider': provider_name,
        'promptVersion': PROMPT_VERSION,
        'caseCount': len(cases),
        'completedCases': completed_cases,
        'providerErrors': provider_errors,
        'status': 'completed' if provider_errors == 0 else 'blocked_or_partial',
        'generatedAt': datetime.now(timezone.utc).isoformat(),
        'metrics': {
            'coreFieldAccuracy': {field: _percent(field_hits[field], field_total[field]) for field in CORE_FIELDS},
            'coreFieldMacroAccuracy': _percent(sum(field_hits.values()), sum(field_total.values())),
            'preferenceF1': round(statistics.mean(preference_scores), 4) if preference_scores else 0.0,
            'uncertainFieldRecall': _percent(uncertain_hits, uncertain_total),
            'expectedErrorAccuracy': _percent(error_hits, expected_errors),
        },
        'latencyMs': {
            'mean': round(statistics.mean(latencies)) if latencies else 0,
            'p50': flat_latencies[len(flat_latencies) // 2] if flat_latencies else 0,
            'p95': flat_latencies[p95_index] if flat_latencies else 0,
            'max': max(flat_latencies) if flat_latencies else 0,
        },
        'recommendationSafety': {
            'evaluatedCases': len(safety),
            'hardFilterViolations': hard_filter_violations,
            'groundingViolations': grounding_violations,
            'matchedCount': sum(item['matchedCount'] for item in safety),
        },
        'failures': failures,
    }
