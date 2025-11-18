import React, { useEffect, useState, useRef } from 'react';
import { Card, Button, Form, Image, Spinner, Container, Row, Col } from 'react-bootstrap';

function parseJwt(token) {
  try {
    return JSON.parse(atob(token.split('.')[1]));
  } catch (e) {
    return null;
  }
}

const Profile = () => {
  const [user, setUser] = useState(null);
  const [name, setName] = useState('');
  const [photo, setPhoto] = useState('');
  const [editing, setEditing] = useState(false);
  const videoRef = useRef(null);
  const canvasRef = useRef(null);
  const [cameraActive, setCameraActive] = useState(false);

  useEffect(() => {
    const token = localStorage.getItem('token');
    if (token) {
      const decoded = parseJwt(token);
      if (decoded?.email) {
        const savedName = localStorage.getItem('name') || 'User';
        const savedPhoto = localStorage.getItem('photo') || '';
        setUser({ email: decoded.email });
        setName(savedName);
        setPhoto(savedPhoto);
      }
    }
  }, []);

  const startCamera = async () => {
    setCameraActive(true);
    const stream = await navigator.mediaDevices.getUserMedia({ video: true });
    videoRef.current.srcObject = stream;
  };

  const capturePhoto = () => {
    const video = videoRef.current;
    const canvas = canvasRef.current;
    const ctx = canvas.getContext('2d');
    ctx.drawImage(video, 0, 0, canvas.width, canvas.height);
    const dataUrl = canvas.toDataURL('image/png');
    setPhoto(dataUrl);
    localStorage.setItem('photo', dataUrl);

    const stream = video.srcObject;
    stream.getTracks().forEach((track) => track.stop());
    setCameraActive(false);
  };

  const handleSave = () => {
    localStorage.setItem('name', name);
    setEditing(false);
    window.location.reload();
  };

  if (!user) {
    return <div className="text-center"><Spinner animation="border" variant="primary" /></div>;
  }

  return (
    <div className="container py-5">
      <div className="row justify-content-center">
        <div className="col-lg-8">
          <Card className="border-0 shadow-lg" style={{ background: '#111111', border: '1px solid rgba(212,175,55,0.25)' }}>
            <Card.Body className="p-5">
              <div className="text-center mb-5">
                <h2 className="display-6 fw-bold mb-3" style={{ color: 'var(--accent-2)' }}>Profile Settings</h2>
                <p className="text-muted">Manage your account information and preferences</p>
              </div>

              <div className="row justify-content-center mb-5">
                <div className="col-md-6 text-center">
                  {photo ? (
                    <div className="position-relative d-inline-block">
                      <Image
                        src={photo}
                        roundedCircle
                        width={150}
                        height={150}
                        className="shadow"
                        style={{ objectFit: 'cover' }}
                        alt="Profile"
                      />
                      {!editing && (
                        <Button 
                          variant="primary" 
                          size="sm" 
                          className="position-absolute bottom-0 end-0"
                          style={{ borderRadius: '50%', padding: '8px' }}
                          onClick={() => setEditing(true)}
                        >
                          📸
                        </Button>
                      )}
                    </div>
                  ) : (
                    <div className="position-relative d-inline-block">
                      <div
                        className="rounded-circle d-flex justify-content-center align-items-center"
                        style={{ width: 150, height: 150, fontSize: 48, background: 'linear-gradient(145deg, rgba(212,175,55,0.15), rgba(241,214,121,0.10))', border: '1px solid rgba(212,175,55,0.25)' }}
                      >
                        {name.charAt(0).toUpperCase()}
                      </div>
                      {!editing && (
                        <Button 
                          variant="primary" 
                          size="sm" 
                          className="position-absolute bottom-0 end-0"
                          style={{ borderRadius: '50%', padding: '8px' }}
                          onClick={() => setEditing(true)}
                        >
                          📸
                        </Button>
                      )}
                    </div>
                  )}
                </div>
              </div>

              {!editing ? (
                <div className="text-center">
                  <h3 className="fw-bold mb-2" style={{ color: 'var(--accent-2)' }}>{name}</h3>
                  <p className="text-muted mb-4">{user.email}</p>
                  <Button 
                    variant="primary" 
                    onClick={() => setEditing(true)}
                    className="px-4 py-2"
                  >
                    ✏️ Edit Profile
                  </Button>
                </div>
              ) : (
                <div className="row justify-content-center">
                  <div className="col-md-8">
                    <Form.Group className="mb-4">
                      <Form.Label className="fw-semibold">Display Name</Form.Label>
                      <Form.Control
                        type="text"
                        value={name}
                        onChange={(e) => setName(e.target.value)}
                        placeholder="Enter your name"
                        className="py-2"
                      />
                    </Form.Group>

                    <div className="mb-4">
                      <Form.Label className="fw-semibold">Profile Photo</Form.Label>
                      {cameraActive ? (
                        <div className="text-center">
                          <div className="position-relative d-inline-block mb-3">
                            <video 
                              ref={videoRef} 
                              autoPlay 
                              style={{ 
                                width: '100%', 
                                maxWidth: '300px', 
                                borderRadius: '12px',
                                transform: 'scaleX(-1)' 
                              }} 
                            />
                            <canvas ref={canvasRef} style={{ display: 'none' }} width="300" height="300" />
                          </div>
                          <div>
                            <Button 
                              variant="success" 
                              className="me-2 px-4" 
                              onClick={capturePhoto}
                            >
                              📸 Take Photo
                            </Button>
                            <Button 
                              variant="outline-secondary" 
                              onClick={() => {
                                videoRef.current.srcObject.getTracks().forEach(track => track.stop());
                                setCameraActive(false);
                              }}
                            >
                              ❌ Cancel
                            </Button>
                          </div>
                        </div>
                      ) : (
                        <Button 
                          variant="outline-primary" 
                          className="w-100 py-2" 
                          onClick={startCamera}
                        >
                          📸 Open Camera
                        </Button>
                      )}
                    </div>

                    <div className="d-grid gap-2">
                      <Button 
                        variant="primary" 
                        size="lg"
                        onClick={handleSave}
                        className="py-2"
                      >
                        Save Changes
                      </Button>
                      <Button 
                        variant="outline-secondary" 
                        onClick={() => setEditing(false)}
                      >
                        Cancel
                      </Button>
                    </div>
                  </div>
                </div>
              )}
            </Card.Body>
          </Card>
        </div>
      </div>
    </div>
  );
};

export default Profile;
