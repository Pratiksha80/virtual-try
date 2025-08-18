// src/pages/Dashboard.jsx
import React, { useEffect, useState } from "react";
import { Card, Row, Col, Button, Badge } from "react-bootstrap";
import { FaCamera, FaLink, FaMicrochip } from "react-icons/fa";

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
    <div>
      <h2 className="mb-4">👋 Welcome to Your Dashboard!</h2>

      <Row className="mb-4">
        <Col md={6}>
          <Card className="shadow-sm">
            <Card.Body className="d-flex align-items-center gap-3">
              {profileImage ? (
                <img
                  src={profileImage}
                  alt="Profile"
                  className="rounded-circle"
                  style={{ width: 80, height: 80, objectFit: "cover" }}
                />
              ) : (
                <div
                  className="rounded-circle bg-primary text-white d-flex justify-content-center align-items-center"
                  style={{ width: 80, height: 80, fontSize: 28 }}
                >
                  {user.name.charAt(0).toUpperCase()}
                </div>
              )}

              <div>
                <h5 className="mb-1">{user.name}</h5>
                <p className="text-muted mb-2">{user.email}</p>
                {/* Edit button removed as per request */}
              </div>
            </Card.Body>
          </Card>
        </Col>

        <Col md={6}>
          <Card className="shadow-sm h-100">
            <Card.Body>
              <h6 className="text-muted mb-2">📈 Recent Activity</h6>
              <ul className="mb-0">
                <li>Scanned RFID for "T-Shirt Pro Max"</li>
                <li>Used Link-Based Try-On at 3:45 PM</li>
                <li>Updated profile photo</li>
              </ul>
            </Card.Body>
          </Card>
        </Col>
      </Row>

      <h5 className="mb-3">⚡ Quick Access</h5>
      <Row className="g-3">
        <Col md={4}>
          <Card className="text-center shadow-sm p-3">
            <FaCamera size={36} className="mb-2 text-primary" />
            <h6>Try via Camera</h6>
            <Button variant="primary" size="sm" className="mt-2 w-100">
              Launch
            </Button>
          </Card>
        </Col>
        <Col md={4}>
          <Card className="text-center shadow-sm p-3">
            <FaLink size={36} className="mb-2 text-success" />
            <h6>Link-Based Try-On</h6>
            <Button variant="success" size="sm" className="mt-2 w-100">
              Open
            </Button>
          </Card>
        </Col>
        <Col md={4}>
          <Card className="text-center shadow-sm p-3">
            <FaMicrochip size={36} className="mb-2 text-warning" />
            <h6>RFID Try-On</h6>
            <Button variant="warning" size="sm" className="mt-2 w-100">
              Scan
            </Button>
          </Card>
        </Col>
      </Row>
    </div>
  );
};

export default Dashboard;
