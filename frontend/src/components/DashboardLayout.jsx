import React from 'react';
import { Container, Nav } from 'react-bootstrap';
import { useNavigate, useLocation } from 'react-router-dom';
import './DashboardLayout.css';

const DashboardLayout = ({ children }) => {
  const navigate = useNavigate();
  const location = useLocation();

  const isActive = (path) => {
    return location.pathname === path ? 'active' : '';
  };

  return (
    <div className="dashboard-wrapper">
      <Container fluid className="dashboard-body p-0">
        {/* Sidebar */}
        <div className="dashboard-sidebar">
          <div className="text-center mb-4">
            <h3 className="text-white mb-0 fw-bold">Virtual Try-On</h3>
            <small className="text-gray-400">AI-Powered Fashion</small>
          </div>
          <Nav className="flex-column">
            <Nav.Link 
              onClick={() => navigate('/dashboard')}
              className={isActive('/dashboard')}
            >
              <span className="nav-icon">⚡</span>
              Dashboard
            </Nav.Link>
            <Nav.Link 
              onClick={() => navigate('/dashboard/link-based-tryon')}
              className={isActive('/dashboard/link-based-tryon')}
            >
              <span className="nav-icon">�</span>
              Try-On with Link
            </Nav.Link>
            <Nav.Link 
              onClick={() => navigate('/dashboard/tryon-qr')}
              className={isActive('/dashboard/tryon-qr')}
            >
              <span className="nav-icon">📱</span>
              Smart Tag Try-On
            </Nav.Link>
            <Nav.Link 
              onClick={() => navigate('/dashboard/camera-tryon')}
              className={isActive('/dashboard/camera-tryon')}
            >
              <span className="nav-icon">📷</span>
              Camera Try-On
            </Nav.Link>
            <Nav.Link 
              onClick={() => navigate('/dashboard/profile')}
              className={isActive('/dashboard/profile')}
            >
              <span className="nav-icon">�</span>
              Profile
            </Nav.Link>
          </Nav>
        </div>

        {/* Main Content */}
        <main className="dashboard-main">
          {children}
        </main>
      </Container>
    </div>
  );
};

export default DashboardLayout;
