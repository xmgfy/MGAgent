"""
数据库迁移脚本 - 添加 security_rules 表（支持 MySQL 和 SQLite）
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.config.settings import settings
from sqlalchemy import create_engine, text


def migrate():
    """执行迁移"""
    database_url = settings.DATABASE_URL
    
    try:
        engine = create_engine(database_url)
        with engine.connect() as conn:
            # 检查 security_rules 表是否已存在
            result = conn.execute(text("""
                SELECT COUNT(*) FROM information_schema.tables 
                WHERE table_name = 'security_rules'
            """))
            exists = result.fetchone()[0]
            
            if exists:
                print("security_rules 表已存在，跳过创建")
                return True
            
            # 创建 security_rules 表
            conn.execute(text("""
                CREATE TABLE security_rules (
                    id VARCHAR(64) PRIMARY KEY,
                    tenant_id VARCHAR(64) NULL,
                    rule_type VARCHAR(20) NOT NULL COMMENT 'keyword, pattern, regex',
                    content TEXT NOT NULL,
                    action VARCHAR(20) NOT NULL DEFAULT 'mask' COMMENT 'block, mask, log',
                    priority INT DEFAULT 0,
                    is_active TINYINT(1) DEFAULT 1,
                    description VARCHAR(500) NULL,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                    INDEX idx_security_rules_tenant_id (tenant_id),
                    INDEX idx_security_rules_is_active (is_active)
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='安全规则表'
            """))
            
            # 插入默认规则
            default_rules = [
                {
                    'id': 'default_system_prompt',
                    'rule_type': 'keyword',
                    'content': '系统提示词',
                    'action': 'block',
                    'priority': 100,
                    'description': '禁止泄露系统提示词内容'
                },
                {
                    'id': 'default_api_key',
                    'rule_type': 'keyword',
                    'content': 'api_key',
                    'action': 'mask',
                    'priority': 90,
                    'description': '过滤API密钥相关内容'
                },
                {
                    'id': 'default_database_schema',
                    'rule_type': 'keyword',
                    'content': '数据库结构',
                    'action': 'block',
                    'priority': 80,
                    'description': '禁止泄露数据库结构'
                },
                {
                    'id': 'default_sql_safety',
                    'rule_type': 'regex',
                    'content': '(?i)\\b(DROP|DELETE|UPDATE|INSERT|ALTER)\\b\\s+(TABLE|FROM|INTO|DATABASE)',
                    'action': 'block',
                    'priority': 100,
                    'description': '禁止生成危险SQL语句'
                },
                {
                    'id': 'default_privacy_email',
                    'rule_type': 'regex',
                    'content': '\\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\\.[A-Z|a-z]{2,}\\b',
                    'action': 'mask',
                    'priority': 70,
                    'description': '过滤邮箱地址'
                },
                {
                    'id': 'default_privacy_phone',
                    'rule_type': 'regex',
                    'content': '\\b1[3-9]\\d{9}\\b',
                    'action': 'mask',
                    'priority': 70,
                    'description': '过滤手机号'
                },
            ]
            
            for rule in default_rules:
                conn.execute(text("""
                    INSERT INTO security_rules (id, rule_type, content, action, priority, description)
                    VALUES (:id, :rule_type, :content, :action, :priority, :description)
                """), rule)
            
            conn.commit()
            print("security_rules 表创建成功，默认规则已插入")
            return True
        
    except Exception as e:
        print(f"迁移失败: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = migrate()
    sys.exit(0 if success else 1)
