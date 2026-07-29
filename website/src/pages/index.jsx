import React from 'react';
import clsx from 'clsx';
import Link from '@docusaurus/Link';
import useDocusaurusContext from '@docusaurus/useDocusaurusContext';
import Layout from '@theme/Layout';
import Translate, {translate} from '@docusaurus/Translate';
import Heading from '@theme/Heading';
import styles from './index.module.css';

function HomepageHeader() {
  const {siteConfig} = useDocusaurusContext();
  return (
    <header className={clsx('hero hero--primary', styles.heroBanner)}>
      <div className="container">
        <Heading as="h1" className="hero__title">
          {siteConfig.title}
        </Heading>
        <p className="hero__subtitle">{siteConfig.tagline}</p>
        <div className={styles.buttons}>
          <Link
            className="button button--secondary button--lg"
            to="/docs/intro">
            快速开始 →
          </Link>
        </div>
      </div>
    </header>
  );
}

const FeatureList = [
  {
    title: '双技术栈架构',
    Svg: require('@site/static/img/feature-stack.svg').default,
    description: (
      <>
        支持 SQLite + ChromaDB 开发方案和 MySQL + Milvus 生产方案，灵活切换。
      </>
    ),
  },
  {
    title: '企业级部署',
    Svg: require('@site/static/img/feature-deploy.svg').default,
    description: (
      <>
        Docker Compose 分层部署，基础设施与应用层分离，一键启动。
      </>
    ),
  },
  {
    title: '模型配置管理',
    Svg: require('@site/static/img/feature-model.svg').default,
    description: (
      <>
        通过 Admin 端统一管理大模型配置，实时生效，无需重启。
      </>
    ),
  },
];

function Feature({Svg, title, description}) {
  return (
    <div className={clsx('col col--4')}>
      <div className="text--center">
        <Svg className={styles.featureSvg} role="img" />
      </div>
      <div className="text--center padding-horiz--md">
        <Heading as="h3">{title}</Heading>
        <p>{description}</p>
      </div>
    </div>
  );
}

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
      </main>
    </Layout>
  );
}
