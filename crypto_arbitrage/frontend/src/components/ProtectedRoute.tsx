import { Navigate, useLocation } from 'react-router-dom'
import { useEffect } from 'react'

interface ProtectedRouteProps {
  children: React.ReactNode
}

const ProtectedRoute: React.FC<ProtectedRouteProps> = ({ children }) => {
  const location = useLocation()

  useEffect(() => {
    // 检查是否已登录
    const token = localStorage.getItem('access_token')
    if (!token) {
      // 未登录，重定向到登录页
      return
    }
  }, [location])

  const token = localStorage.getItem('access_token')

  if (!token) {
    return <Navigate to="/login" state={{ from: location }} replace />
  }

  return <>{children}</>
}

export default ProtectedRoute
