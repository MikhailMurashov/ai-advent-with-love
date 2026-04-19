import { BrowserRouter, Routes, Route } from 'react-router-dom'
import { AppLayout } from '@/components/layout/AppLayout'
import { HomePage } from '@/pages/HomePage'
import { ChatPage } from '@/components/chat/ChatPage'
import { useInitUser } from '@/hooks/useInitUser'
import { NotificationContainer } from '@/components/ui/NotificationContainer'

function AppRoutes() {
  useInitUser()

  return (
    <Routes>
      <Route element={<AppLayout />}>
        <Route index element={<HomePage />} />
        <Route path="/chat/:sessionId" element={<ChatPage />} />
      </Route>
    </Routes>
  )
}

export function App() {
  return (
    <BrowserRouter>
      <AppRoutes />
      <NotificationContainer />
    </BrowserRouter>
  )
}
