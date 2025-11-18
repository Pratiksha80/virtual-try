// src/pages/Dashboard.jsx
import React, { useEffect, useState } from "react";
import { Card, Row, Col, Button, Badge } from "react-bootstrap";
import { FaCamera, FaLink, FaMicrochip } from "react-icons/fa";
import { Link } from "react-router-dom";

const Dashboard = () => {
  const [user, setUser] = useState({
    name: "User",
    email: "user@example.com",
  });
  const [profileImage, setProfileImage] = useState(null);

  useEffect(() => {
    const token = localStorage.getItem("token");
    if (token) {
      try {
        const payload = JSON.parse(atob(token.split(".")[1]));
        const email = payload.email || "user@example.com";
        const name = localStorage.getItem("name") || "User";
        const photo = localStorage.getItem("photo");

        setUser({ name, email });
        setProfileImage(photo);
      } catch (error) {
        console.error("Error decoding token or loading user data", error);
      }
    }
  }, []);

  return (
    <div className="py-4 px-3">
      {/* Hero Header */}
      <div className="mb-5 p-4 rounded-4 position-relative" style={{
        background: 'var(--gradient-1)',
        border: '1px solid var(--border-color)'
      }}>
        <div className="d-flex flex-wrap align-items-center justify-content-between gap-3">
          <div>
            <h2 className="fw-bold mb-1" style={{ color: '#4C1D95', fontFamily: 'Playfair Display, serif' }}>Welcome, {user.name}</h2>
            <div className="text-muted">Manage try-ons, tags and your profile at a glance</div>
          </div>
          <div className="d-flex align-items-center gap-2">
            <span className="text-muted small">Signed in as</span>
            <span className="fw-semibold">{user.email}</span>
          </div>
        </div>
      </div>

      {/* Profile and Recent Activity */}
      <Row className="mb-5 g-4">
        <Col lg={4}>
          <Card className="border-0 shadow-sm h-100" style={{ background: 'var(--surface-color)', border: '1px solid var(--border-color)' }}>
            <Card.Body className="p-4">
              <div className="text-center mb-4">
                {profileImage ? (
                  <img
                    src={profileImage}
                    alt="Profile"
                    className="rounded-circle shadow-sm mb-3"
                    style={{ width: 100, height: 100, objectFit: "cover" }}
                  />
                ) : (
                  <div
                    className="rounded-circle d-flex justify-content-center align-items-center mx-auto mb-3"
                    style={{ width: 100, height: 100, fontSize: 36 }}
                  >
                    {user.name.charAt(0).toUpperCase()}
                  </div>
                )}
                <h5 className="mb-1">{user.name}</h5>
                <p className="text-muted mb-3">{user.email}</p>
                <Link to="/profile">
                  <Button variant="outline-primary" size="sm">
                    View Profile
                  </Button>
                </Link>
              </div>
            </Card.Body>
          </Card>
        </Col>

        <Col lg={8}>
          <Card className="border-0 shadow-sm h-100" style={{ background: 'var(--surface-color)', border: '1px solid var(--border-color)' }}>
            <Card.Body className="p-4">
              <div className="d-flex justify-content-between align-items-center mb-4">
                <h5 className="mb-0" style={{ color: 'var(--primary-color)' }}>📈 Recent Activity</h5>
                <Badge bg="primary" pill>Today</Badge>
              </div>
              <div className="d-flex flex-column gap-3">
                <div className="d-flex align-items-center p-3 rounded" style={{ backgroundColor: 'rgba(37, 99, 235, 0.08)', border: '1px solid var(--border-color)' }}>
                  <FaMicrochip style={{ color: 'var(--primary-color)' }} size={24} />
                  <div className="ms-3">
                    <p className="mb-1 fw-semibold">Scanned RFID Tag</p>
                    <small className="text-muted">T-Shirt Pro Max • Just now</small>
                  </div>
                </div>
                <div className="d-flex align-items-center p-3 rounded" style={{ backgroundColor: 'rgba(37, 99, 235, 0.08)', border: '1px solid var(--border-color)' }}>
                  <FaLink style={{ color: 'var(--primary-color)' }} size={24} />
                  <div className="ms-3">
                    <p className="mb-1 fw-semibold">Used Link-Based Try-On</p>
                    <small className="text-muted">3:45 PM • Today</small>
                  </div>
                </div>
                <div className="d-flex align-items-center p-3 rounded" style={{ backgroundColor: 'rgba(37, 99, 235, 0.08)', border: '1px solid var(--border-color)' }}>
                  <FaCamera style={{ color: 'var(--primary-color)' }} size={24} />
                  <div className="ms-3">
                    <p className="mb-1 fw-semibold">Updated Profile Photo</p>
                    <small className="text-muted">2:30 PM • Today</small>
                  </div>
                </div>
              </div>
            </Card.Body>
          </Card>
        </Col>
      </Row>

      {/* Quick Actions */}
      <div className="mb-4">
        <h4 className="fw-bold mb-4" style={{ color: 'var(--accent-2)' }}>⚡ Quick Actions</h4>
        <Row className="g-4">
          <Col md={4}>
            <Card className="border-0 shadow-sm hover-card h-100" style={{ background: '#111111', border: '1px solid rgba(212,175,55,0.25)' }}>
              <Card.Body className="p-4 text-center">
                <div className="mb-4">
                  <div className="d-inline-flex p-3 rounded-circle mb-3" style={{ backgroundColor: 'rgba(212, 175, 55, 0.12)', border: '1px solid rgba(212,175,55,0.25)' }}>
                    <FaCamera size={32} style={{ color: 'var(--accent-2)' }} />
                  </div>
                  <h5 className="fw-bold">Camera Try-On</h5>
                  <p className="text-muted mb-4">Try clothes instantly using your device camera</p>
                </div>
                <Link to="/dashboard/camera-tryon">
                  <Button variant="primary" className="w-100 py-2">
                    Launch Camera
                  </Button>
                </Link>
              </Card.Body>
            </Card>
          </Col>
          <Col md={4}>
            <Card className="border-0 shadow-sm hover-card h-100" style={{ background: '#111111', border: '1px solid rgba(212,175,55,0.25)' }}>
              <Card.Body className="p-4 text-center">
                <div className="mb-4">
                  <div className="d-inline-flex p-3 rounded-circle mb-3" style={{ backgroundColor: 'rgba(212, 175, 55, 0.12)', border: '1px solid rgba(212,175,55,0.25)' }}>
                    <FaLink size={32} style={{ color: 'var(--accent-2)' }} />
                  </div>
                  <h5 className="fw-bold">Link Try-On</h5>
                  <p className="text-muted mb-4">Try on clothes using product links</p>
                </div>
                <Link to="/dashboard/link-based-tryon">
                  <Button variant="primary" className="w-100 py-2">
                    Try with Link
                  </Button>
                </Link>
              </Card.Body>
            </Card>
          </Col>
          <Col md={4}>
            <Card className="border-0 shadow-sm hover-card h-100" style={{ background: '#111111', border: '1px solid rgba(212,175,55,0.25)' }}>
              <Card.Body className="p-4 text-center">
                <div className="mb-4">
                  <div className="d-inline-flex p-3 rounded-circle mb-3" style={{ backgroundColor: 'rgba(212, 175, 55, 0.12)', border: '1px solid rgba(212,175,55,0.25)' }}>
                    <FaMicrochip size={32} style={{ color: 'var(--accent-2)' }} />
                  </div>
                  <h5 className="fw-bold">RFID Try-On</h5>
                  <p className="text-muted mb-4">Scan RFID tags for instant try-on</p>
                </div>
                <Link to="/dashboard/tryon-qr">
                  <Button variant="primary" className="w-100 py-2">
                    Scan RFID
                  </Button>
                </Link>
              </Card.Body>
            </Card>
          </Col>
        </Row>
      </div>
    </div>
  );
};

export default Dashboard;
