# 🎮 Connect4 AI – Cloud-Deployed Web Application

![Python](https://img.shields.io/badge/Python-3.10-blue)
![Anvil](https://img.shields.io/badge/Frontend-Anvil-purple)
![AWS](https://img.shields.io/badge/Cloud-AWS%20Lightsail-orange)
![Docker](https://img.shields.io/badge/Container-Docker-blue)
![TensorFlow](https://img.shields.io/badge/ML-TensorFlow-red)
![License](https://img.shields.io/badge/License-MIT-green)
![UT Austin](https://img.shields.io/badge/UT%20Austin-McCombs%20School%20of%20Business-burnt%20orange)

---

## 🧠 Project Overview

This project is a fully deployed AI-powered Connect4 web application. Unlike a typical classroom ML assignment that stops at model training, this system was engineered end-to-end:

* A deep learning model trained to play Connect4
* A Python-based web frontend built in Anvil
* A Dockerized backend hosted on AWS Lightsail
* Real-time inference using Anvil Uplink
* Cloud-based production-style deployment

The emphasis of this project was not just predictive accuracy, but system design, robustness, and deployability.

---

## 🏗️ System Architecture

## Architecture Overview

![System_Architecture](report/assets/System%20Architecture%20Diagram.png)

### End-to-End Flow

1. A user interacts with the Connect4 board in their browser.
2. The Anvil frontend captures the move and updates the local UI.
3. A server-side Anvil module validates the move and prepares the board state.
4. The request is sent through Anvil Uplink to an AWS Lightsail instance.
5. Inside AWS, a Docker container runs the inference server.
6. The trained model (CNN or Transformer) predicts the best column.
7. The prediction is returned to Anvil and rendered on the board.

This architecture cleanly separates user interface logic from machine learning inference, mirroring real-world production deployments.

---

## 🖥️ Frontend Design – Anvil

The frontend is built entirely in Python using Anvil’s web framework. The design intentionally separates client-side UI logic from server-side execution.

### Client Responsibilities

* Rendering the 6×7 board grid
* Handling click events for column selection
* Displaying animations and win conditions
* Managing login, signup, and password reset flows

### Server Module Responsibilities

* Validating moves and preventing illegal states
* Locking board state during inference
* Communicating with AWS via Uplink
* Returning AI predictions safely to the client

Authentication includes password validation using regex rules, server-side checks, and database consistency enforcement.

---

## 🧠 Model Design and Training

The board is encoded as a 6×7 matrix with integer values representing empty spaces, the human player, and the AI. Before inference, this matrix is transformed into a tensor suitable for deep learning input.

Two model architectures were implemented:

### Convolutional Neural Network (CNN)

The CNN leverages spatial structure in the board. Convolutions capture patterns such as vertical, horizontal, and diagonal threats effectively. It provides fast inference and strong tactical play.

### Transformer-Based Model

The Transformer captures long-range dependencies using attention mechanisms. This allows the model to learn more strategic patterns across the board, though at a higher computational cost.

Models were trained using self-play generated data and optimized using cross-entropy loss with the Adam optimizer. Evaluation focused on:

* Win rate against baseline strategies
* Stability across edge-case board states
* Illegal move prevention via masking logic

Inference latency averaged 30–50 ms when deployed on AWS, which provided a smooth user experience.

---

## ☁️ Backend Deployment – AWS Lightsail + Docker

The backend runs on an Ubuntu 22.04 AWS Lightsail instance with a static IP. Docker is used to containerize the inference server, ensuring portability and reproducibility.

The container:

* Loads the trained model at startup
* Establishes a persistent Anvil Uplink connection
* Waits for inference calls
* Returns predictions synchronously

A simplified Dockerfile structure:

```dockerfile
FROM python:3.10
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
CMD ["python", "uplink_server.py"]
```

This ensures the environment remains consistent across deployments.

---

## 🔍 Integration Challenges and Solutions

During backend integration, several real-world issues emerged.

### CNN Response Input Shape Mismatch

During initial deployment, the CNN expected a specific tensor shape (e.g., `(1, 6, 7, channels)`), but the frontend occasionally sent improperly reshaped arrays. This caused runtime inference errors inside the Docker container.

**Root Cause:**  

* Inconsistent preprocessing between local training script and deployed inference server
* Missing batch dimension during AWS inference

**Fix:**  

* Standardized preprocessing pipeline
* Enforced reshaping inside backend:

  ```python
  board = np.reshape(board, (1, 6, 7, channels))
  ```

* Added strict validation before model prediction

This eliminated shape-related inference crashes.

### Transformer Version Compatibility Errors

When deploying the trained Transformer model to AWS, loading the `.h5` file produced compatibility errors related to:

* Custom layers
* Attention modules
* SavedModel format mismatches
* TensorFlow version inconsistencies between local training and AWS environment

**Root Cause:**
The model was originally trained using a newer TensorFlow version locally, while the Docker container had a slightly older runtime version.

**Solution:**  
To fix this, we:

1. Aligned TensorFlow versions explicitly in `requirements.txt`
2. Rebuilt the Docker container with pinned dependencies
3. Ultimately **recreated the Transformer model architecture from scratch inside the deployment environment**

Instead of loading a serialized model directly, we:

* Reconstructed the architecture programmatically
* Loaded only the model weights
* Ensured layer definitions matched exactly

This removed version-specific serialization conflicts and restored stable loading.

### Frontend State Synchronization

Asynchronous calls occasionally created UI state mismatches.

**Solution:**  
Board interactions were locked until inference returned, ensuring atomic state updates.  

These debugging steps significantly improved system reliability.

---

## 🚀 How to Deploy Your Own Version

Even beginner Python users can replicate this deployment by following these steps:

### 1. Clone the Anvil Project

Use the provided clone link inside your Anvil workspace.

### 2. Create an AWS Lightsail Instance

Select Ubuntu 22.04 and allocate at least 1GB RAM.

### 3. Install Docker

```bash
sudo apt update
sudo apt install docker.io
```

### 4. Build and Run the Container

```bash
docker build -t connect4-ai .
docker run -d connect4-ai
```

### 5. Update the Uplink Key

Replace the key in `uplink_server.py` with your own from Anvil.

### 6. Publish the Anvil App

Navigate to:

```text
Settings → Publish App
```

and assign your custom URL.

---

## 🎓 Key Takeaways

This project demonstrates how optimization and machine learning concepts can be translated into a production-ready system. It integrates:

* Deep learning model deployment
* Cloud infrastructure
* Containerization
* Secure authentication
* Client-server architecture
* Real-time inference pipelines

It bridges the gap between academic modeling and real-world system engineering.

---

## 🌐 Live Application

**Live App:**  
[https://msba25optim2-31.anvil.app/](https://msba25optim2-31.anvil.app/)

**Public Demo Credentials**  

```markdown
Username: `external`
Password: `external`
```

**Clone the Anvil App:**  
[https://anvil.works/build#clone:A5YOXSRTDDAYATEU=JKX5AXNZVSIHGQOSOK76](https://anvil.works/build#clone:A5YOXSRTDDAYATEU=JKX5AXNZVSIHGQOSOK76)  

---

## 📄 License

This project is licensed under the **MIT License**.
You are free to use, modify, distribute, and deploy this software with proper attribution.

---

## 📌 Academic Context

**Optimization II (RM 294.2)**
MSBA Program – UT Austin, McCombs School of Business

Instructor: **[Dan Mitchell](https://www.linkedin.com/in/dan-mitchell-8297189/)**

This project was developed as part of the Optimization II course, with a focus on building and deploying optimization-driven AI systems in real-world production environments.

---

## 👥 Team Members

* **[Abhiroop Kumar](https://www.linkedin.com/in/abhiroop-kumar/)**
* **[Frank Rong](https://www.linkedin.com/in/frankrong/)**
* **[Kristen Lowe](https://www.linkedin.com/in/kristen-lowe-atx/)**
* **[Lena Weissman](https://www.linkedin.com/in/lenaweissman/)**

---
