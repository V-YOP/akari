import { createRouter, createWebHistory } from 'vue-router'
import TaskListView from '../views/TaskListView.vue'
import TaskFormView from '../views/TaskFormView.vue'
import LogsView from '../views/LogsView.vue'

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes: [
    {
      path: '/',
      name: 'tasks',
      component: TaskListView,
      meta: { title: 'Tasks' }
    },
    {
      path: '/tasks/new',
      name: 'task-new',
      component: TaskFormView,
      meta: { title: 'New Task' }
    },
    {
      path: '/tasks/:id/edit',
      name: 'task-edit',
      component: TaskFormView,
      meta: { title: 'Edit Task' }
    },
    {
      path: '/logs/:id',
      name: 'logs',
      component: LogsView,
      meta: { title: 'Logs' }
    },
    {
      path: '/:pathMatch(.*)*',
      redirect: '/'
    }
  ]
})

// Update document title based on route
router.afterEach((to) => {
  const title = to.meta.title as string
  if (title) {
    document.title = `${title} - Akari Task Scheduler`
  }
})

export default router