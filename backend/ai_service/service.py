from rest_framework.exceptions import APIException, ValidationError
from .provider import GLMProvider, ProviderError
from activities.services import validate_intent

PROMPT_VERSION = 'intent-v2'

SYSTEM_PROMPT = '''你是团团团的需求解析器。只输出 JSON，不要 Markdown。字段必须为：
query(string), people(integer 1-20, 包含本人), day(不限/周六/周日), period(不限/上午/下午/晚上),
maxDistanceKm(number), budgetPerPerson(number), preferences(string array), city(string), notes(string array),
uncertainFields(string array)。城市未提及时使用长沙；无法确认的日期、比较或否定表达放入 notes，并把对应字段名放入 uncertainFields，不要臆测。
价格、距离、容量和活动是否存在不属于你的判断范围。'''


def parse_query_with_meta(query, provider=None):
    if not isinstance(query, str) or not query.strip() or len(query.strip()) > 300:
        raise ValidationError({'query': '需求不能为空且最多 300 字'})
    provider = provider or GLMProvider()
    try:
        raw, model = provider.complete_json([{'role': 'system', 'content': SYSTEM_PROMPT}, {'role': 'user', 'content': query.strip()}])
    except ProviderError as error:
        exception = APIException('AI 服务暂时不可用：' + str(error))
        exception.status_code = error.status or 502
        raise exception
    required = ('people', 'day', 'period', 'maxDistanceKm', 'budgetPerPerson', 'preferences', 'city', 'notes')
    if any(key not in raw for key in required):
        raise ValidationError({'detail': 'AI 返回字段不完整，请重试'})
    try:
        intent = validate_intent(raw)
    except ValidationError:
        raise ValidationError({'detail': 'AI 返回的筛选条件无效，请重试'})
    intent.update({
        'query': query.strip(),
        'notes': [str(x) for x in raw.get('notes', [])][:10],
        'uncertainFields': [str(x) for x in raw.get('uncertainFields', []) if str(x).strip()][:10],
    })
    meta = dict(getattr(provider, 'last_meta', {}) or {})
    meta.update({'model': model, 'promptVersion': PROMPT_VERSION})
    return intent, meta


def parse_query(query, provider=None):
    """Backward-compatible intent-only helper for callers outside the API view."""
    intent, _ = parse_query_with_meta(query, provider=provider)
    return intent
