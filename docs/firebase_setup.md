# Firebase Authentication Setup Guide

## Step 1: Enable Firebase in Google Cloud Console

1. Go to [Firebase Console](https://console.firebase.google.com/)
2. Click "Add project" and select your existing Google Cloud project
3. Follow the prompts to add Firebase to your project

## Step 2: Enable Authentication Providers

1. In Firebase Console, go to **Authentication** → **Sign-in method**
2. Enable **Email/Password**:
   - Click on "Email/Password"
   - Toggle "Enable" to ON
   - Click "Save"
3. Enable **Google**:
   - Click on "Google"
   - Toggle "Enable" to ON
   - Add your project's public-facing name
   - Select a support email
   - Click "Save"

## Step 3: Configure OAuth Consent Screen

1. Go to [Google Cloud Console → OAuth consent screen](https://console.cloud.google.com/apis/credentials/consent)
2. Select "External" user type (or Internal if using Workspace)
3. Fill in required fields:
   - App name: "Douban RAG System"
   - User support email: your email
   - Developer contact email: your email
4. Add scopes: `email`, `profile`, `openid`
5. Add test users if in testing mode

## Step 4: Get Firebase Config

1. In Firebase Console, go to **Project Settings** (gear icon)
2. Scroll to "Your apps" and click the web icon (`</>`)
3. Register your app with a nickname
4. Copy the config object values:

```javascript
const firebaseConfig = {
  apiKey: "YOUR_API_KEY",
  authDomain: "YOUR_PROJECT_ID.firebaseapp.com",
  projectId: "YOUR_PROJECT_ID",
  // ... other values
};
```

## Step 5: Set Environment Variables

Add these to your `.env` file:

```bash
FIREBASE_PROJECT_ID=your-project-id
FIREBASE_API_KEY=your-api-key
FIREBASE_AUTH_DOMAIN=your-project-id.firebaseapp.com
```

## Step 6: Download Service Account Key (for Backend)

1. Go to **Project Settings** → **Service accounts**
2. Click "Generate new private key"
3. Save the JSON file as `firebase-service-account.json` in the project root
4. **IMPORTANT**: Add this file to `.gitignore` to avoid committing secrets

## Verification

After setup, you should be able to:
- See Email/Password and Google enabled in Authentication → Sign-in method
- Have a valid `firebase-service-account.json` file
- Have all environment variables set in `.env`
