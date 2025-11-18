// src/pages/Home.jsx
import React from 'react';
import { Link } from 'react-router-dom';
import { Button, Container, Row, Col, Card } from 'react-bootstrap';

const Home = () => {
  return (
    <div>
      {/* Hero Section */}
      <section className="hero-section py-5 position-relative" style={{ 
        background: 'var(--gradient-1)',
        color: '#1F2937',
        minHeight: '85vh',
        display: 'flex',
        alignItems: 'center',
        position: 'relative',
        overflow: 'hidden'
      }}>
        <Container className="position-relative" style={{ zIndex: 2 }}>
          <Row className="align-items-center">
            <Col lg={12} className="text-center">
              <h1 className="display-4 fw-bold mb-3" style={{ 
                fontFamily: 'Playfair Display, serif',
                color: '#4C1D95'
              }}>
                👗 Virtual Try-On Revolution
              </h1>
              <p className="lead mb-5" style={{ fontSize: '1.15rem', fontWeight: 400, color: '#374151' }}>
                Discover AI Try-On — try outfits quickly and design your wardrobe effortlessly. Experience true virtual try-on technology for fast and fun fashion experimentation.
              </p>
              <div className="d-flex gap-3 justify-content-center">
                <Link to="/login">
                  <Button 
                    variant="primary" 
                    size="lg" 
                    className="px-4 py-3 fw-semibold"
                    style={{ transition: 'transform 0.2s' }}
                  >
                    Try On Clothes
                  </Button>
                </Link>
                <Link to="/signup">
                  <Button 
                    variant="outline-primary" 
                    size="lg" 
                    className="px-4 py-3"
                    style={{ transition: 'transform 0.2s' }}
                  >
                    Photo to Video
                  </Button>
                </Link>
              </div>
            </Col>
          </Row>
        </Container>
        
        {/* Background decoration */}
        <div style={{
          position: 'absolute',
          top: 0,
          right: 0,
          width: '100%',
          height: '100%',
          background: 'radial-gradient(circle at 70% 30%, rgba(255,255,255,0.6) 0%, rgba(255,255,255,0) 70%)',
          zIndex: 1
        }} />
        <div className="hero-sheen" />
      </section>

      {/* Features Section */}
      <Container className="py-5">
        <h2 className="text-center display-6 mb-5 fw-bold">Why Choose Our Platform?</h2>
        <Row className="g-4 justify-content-center">
          <Col md={6} lg={4}>
            <Card className="h-100 shadow-sm hover-card border-0" style={{ transition: 'transform 0.2s' }}>
              <Card.Body className="p-4 text-center">
                <div className="feature-icon mb-4" style={{ 
                  fontSize: '2.5rem',
                  background: 'linear-gradient(45deg, #6B73FF, #000DFF)',
                  WebkitBackgroundClip: 'text',
                  WebkitTextFillColor: 'transparent'
                }}>
                  🔒
                </div>
                <Card.Title className="fw-bold mb-3">Secure Authentication</Card.Title>
                <Card.Text className="text-muted">
                  Your data is protected with state-of-the-art encryption using FastAPI and MongoDB.
                </Card.Text>
              </Card.Body>
            </Card>
          </Col>
          <Col md={6} lg={4}>
            <Card className="h-100 shadow-sm hover-card border-0" style={{ transition: 'transform 0.2s' }}>
              <Card.Body className="p-4 text-center">
                <div className="feature-icon mb-4" style={{ 
                  fontSize: '2.5rem',
                  background: 'linear-gradient(45deg, #6B73FF, #000DFF)',
                  WebkitBackgroundClip: 'text',
                  WebkitTextFillColor: 'transparent'
                }}>
                  🧠
                </div>
                <Card.Title className="fw-bold mb-3">AI-Powered Try-On</Card.Title>
                <Card.Text className="text-muted">
                  Experience real-time clothes overlay powered by MediaPipe and Deep Learning technology.
                </Card.Text>
              </Card.Body>
            </Card>
          </Col>
          <Col md={6} lg={4}>
            <Card className="h-100 shadow-sm hover-card border-0" style={{ transition: 'transform 0.2s' }}>
              <Card.Body className="p-4 text-center">
                <div className="feature-icon mb-4" style={{ 
                  fontSize: '2.5rem',
                  background: 'linear-gradient(45deg, #6B73FF, #000DFF)',
                  WebkitBackgroundClip: 'text',
                  WebkitTextFillColor: 'transparent'
                }}>
                  📲
                </div>
                <Card.Title className="fw-bold mb-3">Smart Tag Integration</Card.Title>
                <Card.Text className="text-muted">
                  Simply scan RFID/QR smart tags to instantly preview fashion products.
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
