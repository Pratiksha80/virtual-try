import React, { useState } from 'react';
import { Container, Form, Button, Alert, Card } from 'react-bootstrap';
import { useNavigate, Link } from 'react-router-dom';

const Signup = () => {
  const navigate = useNavigate(); // ✅ init here

  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [message, setMessage] = useState(null);

  const handleSignup = async (e) => {
    e.preventDefault();
    try {
      const response = await fetch('http://127.0.0.1:8000/register', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email, password }),
      });
      const data = await response.json();
      if (response.ok) {
        setMessage({ type: 'success', text: data.message });
        setEmail('');
        setPassword('');

        // ✅ redirect to login page
        setTimeout(() => navigate('/login'), 1000);
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
          <h2 className="display-6 fw-bold text-white mb-2">Create Account 🎉</h2>
          <p className="text-light mb-4">Join us and start your virtual try-on journey</p>
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
          
          <Form onSubmit={handleSignup}>
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
              <Form.Text className="text-muted">
                We'll never share your email with anyone else.
              </Form.Text>
            </Form.Group>

            <Form.Group className="mb-4" controlId="formPassword">
              <Form.Label className="fw-semibold mb-2">Password</Form.Label>
              <Form.Control
                type="password"
                placeholder="Choose a strong password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                required
                className="py-2 px-3"
                style={{ borderRadius: '10px' }}
              />
              <Form.Text className="text-muted">
                Must be at least 8 characters long.
              </Form.Text>
            </Form.Group>

            <Button 
              variant="primary" 
              type="submit" 
              className="w-100 py-3 mb-3"
              style={{ borderRadius: '10px' }}
            >
              Create Account
            </Button>
            
            <p className="text-center text-muted mb-0">
              Already have an account? {' '}
              <Link to="/login" className="text-decoration-none fw-semibold" style={{ color: 'var(--accent-2)' }}>
                Log in
              </Link>
            </p>
          </Form>
        </Card>
      </Container>
    </Container>
  );
};

export default Signup;
