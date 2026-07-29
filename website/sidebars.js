/** @type {import('@docusaurus/plugin-content-docs').SidebarsConfig} */
const sidebars = {
  tutorialSidebar: [
    {
      type: 'doc',
      id: 'intro',
      label: '简介',
    },
    {
      type: 'category',
      label: '🚀 快速开始',
      items: [
        'getting-started/installation',
        'getting-started/quick-start',
        'getting-started/configuration',
      ],
    },
    {
      type: 'category',
      label: '🏗️ 架构设计',
      items: [
        'architecture/overview',
        'architecture/dual-stack',
        'architecture/database',
        'architecture/model-config',
      ],
    },
    {
      type: 'category',
      label: '📦 部署指南',
      items: [
        'deployment/local-development',
        'deployment/docker-deployment',
        'deployment/mysql-deployment',
        'deployment/production-deployment',
      ],
    },
    {
      type: 'category',
      label: '🛠️ 开发指南',
      items: [
        'development/project-structure',
        'development/scripts',
        'development/api-reference',
      ],
    },
    {
      type: 'category',
      label: '🔧 配置说明',
      items: [
        'configuration/environment-variables',
        'configuration/nginx',
        'configuration/docker',
      ],
    },
    {
      type: 'category',
      label: '❓ 常见问题',
      items: [
        'troubleshooting/faq',
        'troubleshooting/common-issues',
      ],
    },
  ],
};

module.exports = sidebars;
