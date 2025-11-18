// src/Login.jsx
import React, { useState } from 'react';
import { Container, Form, Button, Alert, Card } from 'react-bootstrap';
import { useNavigate, Link } from 'react-router-dom';

const Login = () => {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [message, setMessage] = useState(null);
  const navigate = useNavigate();

  const handleLogin = async (e) => {
    e.preventDefault();
    try {
      const response = await fetch('http://127.0.0.1:8000/login', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email, password }),
      });

      const data = await response.json();

      if (response.ok) {
        localStorage.setItem('token', data.token);
        setMessage({ type: 'success', text: data.message });
        setEmail('');
        setPassword('');
        navigate('/dashboard');
      } else {
        setMessage({ type: 'danger', text: data.detail });
      }
    } catch (error) {
      console.error(error);
      setMessage({ type: 'danger', text: 'Error connecting to server' });
    }
  };

  return (
    <Container fluid className="min-vh-100 d-flex align-items-center justify-content-center py-5" style={{ background: 'linear-gradient(135deg, #0d0d0e 0%, #000000 100%)' }}>
      <Container style={{ maxWidth: '420px' }}>
        <div className="text-center mb-4">
          <h2 className="display-6 fw-bold text-white mb-2">Welcome Back! 👋</h2>
          <p className="text-light mb-4">Log in to access your virtual try-on experience</p>
        </div>
        
        <Card className="shadow-lg p-4 border-0" style={{ background: '#111111', color: 'var(--text-primary)', border: '1px solid rgba(212,175,55,0.25)' }}>
          {message && (
            <Alert 
              variant={message.type} 
              className="mb-4 animate__animated animate__fadeIn"
              style={{ borderRadius: '12px' }}
            >
              {message.text}
            </Alert>
          )}
          
          <Form onSubmit={handleLogin}>
            <Form.Group className="mb-4" controlId="formEmail">
              <Form.Label className="fw-semibold mb-2">Email address</Form.Label>
              <Form.Control
                type="email"
                placeholder="Enter your email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                required
                className="py-2 px-3"
                style={{ borderRadius: '10px' }}
              />
            </Form.Group>

            <Form.Group className="mb-4" controlId="formPassword">
              <div className="d-flex justify-content-between align-items-center mb-2">
                <Form.Label className="fw-semibold mb-0">Password</Form.Label>
                <a href="#" className="text-primary text-decoration-none small">Forgot password?</a>
              </div>
              <Form.Control
                type="password"
                placeholder="Enter your password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                required
                className="py-2 px-3"
                style={{ borderRadius: '10px' }}
              />
            </Form.Group>

            <Button 
              variant="primary" 
              type="submit" 
              className="w-100 py-3 mb-3"
              style={{ borderRadius: '10px' }}
            >
              Login to Account
            </Button>
            
            <p className="text-center text-muted mb-0">
              Don't have an account? {' '}
              <Link to="/signup" className="text-decoration-none fw-semibold" style={{ color: 'var(--accent-2)' }}>
                Sign up
              </Link>
            </p>
          </Form>
        </Card>
      </Container>
    </Container>
  );
};

export default Login;