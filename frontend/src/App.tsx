import { BrowserRouter, Route, Routes } from 'react-router'
import { AuthProvider } from './auth/AuthContext'
import { GuestOnly, RequireAuth, RequireStaff } from './auth/RouteGuards'
import { Layout } from './components/Layout'
import { AccountPage } from './pages/AccountPage'
import { DashboardPage } from './pages/DashboardPage'
import { MyTutorsPage } from './pages/MyTutorsPage'
import { HomePage } from './pages/HomePage'
import { LoginPage } from './pages/LoginPage'
import { NotFoundPage } from './pages/NotFoundPage'
import { RegisterPage } from './pages/RegisterPage'
import { StatusPage } from './pages/StatusPage'
import { ForgotPasswordPage } from './pages/ForgotPasswordPage'
import { ReportPage } from './pages/ReportPage'
import { ResetPasswordPage } from './pages/ResetPasswordPage'
import { VerifyEmailPage } from './pages/VerifyEmailPage'
import { SearchPage } from './pages/SearchPage'
import { TutorProfilePage } from './pages/TutorProfilePage'
import { ApplyPage } from './pages/tutor/ApplyPage'
import { ProfileEditorPage } from './pages/tutor/ProfileEditorPage'
import { ApplicationReviewPage } from './pages/staff/ApplicationReviewPage'
import { ApplicationsPage } from './pages/staff/ApplicationsPage'
import { StaffHomePage } from './pages/staff/StaffHomePage'
import { PhotosPage } from './pages/staff/PhotosPage'
import { ReportReviewPage } from './pages/staff/ReportReviewPage'
import { ReportsPage } from './pages/staff/ReportsPage'
import { MorePage } from './pages/staff/MorePage'
import { UserPage } from './pages/staff/UserPage'
import { UsersPage } from './pages/staff/UsersPage'
import { VideosPage } from './pages/staff/VideosPage'

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
            <Route path="/verify-email" element={<VerifyEmailPage />} />
            <Route path="/forgot-password" element={<ForgotPasswordPage />} />
            <Route path="/reset-password" element={<ResetPasswordPage />} />

            <Route element={<GuestOnly />}>
              <Route path="/login" element={<LoginPage />} />
              <Route path="/register" element={<RegisterPage />} />
            </Route>

            <Route element={<RequireAuth />}>
              <Route path="/dashboard" element={<DashboardPage />} />
              <Route path="/my-tutors" element={<MyTutorsPage />} />
              <Route path="/account" element={<AccountPage />} />
              <Route path="/tutor/apply" element={<ApplyPage />} />
              <Route path="/tutor/profile" element={<ProfileEditorPage />} />
              <Route path="/tutors/:id/report" element={<ReportPage />} />
            </Route>

            {/* The Brights team's area: replaces the Django admin for day-to-day work. */}
            <Route element={<RequireStaff />}>
              <Route path="/staff" element={<StaffHomePage />} />
              <Route path="/staff/applications" element={<ApplicationsPage />} />
              <Route path="/staff/applications/:id" element={<ApplicationReviewPage />} />
              <Route path="/staff/photos" element={<PhotosPage />} />
              <Route path="/staff/reports" element={<ReportsPage />} />
              <Route path="/staff/reports/:id" element={<ReportReviewPage />} />
              <Route path="/staff/more" element={<MorePage />} />
              <Route path="/staff/users" element={<UsersPage />} />
              <Route path="/staff/users/:id" element={<UserPage />} />
              <Route path="/staff/videos" element={<VideosPage />} />
            </Route>

            <Route path="*" element={<NotFoundPage />} />
          </Route>
        </Routes>
      </BrowserRouter>
    </AuthProvider>
  )
}
