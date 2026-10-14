import { BrowserRouter, Route, Routes } from 'react-router'
import { AuthProvider } from './auth/AuthContext'
import { GuestOnly, RequireAuth } from './auth/RouteGuards'
import { Layout } from './components/Layout'
import { DashboardPage } from './pages/DashboardPage'
import { HomePage } from './pages/HomePage'
import { LoginPage } from './pages/LoginPage'
import { NotFoundPage } from './pages/NotFoundPage'
import { RegisterPage } from './pages/RegisterPage'
import { StatusPage } from './pages/StatusPage'
import { SearchPage } from './pages/SearchPage'
import { TutorProfilePage } from './pages/TutorProfilePage'
import { ApplyPage } from './pages/tutor/ApplyPage'
import { ProfileEditorPage } from './pages/tutor/ProfileEditorPage'

export default function App() {
  return (
    <AuthProvider>
      <BrowserRouter>
        <Routes>
          <Route element={<Layout />}>
            <Route path="/" element={<HomePage />} />
            <Route path="/status" element={<StatusPage />} />
            <Route path="/tutors" element={<SearchPage />} />
            <Route path="/tutors/:id" element={<TutorProfilePage />} />

            <Route element={<GuestOnly />}>
              <Route path="/login" element={<LoginPage />} />
              <Route path="/register" element={<RegisterPage />} />
            </Route>

            <Route element={<RequireAuth />}>
              <Route path="/dashboard" element={<DashboardPage />} />
              <Route path="/tutor/apply" element={<ApplyPage />} />
              <Route path="/tutor/profile" element={<ProfileEditorPage />} />
            </Route>

            <Route path="*" element={<NotFoundPage />} />
          </Route>
        </Routes>
      </BrowserRouter>
    </AuthProvider>
  )
}
