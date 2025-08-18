// src/pages/Home.jsx
import React from 'react';
import { Link } from 'react-router-dom';
import { Button, Container, Row, Col, Card } from 'react-bootstrap';

const Home = () => {
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
};

export default Home;
