export default {
  title: 'acodeaday',
  description: 'Daily coding practice with spaced repetition',
  themeConfig: {
    nav: [
      { text: 'Guide', link: '/guide/introduction' },
      { text: 'API Reference', link: '/api/overview' },
      { text: 'Contributing', link: '/guide/contributing' },
      { text: 'About', link: '/about' },
    ],
    sidebar: {
      '/guide/': [
        {
          text: 'Getting Started',
          items: [
            { text: 'Introduction', link: '/guide/introduction' },
            { text: 'Quick Start', link: '/guide/quick-start' },
          ]
        },
        {
          text: 'Local Development',
          items: [
            { text: 'Prerequisites', link: '/guide/prerequisites' },
            { text: 'Backend Setup', link: '/guide/backend-setup' },
            { text: 'Frontend Setup', link: '/guide/frontend-setup' },
            { text: 'Judge0 Setup', link: '/guide/judge0-setup' },
            { text: 'Database Setup', link: '/guide/database-setup' },
          ]
        },
        {
          text: 'Deployment',
          items: [
            { text: 'Overview', link: '/guide/deployment-overview' },
            { text: 'Deploy Backend', link: '/guide/deploy-backend' },
            { text: 'Deploy Frontend', link: '/guide/deploy-frontend' },
            { text: 'Environment Variables', link: '/guide/environment-variables' },
          ]
        },
        {
          text: 'Configuration',
          items: [
            { text: 'Adding Problems', link: '/guide/adding-problems' },
            { text: 'Adding Languages', link: '/guide/adding-languages' },
            { text: 'Spaced Repetition', link: '/guide/spaced-repetition' },
          ]
        },
        {
          text: 'Community',
          items: [
            { text: 'Contributing', link: '/guide/contributing' },
          ]
        }
      ],
      '/api/': [
        {
          text: 'API Reference',
          items: [
            { text: 'Overview', link: '/api/overview' },
            { text: 'Authentication', link: '/api/authentication' },
            { text: 'Problems', link: '/api/problems' },
            { text: 'Submissions', link: '/api/submissions' },
            { text: 'Progress', link: '/api/progress' },
          ]
        }
      ]
    },
    socialLinks: [
      { icon: 'github', link: 'https://github.com/engineeringwithtemi/acodeaday' }
    ],
    search: {
      provider: 'local'
    }
  }
}
