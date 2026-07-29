// @ts-check
// Note: type annotations allow type checking and IDEs autocompletion

/** @type {import('@docusaurus/types').Config} */
const config = {
  title: 'MGAgent',
  tagline: '企业级智能体系统',
  favicon: 'img/favicon.ico',

  // Set the production url of your site here
  url: 'https://xmgfy.github.io',
  // Set the /<baseUrl>/ pathname under which your site is served
  // For GitHub pages deployment, it is often '/<projectName>/'
  baseUrl: '/',

  // GitHub pages deployment config.
  // If you aren't using GitHub pages, you don't need these.
  organizationName: 'xmgfy', // Usually your GitHub org/user name.
  projectName: 'mgagent', // Usually your repo name.

  onBrokenLinks: 'ignore',
  onBrokenMarkdownLinks: 'warn',

  // Even if you don't use internationalization, you can use this field to set
  // useful metadata like html lang. For example, if your site is Chinese, you
  // may want to replace "en" with "zh-Hans".
  i18n: {
    defaultLocale: 'zh-Hans',
    locales: ['zh-Hans'],
  },

  presets: [
    [
      'classic',
      /** @type {import('@docusaurus/preset-classic').Options} */
      ({
        docs: {
          sidebarPath: require.resolve('./sidebars.js'),
          // Please change this to your repo.
          // Remove 'editUrl' to enable 'edit this page' links
          // editUrl:
          //   'https://github.com/your-github-username/mgagent/tree/main/website',
        },
        blog: {
          showReadingTime: true,
          // Please change this to your repo.
          // Remove 'editUrl' to enable 'edit this page' links
          // editUrl:
          //   'https://github.com/your-github-username/mgagent/tree/main/website',
        },
        theme: {
          customCss: require.resolve('./src/css/custom.css'),
        },
      }),
    ],
  ],

  themeConfig:
    /** @type {import('@docusaurus/preset-classic').ThemeConfig} */
    ({
      navbar: {
        title: 'MGAgent',
        logo: {
          alt: 'MGAgent Logo',
          src: 'img/logo.svg',
        },
        items: [
          {
            type: 'docSidebar',
            sidebarId: 'tutorialSidebar',
            position: 'left',
            label: '文档',
          },
          {to: '/blog', label: '更新日志', position: 'left'},
          {
            href: 'https://github.com/xmgfy/mgagent',
            label: 'GitHub',
            position: 'right',
          },
        ],
      },
      footer: {
        style: 'dark',
        links: [
          {
            title: '文档',
            items: [
              {
                label: '快速开始',
                to: 'docs/intro',
              },
              {
                label: '架构设计',
                to: 'docs/architecture/overview',
              },
              {
                label: '部署指南',
                to: 'docs/deployment/local-development',
              },
            ],
          },
          {
            title: '项目',
            items: [
              {
                label: 'GitHub',
                href: 'https://github.com/xmgfy/mgagent',
              },
            ],
          },
          {
            title: '更多',
            items: [
              {
                label: '更新日志',
                to: '/blog',
              },
            ],
          },
        ],
        copyright: `Copyright © ${new Date().getFullYear()} MGAgent. Built with Docusaurus.`,
      },
      prism: {
        additionalLanguages: ['python', 'bash', 'yaml', 'sql', 'docker'],
      },
      markdown: {
        mermaid: true,
      },
    }),

  themes: ['@docusaurus/theme-mermaid'],
};

module.exports = config;
