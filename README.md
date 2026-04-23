<div align="center">

<br/>

```
██╗     ██╗   ██╗██╗  ██╗███████╗    ███████╗███████╗████████╗ █████╗ ████████╗███████╗
██║     ██║   ██║╚██╗██╔╝██╔════╝    ██╔════╝██╔════╝╚══██╔══╝██╔══██╗╚══██╔══╝██╔════╝
██║     ██║   ██║ ╚███╔╝ █████╗      █████╗  ███████╗   ██║   ███████║   ██║   █████╗  
██║     ██║   ██║ ██╔██╗ ██╔══╝      ██╔══╝  ╚════██║   ██║   ██╔══██║   ██║   ██╔══╝  
███████╗╚██████╔╝██╔╝ ██╗███████╗    ███████╗███████║   ██║   ██║  ██║   ██║   ███████╗
╚══════╝ ╚═════╝ ╚═╝  ╚═╝╚══════╝    ╚══════╝╚══════╝   ╚═╝   ╚═╝  ╚═╝   ╚═╝   ╚══════╝
```

<h3>🏛️ Where Prestige Meets Property</h3>

<p>
  <img src="https://img.shields.io/badge/Status-Live-brightgreen?style=for-the-badge&logo=checkmarx" />
  <img src="https://img.shields.io/badge/React-18.x-61DAFB?style=for-the-badge&logo=react" />
  <img src="https://img.shields.io/badge/Node.js-18.x-339933?style=for-the-badge&logo=nodedotjs" />
  <img src="https://img.shields.io/badge/MongoDB-7.x-47A248?style=for-the-badge&logo=mongodb" />
  <img src="https://img.shields.io/badge/Tailwind-3.x-06B6D4?style=for-the-badge&logo=tailwindcss" />
</p>

<p>
  <img src="https://img.shields.io/github/stars/jainam-shah-18/LuxeEstate?style=social" />
  <img src="https://img.shields.io/github/forks/jainam-shah-18/LuxeEstate?style=social" />
  <img src="https://img.shields.io/github/issues/jainam-shah-18/LuxeEstate?color=red" />
  <img src="https://img.shields.io/github/license/jainam-shah-18/LuxeEstate" />
</p>

<br/>

> *"Luxury is not about price — it's about the experience."*  
> **LuxeEstate** delivers a premium, end-to-end real estate platform built for discerning buyers, elite agents, and modern property investors.

<br/>

---

</div>

## 📸 Preview

<div align="center">

| 🏠 Homepage | 🔍 Property Search | 📊 Agent Dashboard |
|:-----------:|:------------------:|:-----------------:|
| ![Home](https://via.placeholder.com/280x180/1a1a2e/gold?text=LuxeEstate+Home) | ![Search](https://via.placeholder.com/280x180/16213e/C9A84C?text=Property+Search) | ![Dashboard](https://via.placeholder.com/280x180/0f3460/D4AF37?text=Agent+Dashboard) |

</div>

---

## 🌟 Why LuxeEstate?

The real estate industry is flooded with generic listing platforms. **LuxeEstate** is different — it's engineered for the **top 1%** of properties and the professionals who sell them.

| Feature | Generic Platforms | LuxeEstate |
|---------|:-----------------:|:----------:|
| Real-time listing updates | ❌ | ✅ |
| AI-assisted property search | ❌ | ✅ |
| Agent performance analytics | ❌ | ✅ |
| Interactive map exploration | ❌ | ✅ |
| Luxury-tier UI/UX | ❌ | ✅ |
| Mobile-first responsive design | ⚠️ Partial | ✅ |

---

## 🏗️ Architecture Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                        CLIENT LAYER                             │
│   React 18  ·  Tailwind CSS  ·  Framer Motion  ·  Leaflet.js  │
└─────────────────────────┬───────────────────────────────────────┘
                          │  REST API / WebSocket
┌─────────────────────────▼───────────────────────────────────────┐
│                        SERVER LAYER                             │
│          Node.js  ·  Express.js  ·  JWT Auth  ·  Socket.io     │
└─────────────────────────┬───────────────────────────────────────┘
                          │
┌─────────────────────────▼───────────────────────────────────────┐
│                        DATA LAYER                               │
│       MongoDB Atlas  ·  Redis Cache  ·  Cloudinary (Media)     │
└─────────────────────────────────────────────────────────────────┘
```

---

## ✨ Features

### 🔎 Smart Property Discovery
- **Advanced Filters** — Bedrooms, bathrooms, price range, area (sq. ft.), amenities, year built
- **Interactive Map** — Leaflet.js powered geo-search with neighborhood overlays
- **AI Suggestions** — "Properties you might love" engine based on browsing history
- **Virtual Tour** — 360° image carousel with full-screen mode

### 👤 User Roles & Portals
| Role | Capabilities |
|------|-------------|
| **Buyer** | Browse listings, save favorites, schedule tours, chat with agents |
| **Seller** | List properties, upload media, track inquiries, manage showings |
| **Agent** | Manage portfolio, analytics dashboard, lead pipeline, commission tracker |
| **Admin** | Full platform control, user management, content moderation |

### 📊 Agent Analytics Dashboard
- Monthly leads & conversion rates
- Property performance heatmaps
- Commission revenue breakdown
- Client communication timeline

### 🔐 Security & Auth
- JWT-based authentication with refresh tokens
- Role-based access control (RBAC)
- bcrypt password hashing
- Rate limiting & CSRF protection

### 📱 Experience Highlights
- Fully responsive — pixel-perfect on mobile, tablet, and desktop
- Dark/Light mode with smooth transitions
- Skeleton loading screens for perceived performance
- Toast notifications & real-time updates via Socket.io

---

## 🛠️ Tech Stack

<div align="center">

### Frontend
![React](https://img.shields.io/badge/React-20232A?style=for-the-badge&logo=react&logoColor=61DAFB)
![TailwindCSS](https://img.shields.io/badge/Tailwind_CSS-38B2AC?style=for-the-badge&logo=tailwind-css&logoColor=white)
![Framer](https://img.shields.io/badge/Framer_Motion-black?style=for-the-badge&logo=framer&logoColor=blue)
![Leaflet](https://img.shields.io/badge/Leaflet.js-199900?style=for-the-badge&logo=leaflet&logoColor=white)

### Backend
![NodeJS](https://img.shields.io/badge/Node.js-43853D?style=for-the-badge&logo=node.js&logoColor=white)
![Express.js](https://img.shields.io/badge/Express.js-404D59?style=for-the-badge)
![MongoDB](https://img.shields.io/badge/MongoDB-4EA94B?style=for-the-badge&logo=mongodb&logoColor=white)
![Redis](https://img.shields.io/badge/Redis-DC382D?style=for-the-badge&logo=redis&logoColor=white)

### DevOps & Tools
![Docker](https://img.shields.io/badge/Docker-2496ED?style=for-the-badge&logo=docker&logoColor=white)
![Cloudinary](https://img.shields.io/badge/Cloudinary-3448C5?style=for-the-badge&logo=cloudinary&logoColor=white)
![Socket.io](https://img.shields.io/badge/Socket.io-black?style=for-the-badge&logo=socket.io&badgeColor=010101)

</div>

---

## 📁 Project Structure

```
LuxeEstate/
│
├── 📂 client/                      # React Frontend
│   ├── 📂 public/
│   │   └── index.html
│   ├── 📂 src/
│   │   ├── 📂 assets/              # Images, icons, fonts
│   │   ├── 📂 components/
│   │   │   ├── Navbar.jsx
│   │   │   ├── PropertyCard.jsx
│   │   │   ├── SearchBar.jsx
│   │   │   ├── MapView.jsx
│   │   │   ├── FilterPanel.jsx
│   │   │   └── ImageCarousel.jsx
│   │   ├── 📂 pages/
│   │   │   ├── Home.jsx
│   │   │   ├── Listings.jsx
│   │   │   ├── PropertyDetail.jsx
│   │   │   ├── Dashboard.jsx
│   │   │   ├── AgentProfile.jsx
│   │   │   └── Auth/
│   │   │       ├── Login.jsx
│   │   │       └── Register.jsx
│   │   ├── 📂 context/
│   │   │   ├── AuthContext.jsx
│   │   │   └── PropertyContext.jsx
│   │   ├── 📂 hooks/
│   │   │   ├── useAuth.js
│   │   │   └── useProperties.js
│   │   ├── 📂 services/
│   │   │   └── api.js
│   │   └── App.jsx
│   └── package.json
│
├── 📂 server/                      # Node.js Backend
│   ├── 📂 config/
│   │   ├── db.js
│   │   └── cloudinary.js
│   ├── 📂 controllers/
│   │   ├── authController.js
│   │   ├── propertyController.js
│   │   ├── userController.js
│   │   └── agentController.js
│   ├── 📂 middleware/
│   │   ├── authMiddleware.js
│   │   ├── errorHandler.js
│   │   └── rateLimiter.js
│   ├── 📂 models/
│   │   ├── User.js
│   │   ├── Property.js
│   │   ├── Agent.js
│   │   └── Inquiry.js
│   ├── 📂 routes/
│   │   ├── authRoutes.js
│   │   ├── propertyRoutes.js
│   │   ├── userRoutes.js
│   │   └── agentRoutes.js
│   ├── 📂 utils/
│   │   ├── generateToken.js
│   │   └── sendEmail.js
│   └── server.js
│
├── 📂 uploads/                     # Temporary media storage
├── .env.example
├── docker-compose.yml
└── README.md
```

---

## 🚀 Getting Started

### Prerequisites

Make sure you have the following installed:

| Tool | Version |
|------|---------|
| Node.js | ≥ 18.x |
| npm / yarn | ≥ 9.x |
| MongoDB | Atlas or Local |
| Git | Latest |

### 1️⃣ Clone the Repository

```bash
git clone https://github.com/jainam-shah-18/LuxeEstate.git
cd LuxeEstate
```

### 2️⃣ Setup Environment Variables

```bash
# In /server directory
cp .env.example .env
```

Edit `.env` with your credentials:

```env
# Server
PORT=5000
NODE_ENV=development

# MongoDB
MONGO_URI=mongodb+srv://<username>:<password>@cluster.mongodb.net/luxeestate

# JWT
JWT_SECRET=your_super_secret_key_here
JWT_EXPIRES_IN=7d

# Cloudinary (Media Storage)
CLOUDINARY_CLOUD_NAME=your_cloud_name
CLOUDINARY_API_KEY=your_api_key
CLOUDINARY_API_SECRET=your_api_secret

# Redis
REDIS_URL=redis://localhost:6379

# Email (Nodemailer)
EMAIL_USER=your_email@gmail.com
EMAIL_PASS=your_app_password
```

### 3️⃣ Install Dependencies

```bash
# Install backend dependencies
cd server
npm install

# Install frontend dependencies
cd ../client
npm install
```

### 4️⃣ Run the Application

```bash
# Terminal 1 — Start backend server
cd server
npm run dev

# Terminal 2 — Start frontend dev server
cd client
npm start
```

### 🐳 Docker (Optional)

```bash
# Build and run entire stack
docker-compose up --build

# Stop all services
docker-compose down
```

> 🌐 App runs at: `http://localhost:3000`  
> 🔧 API runs at: `http://localhost:5000/api`

---

## 🔌 API Reference

### Authentication Endpoints

| Method | Endpoint | Description | Auth Required |
|--------|----------|-------------|:-------------:|
| `POST` | `/api/auth/register` | Register new user | ❌ |
| `POST` | `/api/auth/login` | Login & get JWT | ❌ |
| `POST` | `/api/auth/logout` | Invalidate token | ✅ |
| `GET` | `/api/auth/me` | Get current user | ✅ |

### Property Endpoints

| Method | Endpoint | Description | Auth Required |
|--------|----------|-------------|:-------------:|
| `GET` | `/api/properties` | Get all listings (paginated) | ❌ |
| `GET` | `/api/properties/:id` | Get single property | ❌ |
| `POST` | `/api/properties` | Create new listing | ✅ Seller/Admin |
| `PUT` | `/api/properties/:id` | Update listing | ✅ Owner/Admin |
| `DELETE` | `/api/properties/:id` | Delete listing | ✅ Owner/Admin |
| `GET` | `/api/properties/search` | Filter & search listings | ❌ |

### Agent Endpoints

| Method | Endpoint | Description | Auth Required |
|--------|----------|-------------|:-------------:|
| `GET` | `/api/agents` | List all agents | ❌ |
| `GET` | `/api/agents/:id` | Agent profile | ❌ |
| `GET` | `/api/agents/:id/stats` | Agent analytics | ✅ Agent |
| `POST` | `/api/agents/inquiry` | Send inquiry to agent | ✅ |

---

## 📊 Database Schema

### Property Model

```javascript
{
  title: String,               // "3BHK Luxury Apartment in Banjara Hills"
  description: String,
  price: Number,               // In INR or USD
  location: {
    address: String,
    city: String,
    state: String,
    pincode: String,
    coordinates: {
      lat: Number,
      lng: Number
    }
  },
  propertyType: String,        // apartment | villa | plot | commercial
  status: String,              // for-sale | for-rent | sold
  bedrooms: Number,
  bathrooms: Number,
  area: Number,                // sq. ft.
  amenities: [String],         // ["Pool", "Gym", "Parking", "Security"]
  images: [String],            // Cloudinary URLs
  agent: ObjectId,             // ref: Agent
  owner: ObjectId,             // ref: User
  views: Number,
  isFeatured: Boolean,
  createdAt: Date
}
```

### User Model

```javascript
{
  name: String,
  email: String,
  password: String,            // bcrypt hashed
  role: String,                // buyer | seller | agent | admin
  avatar: String,
  phone: String,
  savedProperties: [ObjectId],
  createdAt: Date
}
```

---

## 🎨 UI Component Gallery

```
Components Used:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  🔹 HeroSection        → Full-screen animated hero with search
  🔹 PropertyCard       → Glassmorphism card with hover effects
  🔹 FilterSidebar      → Collapsible advanced search panel
  🔹 MapView            → Leaflet map with custom markers
  🔹 ImageGallery       → Lightbox photo viewer
  🔹 AgentCard          → Profile card with rating & stats
  🔹 InquiryModal       → Contact form with validation
  🔹 DashboardChart     → Recharts analytics widgets
  🔹 PriceRange Slider  → Dual-handle range input
  🔹 Skeleton Loader    → Shimmer loading placeholders
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

---

## 🔒 Security Practices

- ✅ **JWT Authentication** with short-lived access tokens + refresh tokens
- ✅ **Password Hashing** using bcrypt with salt rounds = 12
- ✅ **Rate Limiting** — 100 req/15min per IP via `express-rate-limit`
- ✅ **CORS** configured for whitelisted origins only
- ✅ **Input Validation** using `express-validator`
- ✅ **MongoDB Injection** prevention via Mongoose sanitization
- ✅ **Helmet.js** for secure HTTP headers
- ✅ **Environment Variables** — zero hardcoded secrets

---

## 🧪 Testing

```bash
# Run backend unit tests
cd server
npm test

# Run frontend component tests
cd client
npm test

# Coverage report
npm run test:coverage
```

Test coverage targets:
- Controllers: `≥ 85%`
- Models: `≥ 90%`
- API Routes: `≥ 80%`

---

## 📦 Deployment

### Deploy to Vercel (Frontend)

```bash
cd client
vercel --prod
```

### Deploy to Render (Backend)

```bash
# Push to GitHub → Connect Render → Set env vars → Auto-deploy
```

### Deploy with Docker

```bash
docker build -t luxeestate-server ./server
docker build -t luxeestate-client ./client
docker-compose -f docker-compose.prod.yml up -d
```

---

## 🗺️ Roadmap

| Milestone | Status |
|-----------|--------|
| Core listings CRUD | ✅ Done |
| User authentication | ✅ Done |
| Agent dashboard | ✅ Done |
| Map integration | ✅ Done |
| Real-time messaging | 🚧 In Progress |
| AI property recommendations | 📋 Planned |
| EMI calculator | 📋 Planned |
| Mortgage partner integration | 📋 Planned |
| Mobile App (React Native) | 📋 Planned |

---

## 🤝 Contributing

Contributions make the open-source community an amazing place to learn and create. Any contributions are **greatly appreciated**!

```bash
# Step 1: Fork the repository

# Step 2: Create your feature branch
git checkout -b feature/AmazingFeature

# Step 3: Commit your changes
git commit -m 'feat: Add AmazingFeature'

# Step 4: Push to the branch
git push origin feature/AmazingFeature

# Step 5: Open a Pull Request
```

Please follow [Conventional Commits](https://www.conventionalcommits.org/) for commit messages.

---

## 📄 License

Distributed under the **MIT License**. See [`LICENSE`](LICENSE) for more information.

---

## 👨‍💻 Author

<div align="center">

<img src="https://github.com/jainam-shah-18.png" width="100" style="border-radius:50%"/>

**Jainam Shah**  
Data Scientist · Full Stack Developer · ML Enthusiast

[![GitHub](https://img.shields.io/badge/GitHub-jainam--shah--18-181717?style=for-the-badge&logo=github)](https://github.com/jainam-shah-18)
[![LinkedIn](https://img.shields.io/badge/LinkedIn-Connect-0077B5?style=for-the-badge&logo=linkedin)](https://linkedin.com/in/jainam-shah)

</div>

---

<div align="center">

**⭐ If this project helped you, please consider giving it a star! ⭐**

*Built with ❤️ from Ahmedabad, India 🇮🇳*

</div>
