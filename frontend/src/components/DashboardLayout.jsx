import React from 'react';
import { Container, Row, Col, Nav } from 'react-bootstrap';
import { useNavigate } from 'react-router-dom';
import './DashboardLayout.css';

const DashboardLayout = ({ children }) => {
  const navigate = useNavigate();

  return (
    <div className="dashboard-wrapper">
      {/* Sidebar only, NO Navbar here */}
      <Container fluid className="dashboard-body">
        <Row>
          {/* Sidebar */}
          <Col md={3} className="dashboard-sidebar p-0">
            <Nav defaultActiveKey="/dashboard" className="flex-column p-3">
              <Nav.Link onClick={() => navigate('/dashboard')}>🏠 Dashboard</Nav.Link>
              <Nav.Link onClick={() => navigate('/dashboard/profile')}>🙍‍♂️ Profile</Nav.Link>
              <Nav.Link onClick={() => navigate('/dashboard/tryon-link')}>🔗 Link-Based Try-On</Nav.Link>
              <Nav.Link onClick={() => navigate('/dashboard/tryon-qr')}>📷 QR/RFID Try-On</Nav.Link>
            </Nav>
          </Col>

          {/* Main Content */}
          <Col md={9} className="dashboard-main p-4">
            {children}
          </Col>
        </Row>
      </Container>
    </div>
  );
};

export default DashboardLayout;
