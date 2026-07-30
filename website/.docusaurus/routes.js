import React from 'react';
import ComponentCreator from '@docusaurus/ComponentCreator';

export default [
  {
    path: '/mgagent/blog',
    component: ComponentCreator('/mgagent/blog', '41f'),
    exact: true
  },
  {
    path: '/mgagent/blog/2026-04-release',
    component: ComponentCreator('/mgagent/blog/2026-04-release', 'b66'),
    exact: true
  },
  {
    path: '/mgagent/blog/2026-05-release',
    component: ComponentCreator('/mgagent/blog/2026-05-release', '63a'),
    exact: true
  },
  {
    path: '/mgagent/blog/2026-06-release',
    component: ComponentCreator('/mgagent/blog/2026-06-release', '0e0'),
    exact: true
  },
  {
    path: '/mgagent/blog/2026-07-release',
    component: ComponentCreator('/mgagent/blog/2026-07-release', '7ad'),
    exact: true
  },
  {
    path: '/mgagent/blog/archive',
    component: ComponentCreator('/mgagent/blog/archive', 'd94'),
    exact: true
  },
  {
    path: '/mgagent/blog/authors',
    component: ComponentCreator('/mgagent/blog/authors', '864'),
    exact: true
  },
  {
    path: '/mgagent/blog/tags',
    component: ComponentCreator('/mgagent/blog/tags', '0be'),
    exact: true
  },
  {
    path: '/mgagent/blog/tags/动态配置',
    component: ComponentCreator('/mgagent/blog/tags/动态配置', '03e'),
    exact: true
  },
  {
    path: '/mgagent/blog/tags/工具集成',
    component: ComponentCreator('/mgagent/blog/tags/工具集成', '5ad'),
    exact: true
  },
  {
    path: '/mgagent/blog/tags/基础功能',
    component: ComponentCreator('/mgagent/blog/tags/基础功能', '0ad'),
    exact: true
  },
  {
    path: '/mgagent/blog/tags/架构升级',
    component: ComponentCreator('/mgagent/blog/tags/架构升级', '280'),
    exact: true
  },
  {
    path: '/mgagent/blog/tags/文档',
    component: ComponentCreator('/mgagent/blog/tags/文档', '3ac'),
    exact: true
  },
  {
    path: '/mgagent/blog/tags/项目启动',
    component: ComponentCreator('/mgagent/blog/tags/项目启动', '81f'),
    exact: true
  },
  {
    path: '/mgagent/blog/tags/新功能',
    component: ComponentCreator('/mgagent/blog/tags/新功能', 'd15'),
    exact: true
  },
  {
    path: '/mgagent/blog/tags/性能优化',
    component: ComponentCreator('/mgagent/blog/tags/性能优化', 'fa9'),
    exact: true
  },
  {
    path: '/mgagent/blog/tags/rag',
    component: ComponentCreator('/mgagent/blog/tags/rag', '8fb'),
    exact: true
  },
  {
    path: '/mgagent/docs',
    component: ComponentCreator('/mgagent/docs', '64c'),
    routes: [
      {
        path: '/mgagent/docs',
        component: ComponentCreator('/mgagent/docs', '95c'),
        routes: [
          {
            path: '/mgagent/docs',
            component: ComponentCreator('/mgagent/docs', '174'),
            routes: [
              {
                path: '/mgagent/docs/architecture/database',
                component: ComponentCreator('/mgagent/docs/architecture/database', 'bff'),
                exact: true,
                sidebar: "tutorialSidebar"
              },
              {
                path: '/mgagent/docs/architecture/dual-stack',
                component: ComponentCreator('/mgagent/docs/architecture/dual-stack', '316'),
                exact: true,
                sidebar: "tutorialSidebar"
              },
              {
                path: '/mgagent/docs/architecture/model-config',
                component: ComponentCreator('/mgagent/docs/architecture/model-config', '0f6'),
                exact: true,
                sidebar: "tutorialSidebar"
              },
              {
                path: '/mgagent/docs/architecture/overview',
                component: ComponentCreator('/mgagent/docs/architecture/overview', '7d4'),
                exact: true,
                sidebar: "tutorialSidebar"
              },
              {
                path: '/mgagent/docs/configuration/docker',
                component: ComponentCreator('/mgagent/docs/configuration/docker', '7a0'),
                exact: true,
                sidebar: "tutorialSidebar"
              },
              {
                path: '/mgagent/docs/configuration/environment-variables',
                component: ComponentCreator('/mgagent/docs/configuration/environment-variables', '8dd'),
                exact: true,
                sidebar: "tutorialSidebar"
              },
              {
                path: '/mgagent/docs/configuration/nginx',
                component: ComponentCreator('/mgagent/docs/configuration/nginx', '2ac'),
                exact: true,
                sidebar: "tutorialSidebar"
              },
              {
                path: '/mgagent/docs/deployment/docker-deployment',
                component: ComponentCreator('/mgagent/docs/deployment/docker-deployment', '119'),
                exact: true,
                sidebar: "tutorialSidebar"
              },
              {
                path: '/mgagent/docs/deployment/local-development',
                component: ComponentCreator('/mgagent/docs/deployment/local-development', '935'),
                exact: true,
                sidebar: "tutorialSidebar"
              },
              {
                path: '/mgagent/docs/deployment/mysql-deployment',
                component: ComponentCreator('/mgagent/docs/deployment/mysql-deployment', '2ff'),
                exact: true,
                sidebar: "tutorialSidebar"
              },
              {
                path: '/mgagent/docs/deployment/production-deployment',
                component: ComponentCreator('/mgagent/docs/deployment/production-deployment', '28c'),
                exact: true,
                sidebar: "tutorialSidebar"
              },
              {
                path: '/mgagent/docs/development/api-reference',
                component: ComponentCreator('/mgagent/docs/development/api-reference', '31d'),
                exact: true,
                sidebar: "tutorialSidebar"
              },
              {
                path: '/mgagent/docs/development/project-structure',
                component: ComponentCreator('/mgagent/docs/development/project-structure', '6ee'),
                exact: true,
                sidebar: "tutorialSidebar"
              },
              {
                path: '/mgagent/docs/development/scripts',
                component: ComponentCreator('/mgagent/docs/development/scripts', 'e23'),
                exact: true,
                sidebar: "tutorialSidebar"
              },
              {
                path: '/mgagent/docs/getting-started/configuration',
                component: ComponentCreator('/mgagent/docs/getting-started/configuration', '813'),
                exact: true,
                sidebar: "tutorialSidebar"
              },
              {
                path: '/mgagent/docs/getting-started/installation',
                component: ComponentCreator('/mgagent/docs/getting-started/installation', '143'),
                exact: true,
                sidebar: "tutorialSidebar"
              },
              {
                path: '/mgagent/docs/getting-started/quick-start',
                component: ComponentCreator('/mgagent/docs/getting-started/quick-start', '7bc'),
                exact: true,
                sidebar: "tutorialSidebar"
              },
              {
                path: '/mgagent/docs/intro',
                component: ComponentCreator('/mgagent/docs/intro', 'e4b'),
                exact: true,
                sidebar: "tutorialSidebar"
              },
              {
                path: '/mgagent/docs/troubleshooting/common-issues',
                component: ComponentCreator('/mgagent/docs/troubleshooting/common-issues', '6c0'),
                exact: true,
                sidebar: "tutorialSidebar"
              },
              {
                path: '/mgagent/docs/troubleshooting/faq',
                component: ComponentCreator('/mgagent/docs/troubleshooting/faq', 'cb6'),
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
    path: '/mgagent/',
    component: ComponentCreator('/mgagent/', 'c8b'),
    exact: true
  },
  {
    path: '*',
    component: ComponentCreator('*'),
  },
];
