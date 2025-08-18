// src/pages/EditProfile.jsx
import React, { useState } from "react";
import { Form, Button, Container, Alert } from "react-bootstrap";

const EditProfile = () => {
  const existingUser = JSON.parse(localStorage.getItem("user")) || {};
  const [name, setName] = useState(existingUser.name || "");
  const [photo, setPhoto] = useState(existingUser.photo || "");
  const [message, setMessage] = useState(null);

  const handlePhotoChange = (e) => {
    const file = e.target.files[0];
    if (file) {
      const reader = new FileReader();
      reader.onloadend = () => setPhoto(reader.result);
      reader.readAsDataURL(file);
    }
  };

  const handleSubmit = (e) => {
    e.preventDefault();
    const updatedUser = { ...existingUser, name, photo };
    localStorage.setItem("user", JSON.stringify(updatedUser));
    setMessage("Profile updated successfully.");
  };

  return (
    <Container style={{ maxWidth: "500px" }} className="mt-4">
      <h2 className="mb-3">Edit Profile</h2>
      {message && <Alert variant="success">{message}</Alert>}
      <Form onSubmit={handleSubmit}>
        <Form.Group className="mb-3">
          <Form.Label>Name</Form.Label>
          <Form.Control value={name} onChange={(e) => setName(e.target.value)} />
        </Form.Group>
        <Form.Group className="mb-3">
          <Form.Label>Upload Profile Picture</Form.Label>
          <Form.Control type="file" accept="image/*" onChange={handlePhotoChange} />
        </Form.Group>
        {photo && <img src={photo} alt="Preview" className="img-thumbnail mb-3" style={{ maxHeight: "150px" }} />}
        <Button type="submit">Save</Button>
      </Form>
    </Container>
  );
};

export default EditProfile;
