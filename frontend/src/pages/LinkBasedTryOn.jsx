import React, { useState, useRef } from 'react';
import { Form, Button, Card, Spinner, Alert, Container } from 'react-bootstrap';

const LinkBasedTryOn = () => {
  const [link, setLink] = useState('');
  const [clothType, setClothType] = useState('shirt');
  const [imageFile, setImageFile] = useState(null);
  const [preview, setPreview] = useState(null);
  const [loading, setLoading] = useState(false);
  const [resultImg, setResultImg] = useState(null);
  const [error, setError] = useState(null);
  const [useCamera, setUseCamera] = useState(false);

  const videoRef = useRef(null);
  const canvasRef = useRef(null);

  // 📂 File upload handler
  const handleImageChange = (e) => {
    const file = e.target.files[0];
    setImageFile(file);
    if (file) {
      const reader = new FileReader();
      reader.onloadend = () => setPreview(reader.result);
      reader.readAsDataURL(file);
    }
  };

  // 📷 Start camera
  const startCamera = async () => {
    try {
      setUseCamera(true);
      const stream = await navigator.mediaDevices.getUserMedia({ video: { width: 1280, height: 720 } });
      if (videoRef.current) videoRef.current.srcObject = stream;
    } catch (err) {
      console.error("Camera error:", err);
      alert("Unable to access camera.");
    }
  };

  // 📸 Capture from camera
  const capturePhoto = () => {
    const video = videoRef.current;
    const canvas = canvasRef.current;
    const ctx = canvas.getContext('2d');
    canvas.width = video.videoWidth;
    canvas.height = video.videoHeight;
    ctx.drawImage(video, 0, 0);

    canvas.toBlob(blob => {
      const file = new File([blob], 'captured.png', { type: 'image/png' });
      setImageFile(file);
      const reader = new FileReader();
      reader.onloadend = () => setPreview(reader.result);
      reader.readAsDataURL(file);
    });

    video.srcObject.getTracks().forEach(track => track.stop());
    setUseCamera(false);
  };

  // 🚀 Submit form (NO SSE, plain JSON)
  const handleSubmit = async (e) => {
    e.preventDefault();

    if (!link || !imageFile) {
      setError("Please provide both a product link and an image.");
      return;
    }

    setLoading(true);
    setResultImg(null);
    setError(null);

    const formData = new FormData();
    formData.append('link', link);
    formData.append('cloth_type', clothType);
    formData.append('image', imageFile);

    try {
      const response = await fetch('http://127.0.0.1:8000/tryon/link', {
        method: 'POST',
        body: formData,
      });

      const data = await response.json();

      if (response.ok) {
        setResultImg(`data:image/png;base64,${data.output_image_base64}`);
      } else {
        setError(data.detail || 'Something went wrong.');
      }
    } catch (err) {
      setError("Server error: " + err.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <Container fluid className="py-4 px-3">
      <Container style={{ maxWidth: '600px' }}>
        <h3 className="mb-4">🔗 Link-Based Try-On</h3>

        {error && <Alert variant="danger">{error}</Alert>}

        <Form onSubmit={handleSubmit}>
          <Form.Group className="mb-3">
            <Form.Label>Paste Product Link</Form.Label>
            <Form.Control
              type="url"
              placeholder="https://www.amazon.in/..."
              value={link}
              onChange={(e) => setLink(e.target.value)}
              required
            />
          </Form.Group>

          <Form.Group className="mb-3">
            <Form.Label>Select Cloth Type</Form.Label>
            <Form.Select
              value={clothType}
              onChange={(e) => setClothType(e.target.value)}
            >
              <option value="shirt">Shirt</option>
              <option value="pant">Pant</option>
              <option value="dress">Dress</option>
            </Form.Select>
          </Form.Group>

          <Form.Group className="mb-3">
            <Form.Label>Upload Full Body Image</Form.Label>
            <Form.Control
              type="file"
              accept="image/*"
              onChange={handleImageChange}
              disabled={useCamera}
            />
          </Form.Group>

          <Button variant="outline-secondary" onClick={startCamera} className="mb-3 w-100">
            📸 Capture Using Camera
          </Button>

          {preview && (
            <div className="text-center mb-3">
              <img src={preview} alt="preview" className="img-fluid rounded" style={{ maxHeight: 300 }} />
            </div>
          )}

          <Button type="submit" disabled={loading} className="w-100">
            {loading ? <Spinner animation="border" size="sm" /> : 'Try Now'}
          </Button>
        </Form>

        {resultImg && (
          <Card className="mt-4 p-3 text-center shadow-sm">
            <h5 className="mb-3">🧥 Virtual Try-On Output</h5>
            <img
              src={resultImg}
              alt="Result"
              className="img-fluid rounded"
              style={{ maxHeight: 400 }}
            />
          </Card>
        )}
      </Container>

      {useCamera && (
        <div
          style={{
            position: 'fixed',
            top: 0,
            left: 0,
            width: '100vw',
            height: '100vh',
            backgroundColor: 'rgba(0, 0, 0, 0.9)',
            display: 'flex',
            flexDirection: 'column',
            justifyContent: 'center',
            alignItems: 'center',
            zIndex: 9999,
          }}
        >
          <video ref={videoRef} autoPlay playsInline style={{ maxWidth: '100%', maxHeight: '80vh' }} />
          <canvas ref={canvasRef} style={{ display: 'none' }} />
          <Button variant="success" className="mt-3" onClick={capturePhoto}>
            📸 Capture Photo
          </Button>
        </div>
      )}
    </Container>
  );
};

export default LinkBasedTryOn;
