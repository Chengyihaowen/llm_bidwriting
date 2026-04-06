import { createRouter, createWebHistory } from 'vue-router'
import ProjectList from '../views/ProjectList.vue'

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes: [
    { path: '/', name: 'home', component: ProjectList },
    {
      path: '/projects/:id',
      name: 'workspace',
      component: () => import('../views/WorkspacePage.vue'),
    },
  ],
})

export default router
