import React, { useEffect, useState, useRef } from 'react';
import { Card, Button, Form, Image, Spinner } from 'react-bootstrap';

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
    <Card className="p-4 shadow-sm text-center">
      {photo ? (
        <Image
          src={photo}
          roundedCircle
          width={120}
          height={120}
          className="mb-3"
          alt="Profile"
        />
      ) : (
        <div className="mb-3">
          <Image
            src={`https://ui-avatars.com/api/?name=${name}&background=0D8ABC&color=fff`}
            roundedCircle
            width={120}
            height={120}
            alt="Default Avatar"
          />
        </div>
      )}

      {!editing ? (
        <>
          <h4 className="mb-1">{name}</h4>
          <p className="text-muted">{user.email}</p>
          <Button variant="outline-primary" onClick={() => setEditing(true)}>
            Edit Profile
          </Button>
        </>
      ) : (
        <>
          <Form.Group className="mb-2">
            <Form.Control
              type="text"
              value={name}
              onChange={(e) => setName(e.target.value)}
              placeholder="Enter name"
            />
          </Form.Group>

          {cameraActive ? (
            <>
              <video ref={videoRef} autoPlay width="120" height="120" className="mb-2" />
              <canvas ref={canvasRef} width="120" height="120" style={{ display: 'none' }} />
              <Button variant="success" className="me-2" onClick={capturePhoto}>
                Capture Photo
              </Button>
            </>
          ) : (
            <Button variant="secondary" className="me-2" onClick={startCamera}>
              Open Camera
            </Button>
          )}

          <div className="mt-3">
            <Button variant="primary" onClick={handleSave}>
              Save
            </Button>
            <Button variant="link" onClick={() => setEditing(false)}>
              Cancel
            </Button>
          </div>
        </>
      )}
    </Card>
  );
};

export default Profile;
