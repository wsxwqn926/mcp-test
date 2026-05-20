import { defineStore } from 'pinia'
import { ref, computed } from 'vue'

export interface Notification {
  id: string
  type: 'info' | 'warning' | 'error' | 'success'
  title: string
  message?: string
  timestamp: string
  data?: any
}

export const useNotificationStore = defineStore('notification', () => {
  const notifications = ref<Notification[]>([])
  const maxNotifications = 100

  const unreadCount = computed(() => notifications.value.filter(n => !n.read).length)
  const recentNotifications = computed(() => notifications.value.slice(0, 20))

  function add(notification: Omit<Notification, 'id' | 'timestamp'>) {
    const n: Notification = {
      ...notification,
      id: `notif-${Date.now()}-${Math.random().toString(36).slice(2, 6)}`,
      timestamp: new Date().toISOString(),
    }
    notifications.value.unshift(n)
    if (notifications.value.length > maxNotifications) {
      notifications.value = notifications.value.slice(0, maxNotifications)
    }
    return n
  }

  function addFromWs(data: any) {
    const method = data.method || data.data?.method || 'unknown'
    let type: Notification['type'] = 'info'
    let title = method
    if (method.includes('error') || method.includes('Error')) type = 'error'
    else if (method.includes('warning') || method.includes('Warning')) type = 'warning'
    else if (method.includes('changed') || method.includes('updated')) type = 'info'
    
    add({ type, title, message: JSON.stringify(data, null, 2), data })
  }

  function clear() {
    notifications.value = []
  }

  function remove(id: string) {
    notifications.value = notifications.value.filter(n => n.id !== id)
  }

  return { notifications, unreadCount, recentNotifications, add, addFromWs, clear, remove }
})
