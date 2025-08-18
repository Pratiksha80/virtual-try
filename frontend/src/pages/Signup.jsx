import React, { useState } from 'react';
import { Container, Form, Button, Alert } from 'react-bootstrap';
import { useNavigate } from 'react-router-dom'; // ✅ import this

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
    <Container className="mt-5" style={{ maxWidth: '400px' }}>
      <h2 className="mb-4">Sign Up</h2>
      {message && <Alert variant={message.type}>{message.text}</Alert>}
      <Form onSubmit={handleSignup}>
        <Form.Group className="mb-3" controlId="formEmail">
          <Form.Label>Email address</Form.Label>
          <Form.Control type="email" placeholder="Enter email" value={email}
            onChange={(e) => setEmail(e.target.value)} required />
        </Form.Group>

        <Form.Group className="mb-4" controlId="formPassword">
          <Form.Label>Password</Form.Label>
          <Form.Control type="password" placeholder="Password" value={password}
            onChange={(e) => setPassword(e.target.value)} required />
        </Form.Group>

        <Button variant="primary" type="submit" className="w-100">Register</Button>
      </Form>
    </Container>
  );
};

export default Signup;
