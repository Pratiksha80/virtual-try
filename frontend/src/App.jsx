import React, { useEffect, useState } from 'react';
import { BrowserRouter as Router, Routes, Route, Link, Navigate, useNavigate } from 'react-router-dom';
import { Container, Navbar, Nav, Row, Col, Button, Card } from 'react-bootstrap';
import Signup from './pages/Signup';
import Login from './pages/Login';
import Dashboard from './pages/Dashboard';
import DashboardLayout from './components/DashboardLayout';
import './App.css';
import Profile from './pages/Profile'; // Add this
import EditProfile from './pages/EditProfile';
import LinkBasedTryOn from './pages/LinkBasedTryOn';





// Separate Home Component
function Home() {
  return (
    <div className="text-center">
      <div className="hero-section py-5">
        <h1 className="display-5 fw-bold">👗 AI & IoT Virtual Try-On</h1>
        <p className="lead mt-3">
          Experience fashion like never before! Our AI-powered try-on system lets you preview outfits in real-time — using smart tags, deep learning, and your webcam.
        </p>
        <div className="d-flex justify-content-center gap-3 mt-4">
          <Link to="/login"><Button variant="primary" size="lg">Login</Button></Link>
          <Link to="/signup"><Button variant="outline-primary" size="lg">Sign Up</Button></Link>
        </div>
      </div>

      <Container className="my-5">
        <Row className="g-4">
          <Col md={4}>
            <Card className="feature-card h-100">
              <Card.Body>
                <Card.Title>🔐 Secure Authentication</Card.Title>
                <Card.Text>
                  Your data is safe with our encrypted login system using FastAPI and MongoDB.
                </Card.Text>
              </Card.Body>
            </Card>
          </Col>
          <Col md={4}>
            <Card className="feature-card h-100">
              <Card.Body>
                <Card.Title>🧠 AI-Powered Try-On</Card.Title>
                <Card.Text>
                  Real-time overlay of clothes on your photo with MediaPipe + Deep Learning integration.
                </Card.Text>
              </Card.Body>
            </Card>
          </Col>
          <Col md={4}>
            <Card className="feature-card h-100">
              <Card.Body>
                <Card.Title>📲 Smart Tag Scanning</Card.Title>
                <Card.Text>
                  Scan RFID/QR smart tags to fetch and preview fashion products instantly.
                </Card.Text>
              </Card.Body>
            </Card>
          </Col>
        </Row>
      </Container>
    </div>
  );
}

function AppWrapper() {
  const [isAuthenticated, setIsAuthenticated] = useState(!!localStorage.getItem('token'));
  const navigate = useNavigate();

  useEffect(() => {
    const checkAuth = () => {
      const token = localStorage.getItem('token');
      setIsAuthenticated(!!token);
    };

    checkAuth();
    window.addEventListener('storage', checkAuth);

    const originalSetItem = localStorage.setItem;
    localStorage.setItem = function (key, value) {
      originalSetItem.apply(this, arguments);
      window.dispatchEvent(new Event('storage'));
    };

    return () => {
      window.removeEventListener('storage', checkAuth);
      localStorage.setItem = originalSetItem;
    };
  }, []);

  const handleLogout = () => {
    localStorage.removeItem('token');
    setIsAuthenticated(false);
    navigate('/');
  };

  return (
    <>
      <Navbar bg="primary" variant="dark" expand="lg" sticky="top" className="shadow-sm">
        <Container>
          <Navbar.Brand as={Link} to="/">👕 AI Virtual Try-On</Navbar.Brand>
          <Navbar.Toggle aria-controls="basic-navbar-nav" />
          <Navbar.Collapse>
            <Nav className="ms-auto">
              {!isAuthenticated ? (
                <>
                  <Nav.Link as={Link} to="/signup">Sign Up</Nav.Link>
                  <Nav.Link as={Link} to="/login">Login</Nav.Link>
                </>
              ) : (
                <Nav.Link onClick={handleLogout}>Logout</Nav.Link>
              )}
            </Nav>
          </Navbar.Collapse>
        </Container>
      </Navbar>

      <Routes>
        {/* Dashboard Route without container */}
        <Route
          path="/dashboard"
          element={
            isAuthenticated ? (
              <DashboardLayout>
                <Dashboard />
              </DashboardLayout>
            ) : (
              <Navigate to="/login" />
            )
          }
        />

        {/* Public pages wrapped in container + glass-card */}
        <Route
          path="*"
          element={
            <Container className="mt-5">
              <Row>
                <Col md={{ span: 10, offset: 1 }} className="glass-card p-4">
                  <Routes>
                    <Route path="/" element={<Home />} />
                    <Route path="/signup" element={isAuthenticated ? <Navigate to="/dashboard" /> : <Signup />} />
                    <Route path="/login" element={isAuthenticated ? <Navigate to="/dashboard" /> : <Login />} />
                  </Routes>
                </Col>
              </Row>
            </Container>
          }
        />
        <Route
  path="/dashboard/profile"
  element={
    isAuthenticated ? (
      <DashboardLayout>
        <Profile />
      </DashboardLayout>
    ) : (
      <Navigate to="/login" />
    )
  }
/>
<Route
  path="/dashboard/profile/edit"
  element={
    isAuthenticated ? (
      <DashboardLayout>
        <EditProfile />
      </DashboardLayout>
    ) : (
      <Navigate to="/login" />
    )
  }
/>
<Route
  path="/dashboard/tryon-link"
  element={
    isAuthenticated ? (
      <DashboardLayout>
        <LinkBasedTryOn />
      </DashboardLayout>
    ) : (
      <Navigate to="/login" />
    )
  }
/>

 

      </Routes>
    </>
  );
}

function App() {
  return (
    <Router>
      <AppWrapper />
    </Router>
  );
}

export default App;
