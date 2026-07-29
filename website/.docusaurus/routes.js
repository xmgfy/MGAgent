import React from 'react';
import ComponentCreator from '@docusaurus/ComponentCreator';

export default [
  {
    path: '/__docusaurus/debug',
    component: ComponentCreator('/__docusaurus/debug', '5ff'),
    exact: true
  },
  {
    path: '/__docusaurus/debug/config',
    component: ComponentCreator('/__docusaurus/debug/config', '5ba'),
    exact: true
  },
  {
    path: '/__docusaurus/debug/content',
    component: ComponentCreator('/__docusaurus/debug/content', 'a2b'),
    exact: true
  },
  {
    path: '/__docusaurus/debug/globalData',
    component: ComponentCreator('/__docusaurus/debug/globalData', 'c3c'),
    exact: true
  },
  {
    path: '/__docusaurus/debug/metadata',
    component: ComponentCreator('/__docusaurus/debug/metadata', '156'),
    exact: true
  },
  {
    path: '/__docusaurus/debug/registry',
    component: ComponentCreator('/__docusaurus/debug/registry', '88c'),
    exact: true
  },
  {
    path: '/__docusaurus/debug/routes',
    component: ComponentCreator('/__docusaurus/debug/routes', '000'),
    exact: true
  },
  {
    path: '/blog',
    component: ComponentCreator('/blog', '98b'),
    exact: true
  },
  {
    path: '/docs',
    component: ComponentCreator('/docs', '566'),
    routes: [
      {
        path: '/docs',
        component: ComponentCreator('/docs', '782'),
        routes: [
          {
            path: '/docs',
            component: ComponentCreator('/docs', 'c01'),
            routes: [
              {
                path: '/docs/architecture/database',
                component: ComponentCreator('/docs/architecture/database', 'd7f'),
                exact: true,
                sidebar: "tutorialSidebar"
              },
              {
                path: '/docs/architecture/dual-stack',
                component: ComponentCreator('/docs/architecture/dual-stack', '17a'),
                exact: true,
                sidebar: "tutorialSidebar"
              },
              {
                path: '/docs/architecture/model-config',
                component: ComponentCreator('/docs/architecture/model-config', '2aa'),
                exact: true,
                sidebar: "tutorialSidebar"
              },
              {
                path: '/docs/architecture/overview',
                component: ComponentCreator('/docs/architecture/overview', '833'),
                exact: true,
                sidebar: "tutorialSidebar"
              },
              {
                path: '/docs/configuration/docker',
                component: ComponentCreator('/docs/configuration/docker', '287'),
                exact: true,
                sidebar: "tutorialSidebar"
              },
              {
                path: '/docs/configuration/environment-variables',
                component: ComponentCreator('/docs/configuration/environment-variables', 'e8e'),
                exact: true,
                sidebar: "tutorialSidebar"
              },
              {
                path: '/docs/configuration/nginx',
                component: ComponentCreator('/docs/configuration/nginx', '9dc'),
                exact: true,
                sidebar: "tutorialSidebar"
              },
              {
                path: '/docs/deployment/docker-deployment',
                component: ComponentCreator('/docs/deployment/docker-deployment', 'e05'),
                exact: true,
                sidebar: "tutorialSidebar"
              },
              {
                path: '/docs/deployment/local-development',
                component: ComponentCreator('/docs/deployment/local-development', '8b0'),
                exact: true,
                sidebar: "tutorialSidebar"
              },
              {
                path: '/docs/deployment/mysql-deployment',
                component: ComponentCreator('/docs/deployment/mysql-deployment', '5d2'),
                exact: true,
                sidebar: "tutorialSidebar"
              },
              {
                path: '/docs/deployment/production-deployment',
                component: ComponentCreator('/docs/deployment/production-deployment', '933'),
                exact: true,
                sidebar: "tutorialSidebar"
              },
              {
                path: '/docs/development/api-reference',
                component: ComponentCreator('/docs/development/api-reference', 'a86'),
                exact: true,
                sidebar: "tutorialSidebar"
              },
              {
                path: '/docs/development/project-structure',
                component: ComponentCreator('/docs/development/project-structure', 'f96'),
                exact: true,
                sidebar: "tutorialSidebar"
              },
              {
                path: '/docs/development/scripts',
                component: ComponentCreator('/docs/development/scripts', '05d'),
                exact: true,
                sidebar: "tutorialSidebar"
              },
              {
                path: '/docs/getting-started/configuration',
                component: ComponentCreator('/docs/getting-started/configuration', '468'),
                exact: true,
                sidebar: "tutorialSidebar"
              },
              {
                path: '/docs/getting-started/installation',
                component: ComponentCreator('/docs/getting-started/installation', '267'),
                exact: true,
                sidebar: "tutorialSidebar"
              },
              {
                path: '/docs/getting-started/quick-start',
                component: ComponentCreator('/docs/getting-started/quick-start', '09c'),
                exact: true,
                sidebar: "tutorialSidebar"
              },
              {
                path: '/docs/intro',
                component: ComponentCreator('/docs/intro', '61d'),
                exact: true,
                sidebar: "tutorialSidebar"
              },
              {
                path: '/docs/troubleshooting/common-issues',
                component: ComponentCreator('/docs/troubleshooting/common-issues', '944'),
                exact: true,
                sidebar: "tutorialSidebar"
              },
              {
                path: '/docs/troubleshooting/faq',
                component: ComponentCreator('/docs/troubleshooting/faq', '8fb'),
                exact: true,
                sidebar: "tutorialSidebar"
              }
            ]
          }
        ]
      }
    ]
  },
  {
    path: '/',
    component: ComponentCreator('/', '070'),
    exact: true
  },
  {
    path: '*',
    component: ComponentCreator('*'),
  },
];
