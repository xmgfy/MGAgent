"""
敏感信息过滤服务 - 基于安全规则过滤LLM输出
"""
import re
import logging
from typing import Optional, List, Dict
from sqlalchemy.orm import Session

from app.db.database import SessionLocal
from app.db.models import SecurityRule

logger = logging.getLogger(__name__)

# 内置敏感词（硬编码，始终生效）
BUILTIN_SENSITIVE_KEYWORDS = [
    # 系统信息
    'system prompt',
    '系统提示词',
    'prompt内容',
    'api_key',
    'api密钥',
    'secret_key',
    '数据库结构',
    'database schema',
    '内部机制',
    '工具实现',
    
    # 安全相关
    'password',
    '密码',
    'token',
    '密钥',
    'secret',
    'credential',
    
    # 数据库操作
    'drop table',
    'delete from',
    'update set',
    'insert into',
    'alter table',
    'truncate table',
    
    # 泄露风险
    '源代码',
    'source code',
    '配置文件',
    'config file',
    '内部接口',
    'internal api',
]

# 内置正则模式（硬编码，始终生效）
BUILTIN_SENSITIVE_PATTERNS = [
    # IP 地址
    (r'\b(?:\d{1,3}\.){3}\d{1,3}\b', '[IP地址]'),
    
    # 邮箱地址
    (r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', '[邮箱]'),
    
    # 手机号
    (r'\b1[3-9]\d{9}\b', '[手机号]'),
    
    # 身份证号
    (r'\b\d{17}[\dXx]\b', '[身份证号]'),
    
    # API Key 格式
    (r'(?i)(api[_-]?key|secret[_-]?key|access[_-]?key)\s*[:=]\s*["\']?[\w\-\.]+["\']?', '[API密钥]'),
    
    # Token 格式
    (r'(?i)(token|access[_-]?token|auth[_-]?token)\s*[:=]\s*["\']?[\w\-\.]+["\']?', '[令牌]'),
    
    # SQL 危险操作
    (r'(?i)\b(DROP|DELETE|UPDATE|INSERT|ALTER|TRUNCATE)\b\s+(TABLE|FROM|INTO|DATABASE)', '[危险SQL操作]'),
]


class ContentFilter:
    """内容过滤器"""
    
    def __init__(self):
        self._custom_rules: List[Dict] = []
        self._rules_loaded = False
    
    def _load_custom_rules(self, tenant_id: Optional[str] = None) -> List[Dict]:
        """从数据库加载自定义规则"""
        db = SessionLocal()
        try:
            query = db.query(SecurityRule).filter(SecurityRule.is_active == True)
            
            if tenant_id:
                # 加载全局规则 + 租户规则
                query = query.filter(
                    (SecurityRule.tenant_id == None) | (SecurityRule.tenant_id == tenant_id)
                )
            
            rules = query.order_by(SecurityRule.priority.desc()).all()
            
            return [
                {
                    'id': rule.id,
                    'rule_type': rule.rule_type,
                    'content': rule.content,
                    'action': rule.action,
                }
                for rule in rules
            ]
        except Exception as e:
            logger.error(f"加载安全规则失败: {e}")
            return []
        finally:
            db.close()
    
    def filter_content(
        self, 
        content: str, 
        tenant_id: Optional[str] = None,
        user_id: Optional[str] = None
    ) -> Dict:
        """
        过滤内容中的敏感信息
        
        Args:
            content: 待过滤的内容
            tenant_id: 租户ID（用于加载租户特定规则）
            user_id: 用户ID（用于日志记录）
            
        Returns:
            过滤结果字典：
            - filtered_content: 过滤后的内容
            - has_sensitive: 是否包含敏感信息
            - blocked: 是否被阻止（严重违规）
            - matched_rules: 匹配到的规则列表
        """
        result = {
            'filtered_content': content,
            'has_sensitive': False,
            'blocked': False,
            'matched_rules': []
        }
        
        # 1. 检查内置敏感关键词
        for keyword in BUILTIN_SENSITIVE_KEYWORDS:
            if self._contains_keyword(content, keyword):
                result['has_sensitive'] = True
                result['matched_rules'].append({
                    'type': 'builtin_keyword',
                    'pattern': keyword,
                    'action': 'mask'
                })
        
        # 2. 应用内置正则模式
        for pattern, replacement in BUILTIN_SENSITIVE_PATTERNS:
            matches = re.findall(pattern, content, re.IGNORECASE)
            if matches:
                result['has_sensitive'] = True
                result['matched_rules'].append({
                    'type': 'builtin_pattern',
                    'pattern': pattern,
                    'action': 'mask'
                })
                # 替换敏感内容
                result['filtered_content'] = re.sub(
                    pattern, 
                    replacement, 
                    result['filtered_content'],
                    flags=re.IGNORECASE
                )
        
        # 3. 加载并应用自定义规则
        custom_rules = self._load_custom_rules(tenant_id)
        for rule in custom_rules:
            if rule['rule_type'] == 'keyword':
                if self._contains_keyword(result['filtered_content'], rule['content']):
                    result['has_sensitive'] = True
                    result['matched_rules'].append(rule)
                    
                    if rule['action'] == 'block':
                        result['blocked'] = True
                    elif rule['action'] == 'mask':
                        result['filtered_content'] = self._mask_keyword(
                            result['filtered_content'], 
                            rule['content']
                        )
            
            elif rule['rule_type'] == 'regex':
                try:
                    matches = re.findall(rule['content'], result['filtered_content'], re.IGNORECASE)
                    if matches:
                        result['has_sensitive'] = True
                        result['matched_rules'].append(rule)
                        
                        if rule['action'] == 'block':
                            result['blocked'] = True
                        elif rule['action'] == 'mask':
                            result['filtered_content'] = re.sub(
                                rule['content'],
                                '[已过滤]',
                                result['filtered_content'],
                                flags=re.IGNORECASE
                            )
                except re.error as e:
                    logger.error(f"正则规则错误 {rule['id']}: {e}")
        
        # 4. 如果被阻止，返回拒绝消息
        if result['blocked']:
            result['filtered_content'] = "该请求涉及敏感内容，已被安全系统拦截。"
        
        # 5. 记录日志
        if result['has_sensitive']:
            logger.warning(
                f"检测到敏感内容: user={user_id}, tenant={tenant_id}, "
                f"rules={len(result['matched_rules'])}, blocked={result['blocked']}"
            )
        
        return result
    
    def _contains_keyword(self, content: str, keyword: str) -> bool:
        """检查内容是否包含关键词（不区分大小写）"""
        return keyword.lower() in content.lower()
    
    def _mask_keyword(self, content: str, keyword: str) -> str:
        """替换内容中的关键词为掩码"""
        return re.sub(
            re.escape(keyword),
            '[已过滤]',
            content,
            flags=re.IGNORECASE
        )


# 全局过滤器实例
_content_filter: Optional[ContentFilter] = None


def get_content_filter() -> ContentFilter:
    """获取内容过滤器实例"""
    global _content_filter
    if _content_filter is None:
        _content_filter = ContentFilter()
    return _content_filter
