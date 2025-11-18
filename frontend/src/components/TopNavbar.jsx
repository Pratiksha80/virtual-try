// src/components/TopNavbar.jsx
import React from 'react';
import { Navbar, Container, Nav, Button, Image } from 'react-bootstrap';
import { useNavigate } from 'react-router-dom';
import './TopNavbar.css';

const TopNavbar = ({ user, onLogout }) => {
  const navigate = useNavigate();
  const [theme, setTheme] = React.useState(() => localStorage.getItem('theme') || 'light');

  React.useEffect(() => {
    document.documentElement.setAttribute('data-theme', theme);
    localStorage.setItem('theme', theme);
  }, [theme]);

  const toggleTheme = () => {
    setTheme((prev) => (prev === 'light' ? 'dark' : 'light'));
  };

  return (
    <Navbar expand="lg" sticky="top" className="shadow-sm px-3">
      <Container fluid>
        <Navbar.Brand onClick={() => navigate('/')} style={{ cursor: 'pointer' }}>
          👕 AI Virtual Try-On
        </Navbar.Brand>
        <Nav className="ms-auto d-flex align-items-center gap-3">
          <Button variant="light" onClick={toggleTheme} className="d-flex align-items-center">
            {theme === 'light' ? '🌙' : '☀️'}
          </Button>
          <div className="d-flex align-items-center gap-2 text-white">
            {user?.photo ? (
              <Image
                src={user.photo}
                roundedCircle
                width={35}
                height={35}
                alt="User"
                style={{ objectFit: 'cover' }}
              />
            ) : (
              <div className="avatar-circle">
                {(user?.name?.[0] || 'U').toUpperCase()}
              </div>
            )}
            <div className="text-nowrap">
              <div className="fw-semibold small">{user?.name || 'User'}</div>
            </div>
          </div>
          <Button variant="outline-light" onClick={onLogout}>Logout</Button>
        </Nav>
      </Container>
    </Navbar>
  );
};

export default TopNavbar;
