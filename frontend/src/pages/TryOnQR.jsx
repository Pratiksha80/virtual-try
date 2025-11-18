import React, { useState } from 'react';
import { Container, Card, Button, Alert } from 'react-bootstrap';
import { FaMicrochip } from 'react-icons/fa';

const TryOnQR = () => {
  const [scanning, setScanning] = useState(false);
  const [scannedCode, setScannedCode] = useState(null);
  const [error, setError] = useState(null);

  const startScanning = () => {
    setScanning(true);
    // Simulated scanning process
    setTimeout(() => {
      setScanning(false);
      setScannedCode('SAMPLE-RFID-001');
    }, 2000);
  };

  return (
    <Container className="py-5">
      <div className="text-center mb-5">
        <h2 className="display-6 fw-bold mb-3" style={{ color: 'var(--accent-2)' }}>📱 Smart Tag Try-On</h2>
        <p className="lead text-muted">
          Scan RFID or QR tags to instantly preview clothes on yourself
        </p>
      </div>

      <div className="row justify-content-center">
        <div className="col-lg-8">
          <Card className="border-0 shadow-lg" style={{ background: 'var(--surface-color)', border: '1px solid var(--border-color)' }}>
            <Card.Body className="p-5">
              {error && (
                <Alert variant="danger" className="mb-4">
                  {error}
                </Alert>
              )}

              <div className="text-center mb-4">
                <div
                  className="d-inline-flex align-items-center justify-content-center mb-4"
                  style={{
                    width: '120px',
                    height: '120px',
                    borderRadius: '50%',
                    background: 'rgba(37,99,235,0.1)',
                    border: '1px solid var(--border-color)'
                  }}
                >
                  <FaMicrochip size={48} style={{ color: 'var(--primary-color)' }} />
                </div>
                
                {!scanning && !scannedCode && (
                  <div>
                    <h4 className="mb-3">Ready to Scan</h4>
                    <p className="text-muted mb-4">
                      Position your device near the smart tag to begin scanning
                    </p>
                    <Button 
                      variant="primary" 
                      size="lg" 
                      className="px-5 py-3"
                      onClick={startScanning}
                    >
                      Start Scanning
                    </Button>
                  </div>
                )}

                {scanning && (
                  <div>
                    <h4 className="mb-3">Scanning...</h4>
                    <p className="text-muted">
                      Please keep your device close to the tag
                    </p>
                    <div className="spinner-grow" role="status" style={{ color: 'var(--primary-color)' }}>
                      <span className="visually-hidden">Loading...</span>
                    </div>
                  </div>
                )}

                {scannedCode && (
                  <div>
                    <h4 className="mb-3">Tag Detected! 🎉</h4>
                    <p className="text-muted mb-4">
                      Successfully scanned tag: {scannedCode}
                    </p>
                    <div className="d-grid gap-3">
                      <Button variant="success" size="lg">
                        Try On This Item
                      </Button>
                      <Button 
                        variant="outline-primary"
                        onClick={() => {
                          setScannedCode(null);
                          startScanning();
                        }}
                      >
                        Scan Another Tag
                      </Button>
                    </div>
                  </div>
                )}
              </div>
            </Card.Body>
          </Card>

          <div className="text-center mt-4">
            <p className="text-muted">
              <small>
                Make sure your device supports RFID/NFC scanning and is enabled
              </small>
            </p>
          </div>
        </div>
      </div>
    </Container>
  );
};

export default TryOnQR;
