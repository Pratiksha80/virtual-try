import React, { useState, useRef } from 'react';
import { Container, Form, Button, Image, Spinner, Alert } from 'react-bootstrap';
import { Camera, Upload } from 'lucide-react';
import axios from 'axios';

const BACKEND_URL = import.meta.env.VITE_BACKEND_URL || 'http://localhost:8000';

const CLOTH_TYPES = ['shirt', 'pant', 'dress', 'saree']; // lowercase to match backend

const LinkBasedTryOn = () => {
    const [productLink, setProductLink] = useState('');
    const [clothType, setClothType] = useState('shirt');
    const [userImage, setUserImage] = useState(null);
    const [userImagePreview, setUserImagePreview] = useState(null);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState(null);
    const [result, setResult] = useState(null);
    const fileInputRef = useRef(null);

    const handleFileChange = (e) => {
        const file = e.target.files[0];
        if (file) {
            // Validate file type
            if (!file.type.startsWith('image/')) {
                setError('Please select a valid image file');
                return;
            }

            // Validate file size (max 10MB)
            if (file.size > 10 * 1024 * 1024) {
                setError('Image file size should be less than 10MB');
                return;
            }

            setUserImage(file);
            setError(null);
            
            // Create preview
            const reader = new FileReader();
            reader.onload = (e) => {
                setUserImagePreview(e.target.result);
            };
            reader.readAsDataURL(file);
        }
    };

    const handleCapture = () => {
        // TODO: Implement camera capture functionality
        alert('Camera capture will be implemented soon!');
    };

    const validateForm = () => {
        if (!productLink.trim()) {
            setError('Please enter a product link');
            return false;
        }

        // Basic URL validation
        try {
            new URL(productLink);
        } catch {
            setError('Please enter a valid URL');
            return false;
        }

        if (!userImage) {
            setError('Please select an image');
            return false;
        }

        return true;
    };

    const handleSubmit = async (e) => {
        e.preventDefault();
        
        if (!validateForm()) {
            return;
        }

        setLoading(true);
        setError(null);
        setResult(null);

        const formData = new FormData();
        formData.append('link', productLink.trim());
        formData.append('cloth_type', clothType);
        formData.append('image', userImage);

        try {
            console.log('Sending request with:', { 
                productLink: productLink.trim(), 
                clothType,
                imageSize: userImage.size,
                imageName: userImage.name 
            });

            const response = await axios.post(`${BACKEND_URL}/tryon/link`, formData, {
                headers: {
                    'Content-Type': 'multipart/form-data',
                },
                timeout: 60000, // 60 second timeout
                onUploadProgress: (progressEvent) => {
                    const percentCompleted = Math.round((progressEvent.loaded * 100) / progressEvent.total);
                    console.log(`Upload Progress: ${percentCompleted}%`);
                }
            });

            console.log('Response received:', response.data);

            if (response.data.status === 'done') {
                if (response.data.output_image_base64) {
                    setResult(response.data);
                } else {
                    setError('Processing completed but no image was returned');
                }
            } else if (response.data.error) {
                setError(response.data.error);
            } else {
                setError(response.data.detail || 'Processing failed');
            }
        } catch (error) {
            console.error('Request failed:', error);
            
            if (error.code === 'ECONNABORTED') {
                setError('Request timed out. Please try again with a smaller image.');
            } else if (error.response) {
                // Server responded with error status
                const errorMessage = error.response.data?.error || 
                                   error.response.data?.detail || 
                                   `Server error: ${error.response.status}`;
                setError(errorMessage);
            } else if (error.request) {
                // Request made but no response
                setError('Unable to connect to server. Please check your connection.');
            } else {
                // Other error
                setError(`Request failed: ${error.message}`);
            }
        } finally {
            setLoading(false);
        }
    };

    const resetForm = () => {
        setProductLink('');
        setClothType('shirt');
        setUserImage(null);
        setUserImagePreview(null);
        setError(null);
        setResult(null);
        if (fileInputRef.current) {
            fileInputRef.current.value = '';
        }
    };

    const downloadResult = () => {
        if (!result?.output_image_base64) return;
        
        try {
            const link = document.createElement('a');
            link.href = `data:image/png;base64,${result.output_image_base64}`;
            link.download = `virtual-tryon-${Date.now()}.png`;
            document.body.appendChild(link);
            link.click();
            document.body.removeChild(link);
        } catch (error) {
            console.error('Download failed:', error);
            setError('Failed to download image');
        }
    };

    return (
        <Container className="mt-4">
            <div className="text-center mb-5">
                <h2 style={{ color: 'var(--primary-color)' }}>✨ Your Virtual Try-On</h2>
                <p className="text-muted">AI-Powered Fashion</p>
                <h4 className="mt-4" style={{ color: 'var(--primary-color)' }}>💎 Try-On with Link</h4>
            </div>

            <div className="mx-auto" style={{ maxWidth: '600px' }}>
                <Form onSubmit={handleSubmit} className="p-4 rounded-3 shadow-sm" style={{ background: 'var(--surface-color)', border: '1px solid var(--border-color)' }}>
                    <Form.Group className="mb-4">
                        <Form.Label className="fw-bold">Paste Product Link</Form.Label>
                        <Form.Control
                            type="url"
                            value={productLink}
                            onChange={(e) => setProductLink(e.target.value)}
                            placeholder="https://www.amazon.in/product-link"
                            className="py-2"
                            required
                        />
                        <Form.Text className="text-muted">
                            Supported: Amazon, Flipkart, and other e-commerce sites
                        </Form.Text>
                    </Form.Group>

                    <Form.Group className="mb-4">
                        <Form.Label className="fw-bold">Select Cloth Type</Form.Label>
                        <Form.Select
                            value={clothType}
                            onChange={(e) => setClothType(e.target.value)}
                            className="py-2"
                        >
                            {CLOTH_TYPES.map(type => (
                                <option key={type} value={type}>
                                    {type.charAt(0).toUpperCase() + type.slice(1)}
                                </option>
                            ))}
                        </Form.Select>
                    </Form.Group>

                    <Form.Group className="mb-4">
                        <Form.Label className="fw-bold">Upload Full Body Image</Form.Label>
                        <div className="d-grid gap-2">
                            <Button 
                                variant="outline-secondary" 
                                className="py-3 d-flex align-items-center justify-content-center gap-2"
                                onClick={() => fileInputRef.current?.click()}
                                type="button"
                            >
                                <Upload size={20} />
                                {userImage ? 'Change Image' : 'Choose File'}
                            </Button>
                            <Button 
                                variant="outline-primary" 
                                className="py-3 d-flex align-items-center justify-content-center gap-2"
                                onClick={handleCapture}
                                type="button"
                            >
                                <Camera size={20} />
                                Capture Using Camera
                            </Button>
                            <Form.Control
                                type="file"
                                ref={fileInputRef}
                                onChange={handleFileChange}
                                accept="image/*"
                                className="d-none"
                            />
                            {userImage && (
                                <div className="text-center mt-2">
                                    <div className="text-muted mb-2">
                                        Selected: {userImage.name} ({(userImage.size / 1024 / 1024).toFixed(1)} MB)
                                    </div>
                                    {userImagePreview && (
                                        <Image 
                                            src={userImagePreview} 
                                            alt="Preview" 
                                            style={{ maxHeight: '200px', maxWidth: '150px' }}
                                            className="rounded"
                                        />
                                    )}
                                </div>
                            )}
                        </div>
                        <Form.Text className="text-muted">
                            For best results, use a clear, full-body image with good lighting
                        </Form.Text>
                    </Form.Group>

                    <div className="d-grid gap-2 mt-4">
                        <Button 
                            variant="primary" 
                            type="submit" 
                            disabled={loading || !productLink.trim() || !userImage} 
                            className="py-3"
                        >
                            {loading ? (
                                <>
                                    <Spinner animation="border" size="sm" className="me-2" />
                                    Processing your request...
                                </>
                            ) : (
                                'Try Now'
                            )}
                        </Button>
                        
                        {(userImage || productLink || result) && (
                            <Button 
                                variant="outline-secondary" 
                                onClick={resetForm}
                                className="py-2"
                                type="button"
                            >
                                Reset Form
                            </Button>
                        )}
                    </div>
                </Form>

                {error && (
                    <Alert variant="danger" className="mt-4" dismissible onClose={() => setError(null)}>
                        <strong>Error:</strong> {error}
                    </Alert>
                )}

                {result && (
                    <div className="mt-5">
                        <div className="text-center mb-4">
                            <h3 style={{ color: 'var(--accent-2)' }}>🎉 Your Virtual Try-On Result</h3>
                            {result.preferred_size && (
                                <p className="text-muted">
                                    Recommended Size: <strong>{result.preferred_size}</strong>
                                </p>
                            )}
                        </div>
                        <div className="d-flex flex-column align-items-center">
                            <div style={{ maxWidth: '500px', width: '100%' }}>
                                <Image 
                                    src={`data:image/png;base64,${result.output_image_base64}`}
                                    alt="Virtual Try-On Result" 
                                    fluid 
                                    className="rounded-3 shadow-sm"
                                    style={{ width: '100%', objectFit: 'cover' }} 
                                />
                            </div>
                            <div className="d-flex gap-2 mt-4">
                                <Button 
                                    variant="success" 
                                    className="d-flex align-items-center gap-2"
                                    style={{ 
                                        borderRadius: '50px',
                                        padding: '10px 24px',
                                        fontSize: '1.1rem'
                                    }}
                                    onClick={downloadResult}
                                >
                                    <span role="img" aria-label="download">⬇️</span> Download Result
                                </Button>
                                <Button 
                                    variant="outline-primary" 
                                    className="d-flex align-items-center gap-2"
                                    style={{ 
                                        borderRadius: '50px',
                                        padding: '10px 24px',
                                        fontSize: '1.1rem'
                                    }}
                                    onClick={() => setResult(null)}
                                >
                                    Try Another
                                </Button>
                            </div>
                        </div>
                    </div>
                )}
            </div>
        </Container>
    );
};

export default LinkBasedTryOn;