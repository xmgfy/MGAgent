"""
种子数据脚本 - 为 admin 前端添加测试数据
"""
import sys
import os
import uuid
from datetime import datetime, timedelta, timezone

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy.orm import sessionmaker
from app.db.database import init_engine
from app.db.models import (
    Admin, Tenant, AdminSession, ModelConfig,
    SystemNotification, User, ChatSession, ChatMessage,
    Document, AnonymousStats, Base
)

def hash_password(password: str) -> str:
    """使用 bcrypt 哈希密码"""
    import bcrypt
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

def seed():
    """添加种子数据"""
    print("开始添加种子数据...")
    
    # 初始化引擎
    engine = init_engine()
    
    # 删除所有表并重新创建（确保与模型一致）
    print("重建数据库表结构...")
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    session = SessionLocal()
    
    try:
        # 0. 添加平台管理员
        print("添加平台管理员...")
        platform_admin = Admin(
            id=str(uuid.uuid4()),
            username="admin",
            email="admin@mgagent.com",
            hashed_password=hash_password("admin123"),
            role="platform_admin",
            tenant_id=None,
            status="active"
        )
        session.add(platform_admin)
        session.flush()
        print(f"  添加了平台管理员: admin / admin123")
        
        # 1. 添加租户
        print("添加租户数据...")
        tenants = [
            Tenant(
                id=str(uuid.uuid4()),
                name="科技公司A",
                description="专注于人工智能研发的科技公司",
                status="active",
                max_users=500
            ),
            Tenant(
                id=str(uuid.uuid4()),
                name="教育机构B",
                description="在线教育服务提供商",
                status="active",
                max_users=1000
            ),
            Tenant(
                id=str(uuid.uuid4()),
                name="金融公司C",
                description="金融科技解决方案提供商",
                status="active",
                max_users=200
            )
        ]
        for t in tenants:
            session.add(t)
        session.flush()
        
        tenant_ids = [t.id for t in tenants]
        print(f"  添加了 {len(tenants)} 个租户")
        
        # 2. 添加租户管理员
        print("添加租户管理员...")
        tenant_admins = [
            Admin(
                id=str(uuid.uuid4()),
                username="tenant_admin_a",
                email="admin@company-a.com",
                hashed_password=hash_password("admin123"),
                role="tenant_admin",
                tenant_id=tenant_ids[0],
                status="active"
            ),
            Admin(
                id=str(uuid.uuid4()),
                username="tenant_admin_b",
                email="admin@company-b.com",
                hashed_password=hash_password("admin123"),
                role="tenant_admin",
                tenant_id=tenant_ids[1],
                status="active"
            )
        ]
        for a in tenant_admins:
            session.add(a)
        session.flush()
        
        # 3. 添加普通用户
        print("添加普通用户...")
        users = []
        user_data = [
            ("alice", "alice@example.com", "user", tenant_ids[0]),
            ("bob", "bob@example.com", "user", tenant_ids[0]),
            ("charlie", "charlie@example.com", "user", tenant_ids[1]),
            ("diana", "diana@example.com", "user", tenant_ids[1]),
            ("eve", "eve@example.com", "user", tenant_ids[2]),
            ("frank", "frank@example.com", "user", None),
            ("grace", "grace@example.com", "user", None),
            ("henry", "henry@example.com", "admin", tenant_ids[0]),
        ]
        
        for username, email, role, tid in user_data:
            users.append(User(
                id=str(uuid.uuid4()),
                username=username,
                email=email,
                hashed_password=hash_password("user123"),
                role=role,
                status="active",
                tenant_id=tid,
                chat_count=0,
                max_chats=10
            ))
        
        for u in users:
            session.add(u)
        session.flush()
        
        user_ids = [u.id for u in users]
        print(f"  添加了 {len(users)} 个用户")
        
        # 4. 添加聊天会话和消息
        print("添加聊天数据...")
        now = datetime.now(timezone.utc)
        sessions_and_messages = [
            # Alice 的会话
            (user_ids[0], "关于产品介绍的对话", [
                ("user", "你好，请介绍一下你们的产品功能。"),
                ("assistant", "您好！我们的产品主要提供以下功能：\n1. 智能对话系统\n2. 知识库管理\n3. 多租户支持\n4. API 集成能力\n\n请问您对哪个功能最感兴趣？"),
                ("user", "知识库管理怎么用？"),
                ("assistant", "知识库管理功能允许您上传文档，系统会自动进行向量化处理，然后可以通过对话来检索和引用相关内容。支持 PDF、Word、Markdown 等多种格式。")
            ]),
            # Bob 的会话
            (user_ids[1], "技术支持咨询", [
                ("user", "我使用中遇到了问题，对话响应很慢。"),
                ("assistant", "您好！对话响应速度可能与以下因素有关：\n1. 网络延迟\n2. 模型服务负载\n3. 知识库检索时间\n\n建议您检查网络连接，或联系管理员查看系统状态。"),
                ("user", "好的，谢谢。"),
                ("assistant", "不客气！如果还有其他问题，随时可以问我。")
            ]),
            # Charlie 的会话
            (user_ids[2], "英语学习助手", [
                ("user", "帮我翻译这句话：今天天气真好。"),
                ("assistant", "The weather is really nice today."),
                ("user", "再帮我润色一下，让它更自然。"),
                ("assistant", "Here are some more natural ways to express this:\n1. What a beautiful day!\n2. The weather is lovely today.\n3. It's a gorgeous day outside.")
            ]),
            # Diana 的会话
            (user_ids[3], "代码审查助手", [
                ("user", "帮我检查这段 Python 代码的性能问题。"),
                ("assistant", "好的，您可以将代码分享给我，我会从以下方面进行分析：\n1. 时间复杂度\n2. 空间复杂度\n3. 潜在的性能瓶颈\n4. 优化建议")
            ]),
            # Eve 的会话
            (user_ids[4], "数据分析咨询", [
                ("user", "如何做数据可视化？"),
                ("assistant", "数据可视化可以通过多种工具实现：\n1. Python: Matplotlib, Seaborn, Plotly\n2. JavaScript: D3.js, Chart.js\n3. BI 工具: Tableau, Power BI\n\n您的具体需求是什么？")
            ]),
            # Frank 的会话（无租户）
            (user_ids[5], "通用问题咨询", [
                ("user", "什么是人工智能？"),
                ("assistant", "人工智能（AI）是计算机科学的一个分支，致力于创建能够执行通常需要人类智能的任务的系统，包括学习、推理、问题解决、感知和语言理解等。")
            ])
        ]
        
        total_sessions = 0
        total_messages = 0
        
        for uid, title, messages in sessions_and_messages:
            session_obj = ChatSession(
                id=str(uuid.uuid4()),
                user_id=uid,
                title=title,
                created_at=now - timedelta(minutes=30 * len(messages)),
                updated_at=now
            )
            session.add(session_obj)
            session.flush()
            
            for i, (role, content) in enumerate(messages):
                msg = ChatMessage(
                    session_id=session_obj.id,
                    role=role,
                    content=content,
                    created_at=now - timedelta(minutes=30 * (len(messages) - i))
                )
                session.add(msg)
                total_messages += 1
            
            total_sessions += 1
        
        print(f"  添加了 {total_sessions} 个会话，{total_messages} 条消息")
        
        # 5. 添加系统通知
        print("添加系统通知...")
        notifications = [
            SystemNotification(
                id=str(uuid.uuid4()),
                type="system",
                title="系统升级通知",
                message="系统将于本周六凌晨进行升级维护，预计停机时间为2小时。",
                admin_id=None,
                is_read=False
            ),
            SystemNotification(
                id=str(uuid.uuid4()),
                type="feature",
                title="新功能上线",
                message="知识库管理功能已上线，支持上传 PDF、Word、Markdown 等格式文档。",
                admin_id=None,
                is_read=False
            ),
            SystemNotification(
                id=str(uuid.uuid4()),
                type="warning",
                title="存储空间告警",
                message="检测到租户「科技公司A」的存储空间使用率已达到 85%，建议及时清理。",
                admin_id=tenant_admins[0].id if tenant_admins else None,
                is_read=False
            ),
            SystemNotification(
                id=str(uuid.uuid4()),
                type="info",
                title="API 使用统计",
                message="本月 API 调用量统计已更新，请查看仪表板了解详情。",
                admin_id=None,
                is_read=True
            ),
            SystemNotification(
                id=str(uuid.uuid4()),
                type="system",
                title="安全提醒",
                message="建议定期更换管理员密码，确保账户安全。",
                admin_id=None,
                is_read=True
            ),
            SystemNotification(
                id=str(uuid.uuid4()),
                type="feature",
                title="模型更新",
                message="已添加新的嵌入模型 BGE-M3，支持多语言知识库检索。",
                admin_id=None,
                is_read=False
            ),
        ]
        for n in notifications:
            session.add(n)
        
        print(f"  添加了 {len(notifications)} 条通知")
        
        # 6. 添加模型配置
        print("添加模型配置...")
        model_configs = [
            ModelConfig(
                id=str(uuid.uuid4()),
                name="GPT-4 对话模型",
                api_key="sk-test-key-123456",
                api_base="https://api.openai.com/v1",
                model_name="gpt-4o",
                is_active=True
            ),
            ModelConfig(
                id=str(uuid.uuid4()),
                name="嵌入模型 BGE-M3",
                api_key="sk-test-key-embedding",
                api_base="https://api.example.com/v1",
                model_name="bge-m3",
                is_active=True
            ),
            ModelConfig(
                id=str(uuid.uuid4()),
                name="GPT-3.5 对话模型",
                api_key="sk-test-key-789012",
                api_base="https://api.openai.com/v1",
                model_name="gpt-3.5-turbo",
                is_active=False
            )
        ]
        for m in model_configs:
            session.add(m)
        
        print(f"  添加了 {len(model_configs)} 个模型配置")
        
        # 7. 添加文档记录
        print("添加文档记录...")
        documents = [
            Document(
                id=str(uuid.uuid4()),
                filename="产品说明书.pdf",
                file_type="pdf",
                file_size=256000,
                status="indexed",
                tenant_id=tenant_ids[0]
            ),
            Document(
                id=str(uuid.uuid4()),
                filename="API文档.md",
                file_type="markdown",
                file_size=45000,
                status="indexed",
                tenant_id=tenant_ids[0]
            ),
            Document(
                id=str(uuid.uuid4()),
                filename="用户手册.docx",
                file_type="docx",
                file_size=128000,
                status="processing",
                tenant_id=tenant_ids[1]
            ),
            Document(
                id=str(uuid.uuid4()),
                filename="培训资料.pdf",
                file_type="pdf",
                file_size=512000,
                status="uploaded",
                tenant_id=tenant_ids[2]
            ),
            Document(
                id=str(uuid.uuid4()),
                filename="技术白皮书.pdf",
                file_type="pdf",
                file_size=1024000,
                status="indexed",
                tenant_id=None
            ),
        ]
        for d in documents:
            session.add(d)
        
        print(f"  添加了 {len(documents)} 条文档记录")
        
        # 8. 添加匿名统计
        print("添加匿名统计数据...")
        for i in range(7):
            stats = AnonymousStats(
                chat_count=10 + i * 5,
                max_chats=3,
                last_used_at=now - timedelta(days=i)
            )
            session.add(stats)
        
        print("  添加了 7 天的匿名统计数据")
        
        # 提交事务
        session.commit()
        print("\n✅ 种子数据添加成功！")
        print("\n数据摘要：")
        print(f"  - 平台管理员：1 个 (admin / admin123)")
        print(f"  - 租户：{len(tenants)} 个")
        print(f"  - 租户管理员：{len(tenant_admins)} 个 (admin123)")
        print(f"  - 用户：{len(users)} 个 (user123)")
        print(f"  - 聊天会话：{total_sessions} 个")
        print(f"  - 聊天消息：{total_messages} 条")
        print(f"  - 系统通知：{len(notifications)} 条")
        print(f"  - 模型配置：{len(model_configs)} 个")
        print(f"  - 文档记录：{len(documents)} 条")
        print(f"  - 匿名统计：7 天数据")
        
    except Exception as e:
        session.rollback()
        print(f"\n❌ 添加种子数据失败：{e}")
        import traceback
        traceback.print_exc()
        raise
    finally:
        session.close()

if __name__ == "__main__":
    seed()
