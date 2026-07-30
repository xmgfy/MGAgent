import React from 'react';
import clsx from 'clsx';
import Link from '@docusaurus/Link';
import useDocusaurusContext from '@docusaurus/useDocusaurusContext';
import Layout from '@theme/Layout';
import Heading from '@theme/Heading';
import styles from './index.module.css';

// SVG Icons for features
const ChatIcon = () => (
  <svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
    <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z" stroke="#2563eb" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
    <circle cx="8.5" cy="10.5" r="1" fill="#2563eb"/>
    <circle cx="12" cy="10.5" r="1" fill="#2563eb"/>
    <circle cx="15.5" cy="10.5" r="1" fill="#2563eb"/>
  </svg>
);

const BookIcon = () => (
  <svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
    <path d="M4 19.5A2.5 2.5 0 0 1 6.5 17H20" stroke="#2563eb" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
    <path d="M6.5 2H20v20H6.5A2.5 2.5 0 0 1 4 19.5v-15A2.5 2.5 0 0 1 6.5 2z" stroke="#2563eb" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
    <path d="M8 7h8M8 11h6" stroke="#3b82f6" strokeWidth="2" strokeLinecap="round"/>
  </svg>
);

const DatabaseIcon = () => (
  <svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
    <ellipse cx="12" cy="5" rx="9" ry="3" stroke="#2563eb" strokeWidth="2"/>
    <path d="M3 5v14c0 1.657 4.03 3 9 3s9-1.343 9-3V5" stroke="#2563eb" strokeWidth="2"/>
    <path d="M3 12c0 1.657 4.03 3 9 3s9-1.343 9-3" stroke="#3b82f6" strokeWidth="2"/>
  </svg>
);

const ToolIcon = () => (
  <svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
    <path d="M14.7 6.3a1 1 0 0 0 0 1.4l1.6 1.6a1 1 0 0 0 1.4 0l3.77-3.77a6 6 0 0 1-7.94 7.94l-6.91 6.91a2.12 2.12 0 0 1-3-3l6.91-6.91a6 6 0 0 1 7.94-7.94l-3.76 3.76z" stroke="#2563eb" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
  </svg>
);

const UsersIcon = () => (
  <svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
    <path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2" stroke="#2563eb" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
    <circle cx="9" cy="7" r="4" stroke="#2563eb" strokeWidth="2"/>
    <path d="M23 21v-2a4 4 0 0 0-3-3.87" stroke="#3b82f6" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
    <path d="M16 3.13a4 4 0 0 1 0 7.75" stroke="#3b82f6" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
  </svg>
);

const SettingsIcon = () => (
  <svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
    <circle cx="12" cy="12" r="3" stroke="#2563eb" strokeWidth="2"/>
    <path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 0 1 0 2.83 2 2 0 0 1-2.83 0l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-4 0v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 0 1-2.83-2.83l.06-.06a1.65 1.65 0 0 0 .33-1.82 1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1 0-4h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 0 1 2.83-2.83l.06.06a1.65 1.65 0 0 0 1.82.33H9a1.65 1.65 0 0 0 1-1.51V3a2 2 0 0 1 4 0v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 0 1 2.83 2.83l-.06.06a1.65 1.65 0 0 0-.33 1.82V9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 0 4h-.09a1.65 1.65 0 0 0-1.51 1z" stroke="#2563eb" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
  </svg>
);

function HomepageHeader() {
  const {siteConfig} = useDocusaurusContext();
  return (
    <header className={clsx(styles.heroBanner)}>
      <div className="container">
        <div style={{ position: 'relative', zIndex: 1 }}>
          <Heading as="h1" className={styles.heroTitle}>
            {siteConfig.title}
          </Heading>
          <p className={styles.heroSubtitle}>{siteConfig.tagline}</p>
          <p className={styles.heroDescription}>
            基于 LangChain 构建的企业级智能体系统，支持双技术栈架构，适用于智能客服、知识问答、数据分析等场景
          </p>
          <div className={styles.buttons}>
            <Link
              className={clsx('button', styles.primaryButton)}
              to="/docs/intro">
              🚀 快速开始
            </Link>
            <Link
              className={clsx('button', styles.secondaryButton)}
              to="/docs/architecture/overview">
              📖 查看架构
            </Link>
          </div>
        </div>
      </div>
    </header>
  );
}

const FeatureList = [
  {
    title: '智能对话',
    description: '基于大模型的多轮对话能力，支持上下文理解、意图识别、自然语言交互',
    gradient: 'linear-gradient(135deg, #dbeafe 0%, #bfdbfe 100%)',
    icon: <ChatIcon />,
  },
  {
    title: '知识库检索',
    description: '向量检索增强的 RAG 能力，支持 PDF、Word、Markdown 等多种文档格式',
    gradient: 'linear-gradient(135deg, #e0e7ff 0%, #c7d2fe 100%)',
    icon: <BookIcon />,
  },
  {
    title: '数据库查询',
    description: '自然语言转 SQL，支持 MySQL、SQLite，自动生成和优化查询语句',
    gradient: 'linear-gradient(135deg, #cffafe 0%, #a5f3fc 100%)',
    icon: <DatabaseIcon />,
  },
  {
    title: '多工具调用',
    description: '支持计算器、API 调用、搜索引擎等多种工具，扩展 Agent 能力',
    gradient: 'linear-gradient(135deg, #ede9fe 0%, #ddd6fe 100%)',
    icon: <ToolIcon />,
  },
  {
    title: '多租户管理',
    description: '支持多用户、多知识库隔离，管理员审批流程，使用配额管理',
    gradient: 'linear-gradient(135deg, #e0f2fe 0%, #bae6fd 100%)',
    icon: <UsersIcon />,
  },
  {
    title: '模型配置',
    description: 'Admin 端统一管理大模型配置，动态切换，实时生效，无需重启',
    gradient: 'linear-gradient(135deg, #dbeafe 0%, #93c5fd 100%)',
    icon: <SettingsIcon />,
  },
];

function Feature({title, description, gradient, icon}) {
  return (
    <div className={clsx('col col--4')}>
      <div className={styles.featureCard}>
        <div className={styles.featureIcon} style={{ background: gradient }}>
          {icon}
        </div>
        <Heading as="h3" className={styles.featureTitle}>{title}</Heading>
        <p className={styles.featureDescription}>{description}</p>
      </div>
    </div>
  );
}

const StatsSection = () => (
  <section className={styles.stats}>
    <div className="container">
      <div className="row">
        <div className={clsx('col col--3', styles.statItem)}>
          <div className={styles.statNumber}>2</div>
          <div className={styles.statLabel}>技术栈方案</div>
        </div>
        <div className={clsx('col col--3', styles.statItem)}>
          <div className={styles.statNumber}>5+</div>
          <div className={styles.statLabel}>核心功能模块</div>
        </div>
        <div className={clsx('col col--3', styles.statItem)}>
          <div className={styles.statNumber}>100%</div>
          <div className={styles.statLabel}>模型配置动态化</div>
        </div>
        <div className={clsx('col col--3', styles.statItem)}>
          <div className={styles.statNumber}>∞</div>
          <div className={styles.statLabel}>可扩展能力</div>
        </div>
      </div>
    </div>
  </section>
);

export default function Home() {
  const {siteConfig} = useDocusaurusContext();
  return (
    <Layout
      title="首页"
      description={`${siteConfig.title} - ${siteConfig.tagline}`}>
      <HomepageHeader />
      <main>
        <section className={styles.features}>
          <div className="container">
            <div className="row">
              {FeatureList.map((props, idx) => (
                <Feature key={idx} {...props} />
              ))}
            </div>
          </div>
        </section>
        <StatsSection />
      </main>
    </Layout>
  );
}
