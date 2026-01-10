# Legal Research Assistant - Frontend

Next.js frontend application for the Legal Research Assistant platform.

## 🚀 Getting Started

### Prerequisites

- Node.js 20.x or higher
- npm or yarn

### Installation

1. Install dependencies:
```bash
npm install
```

2. Create environment file:
```bash
cp .env.example .env.local
```

3. Configure environment variables in `.env.local`:
```
NEXT_PUBLIC_BACKEND_URL=http://localhost:4000
NEXT_PUBLIC_GRAPHQL_URL=http://localhost:4000/graphql
```

### Development

Run the development server:

```bash
npm run dev
```

Open [http://localhost:3000](http://localhost:3000) in your browser.

### Build

Build for production:

```bash
npm run build
```

Start production server:

```bash
npm start
```

## 📁 Project Structure

```
frontend/
├── app/                    # Next.js 14 App Router
│   ├── layout.tsx         # Root layout with providers
│   ├── page.tsx           # Home page (redirects)
│   ├── login/             # Login page
│   ├── signup/            # Signup page
│   ├── search/            # Search interface
│   └── globals.css        # Global styles
├── components/            # React components
│   └── ApolloWrapper.tsx  # Apollo Client provider
├── contexts/              # React contexts
│   └── AuthContext.tsx    # Authentication context
├── lib/                   # Utilities and configurations
│   ├── apollo-client.ts   # Apollo Client setup
│   └── api.ts             # API utilities
└── package.json           # Dependencies
```

## 🔐 Authentication

The app uses JWT tokens stored in cookies for authentication:

- **Signup**: `/signup` - Create new account
- **Login**: `/login` - Sign in with existing account
- **Protected Routes**: Automatically redirect to login if not authenticated

### Auth API

- `POST /api/auth/signup` - Register new user
- `POST /api/auth/login` - Login user

Both endpoints return `{ user, token }` on success.

## 🛠️ Features

### ✅ Implemented

- ✅ Next.js 14 with App Router
- ✅ TypeScript support
- ✅ Tailwind CSS styling
- ✅ Apollo Client for GraphQL
- ✅ Authentication (Login/Signup)
- ✅ Protected routes
- ✅ User context management
- ✅ Cookie-based session storage

### 🚧 Coming Soon

- 🔄 Legal search interface
- 🔄 Search results display
- 🔄 Source citations viewer
- 🔄 Graph references visualization
- 🔄 User feedback collection

## 📡 API Integration

### GraphQL Endpoints

- `POST /graphql` - Main GraphQL endpoint

### REST Endpoints

- `POST /api/auth/signup` - User registration
- `POST /api/auth/login` - User login

## 🎨 Styling

The app uses Tailwind CSS with a custom color palette:

- Primary color: Blue (primary-500: #0ea5e9)
- Responsive design with mobile-first approach

## 🔧 Configuration

### Environment Variables

- `NEXT_PUBLIC_BACKEND_URL` - Backend API URL (default: http://localhost:4000)
- `NEXT_PUBLIC_GRAPHQL_URL` - GraphQL endpoint (default: http://localhost:4000/graphql)

### Backend Connection

Make sure the backend is running on port 4000:

```bash
cd ../backend
npm run dev
```

## 📝 Notes

- Authentication tokens are stored in cookies with 7-day expiration
- Protected routes automatically redirect to `/login` if not authenticated
- All API calls include authentication headers automatically

## 🐛 Troubleshooting

### Backend Connection Issues

1. Ensure backend is running on port 4000
2. Check CORS settings in backend
3. Verify environment variables are set correctly

### Authentication Issues

1. Clear browser cookies
2. Check token expiration
3. Verify backend authentication endpoints are working
