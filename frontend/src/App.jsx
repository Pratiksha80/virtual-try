
import React from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import Signup from './pages/Signup';
import Login from './pages/Login';
import Dashboard from './pages/Dashboard';
import DashboardLayout from './components/DashboardLayout';
import Profile from './pages/Profile';
import EditProfile from './pages/EditProfile';
import LinkBasedTryOn from './pages/LinkBasedTryOn';
import TryOnQR from './pages/TryOnQR';
import CameraTryOn from './pages/CameraTryOn';
import Home from './pages/Home';
import TopNavbar from './components/TopNavbar';
import './App.css';

const ProtectedRoute = ({ children }) => {
  const token = localStorage.getItem('token');
  if (!token) {
    // Save the attempted URL
    localStorage.setItem('redirectUrl', window.location.pathname);
    return <Navigate to="/login" />;
  }
  return children;
};

const PublicRoute = ({ children }) => {
  const token = localStorage.getItem('token');
  if (token) {
    return <Navigate to="/dashboard" />;
  }
  return children;
};

function App() {
  const [user, setUser] = React.useState(null);

  React.useEffect(() => {
    const token = localStorage.getItem('token');
    if (token) {
      try {
        const decoded = JSON.parse(atob(token.split('.')[1]));
        const name = localStorage.getItem('name') || 'User';
        const photo = localStorage.getItem('photo');
        setUser({ name, email: decoded.email, photo });
      } catch (error) {
        console.error('Error decoding token:', error);
        localStorage.removeItem('token');
        setUser(null);
      }
    }
  }, []);

  const handleLogout = () => {
    localStorage.removeItem('token');
    localStorage.removeItem('name');
    localStorage.removeItem('photo');
    setUser(null);
    window.location.href = '/login';
  };

  return (
    <Router>
      {user && <TopNavbar user={user} onLogout={handleLogout} />}
      <Routes>
        <Route path="/" element={
          <PublicRoute>
            <Home />
          </PublicRoute>
        } />
        <Route path="/login" element={
          <PublicRoute>
            <Login />
          </PublicRoute>
        } />
        <Route path="/signup" element={
          <PublicRoute>
            <Signup />
          </PublicRoute>
        } />
        <Route path="/dashboard/*" element={
          <ProtectedRoute>
            <DashboardLayout>
              <Routes>
                <Route path="" element={<Dashboard />} />
                <Route path="profile" element={<Profile />} />
                <Route path="edit-profile" element={<EditProfile />} />
                <Route path="link-based-tryon" element={<LinkBasedTryOn />} />
                <Route path="tryon-qr" element={<TryOnQR />} />
                <Route path="camera-tryon" element={<CameraTryOn />} />
                <Route path="*" element={<Navigate to="/dashboard" />} />
              </Routes>
            </DashboardLayout>
          </ProtectedRoute>
        } />
        <Route path="*" element={<Navigate to="/" />} />
      </Routes>
    </Router>
  );
}

export default App;
