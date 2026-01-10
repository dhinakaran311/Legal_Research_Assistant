# Setup Instructions

## Quick Start

1. **Install Dependencies:**
```bash
cd frontend
npm install
```

2. **Create Environment File:**
```bash
# Create .env.local file
cat > .env.local << EOF
NEXT_PUBLIC_BACKEND_URL=http://localhost:4000
NEXT_PUBLIC_GRAPHQL_URL=http://localhost:4000/graphql
EOF
```

3. **Start Development Server:**
```bash
npm run dev
```

4. **Open Browser:**
Navigate to [http://localhost:3000](http://localhost:3000)

## Prerequisites

- Node.js 20.x or higher
- Backend server running on port 4000

## Project Structure

```
frontend/
├── app/
│   ├── login/          # Login page
│   ├── signup/         # Signup page
│   ├── search/         # Search interface (placeholder)
│   └── layout.tsx      # Root layout
├── components/         # React components
├── contexts/           # React contexts (Auth)
├── lib/                # Utilities (Apollo, API)
└── package.json        # Dependencies
```

## Features Implemented

✅ Next.js 14 with App Router  
✅ TypeScript support  
✅ Tailwind CSS styling  
✅ Apollo Client for GraphQL  
✅ Authentication (Login/Signup)  
✅ Protected routes  
✅ User context management  

## Testing Authentication

1. Navigate to http://localhost:3000
2. You'll be redirected to `/login`
3. Click "Sign up" to create a new account
4. Fill in the form and submit
5. You'll be redirected to `/search` after successful signup
6. Logout and login again to test login flow

## Troubleshooting

### Module not found errors
Run `npm install` to install all dependencies.

### Backend connection errors
1. Ensure backend is running: `cd ../backend && npm run dev`
2. Check backend is on port 4000
3. Verify CORS is enabled in backend

### TypeScript errors
These should resolve after running `npm install`. The project uses Next.js 14 with TypeScript.
