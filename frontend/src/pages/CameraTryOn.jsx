import React from 'react';
import { Container, Row, Col, Button, Card, Alert, Spinner } from 'react-bootstrap';

const CameraTryOn = () => {
  const videoRef = React.useRef(null);
  const canvasRef = React.useRef(null);
  const [isReady, setIsReady] = React.useState(false);
  const [isCapturing, setIsCapturing] = React.useState(false);
  const [error, setError] = React.useState('');
  const [imageDataUrl, setImageDataUrl] = React.useState('');

  React.useEffect(() => {
    let stream;
    const start = async () => {
      try {
        setError('');
        setIsCapturing(true);
        stream = await navigator.mediaDevices.getUserMedia({ video: { facingMode: 'user', width: { ideal: 1280 }, height: { ideal: 720 } }, audio: false });
        if (videoRef.current) {
          videoRef.current.srcObject = stream;
          await videoRef.current.play();
          setIsReady(true);
        }
      } catch (err) {
        setError(err?.message || 'Camera access denied or unavailable.');
      } finally {
        setIsCapturing(false);
      }
    };
    start();
    return () => {
      if (stream) {
        stream.getTracks().forEach(t => t.stop());
      }
    };
  }, []);

  const handleCapture = () => {
    const video = videoRef.current;
    const canvas = canvasRef.current;
    if (!video || !canvas) return;
    const width = video.videoWidth;
    const height = video.videoHeight;
    canvas.width = width;
    canvas.height = height;
    const ctx = canvas.getContext('2d');
    ctx.drawImage(video, 0, 0, width, height);
    const dataUrl = canvas.toDataURL('image/png');
    setImageDataUrl(dataUrl);
  };

  const handleRetake = () => {
    setImageDataUrl('');
  };

  const handleDownload = () => {
    if (!imageDataUrl) return;
    const a = document.createElement('a');
    a.href = imageDataUrl;
    a.download = 'capture.png';
    a.click();
  };

  return (
    <Container className="py-4">
      <Row className="mb-4">
        <Col>
          <h2 className="fw-bold mb-1" style={{ color: 'var(--primary-color)' }}>Camera Try-On</h2>
          <div className="text-muted">Allow camera access to capture your photo for try-on</div>
        </Col>
      </Row>

      {error && (
        <Alert variant="danger" className="mb-4">
          {error}
        </Alert>
      )}

      <Row className="g-4 align-items-stretch">
        <Col lg={8}>
          <Card className="shadow-sm border-0 h-100" style={{ overflow: 'hidden', background: 'var(--surface-color)', border: '1px solid var(--border-color)' }}>
            <div style={{ position: 'relative', background: '#000' }}>
              {!imageDataUrl && (
                <video
                  ref={videoRef}
                  playsInline
                  muted
                  style={{ width: '100%', height: 'auto', display: isReady ? 'block' : 'none' }}
                />
              )}
              {imageDataUrl && (
                <img src={imageDataUrl} alt="Captured" style={{ width: '100%', height: 'auto', display: 'block' }} />
              )}
              {!isReady && !error && (
                <div style={{ position: 'absolute', inset: 0, display: 'flex', alignItems: 'center', justifyContent: 'center', color: 'white' }}>
                  <div className="d-flex align-items-center gap-2">
                    <Spinner animation="border" variant="light" size="sm" />
                    <span>Initializing camera…</span>
                  </div>
                </div>
              )}
            </div>
          </Card>
        </Col>
        <Col lg={4}>
          <Card className="shadow-sm border-0 h-100" style={{ background: 'var(--surface-color)', border: '1px solid var(--border-color)' }}>
            <Card.Body className="d-flex flex-column">
              <div className="mb-3">
                <div className="fw-semibold mb-1">Tips</div>
                <div className="text-muted small">Ensure good lighting and keep your face centered.</div>
              </div>
              <div className="mt-auto d-grid gap-2">
                {!imageDataUrl ? (
                  <>
                    <Button disabled={!isReady || isCapturing} size="lg" onClick={handleCapture}>
                      {isCapturing ? 'Please wait…' : 'Capture Photo'}
                    </Button>
                  </>
                ) : (
                  <>
                    <Button variant="primary" size="lg" onClick={handleDownload}>Download</Button>
                    <Button variant="outline-secondary" onClick={handleRetake}>Retake</Button>
                  </>
                )}
              </div>
            </Card.Body>
          </Card>
        </Col>
      </Row>

      <canvas ref={canvasRef} style={{ display: 'none' }} />
    </Container>
  );
};

export default CameraTryOn;


