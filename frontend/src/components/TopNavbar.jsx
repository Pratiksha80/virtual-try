// src/components/TopNavbar.jsx
import React from 'react';
import { Navbar, Container, Nav, Button, Image } from 'react-bootstrap';
import { useNavigate } from 'react-router-dom';
import './TopNavbar.css';

const TopNavbar = ({ user, onLogout }) => {
  const navigate = useNavigate();

  return (
    <Navbar bg="primary" variant="dark" expand="lg" sticky="top" className="shadow-sm px-3">
      <Container fluid>
        <Navbar.Brand onClick={() => navigate('/')} style={{ cursor: 'pointer' }}>
          👕 AI Virtual Try-On
        </Navbar.Brand>
        <Nav className="ms-auto d-flex align-items-center gap-3">
          <div className="d-flex align-items-center gap-2 text-white">
            {user?.imageUrl ? (
              <Image
                src={user.imageUrl}
                roundedCircle
                width={35}
                height={35}
                alt="User"
                style={{ objectFit: 'cover' }}
              />
            ) : (
              <div className="avatar-circle">
                {user?.username?.[0]?.toUpperCase() || 'U'}
              </div>
            )}
            <div className="text-nowrap">
              <div className="fw-semibold small">{user?.username || 'User'}</div>
            </div>
          </div>
          <Button variant="outline-light" onClick={onLogout}>Logout</Button>
        </Nav>
      </Container>
    </Navbar>
  );
};

export default TopNavbar;
