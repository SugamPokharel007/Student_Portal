# OAuth Setup Guide for Sikshya Kendra

## Google OAuth Configuration

### Step 1: Create Google OAuth Credentials

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select an existing one
3. Enable the **Google+ API** or **Google Identity API**
4. Navigate to **APIs & Services** > **Credentials**
5. Click **Create Credentials** > **OAuth 2.0 Client ID**
6. Configure the OAuth consent screen if prompted:
   - Choose "External" for user type
   - Fill in the required fields (App name, User support email, etc.)
   - Add your domain to authorized domains
   - Add test users if in development

### Step 2: Configure OAuth Client

1. Application type: **Web application**
2. Name: "Sikshya Kendra" (or any name you prefer)
3. Authorized JavaScript origins:
   - `http://localhost:8000` (for local development)
   - `http://127.0.0.1:8000` (for local development)
   - `https://yourdomain.com` (for production)

4. Authorized redirect URIs:
   - `http://localhost:8000/oauth/google/callback/`
   - `http://127.0.0.1:8000/oauth/google/callback/`
   - `https://yourdomain.com/oauth/google/callback/`

5. Click **Create**
6. Copy the **Client ID** and **Client Secret**

### Step 3: Configure Environment Variables

Create a `.env` file in the `std_portal` directory with the following content:

```env
# Django Settings
SECRET_KEY=django-insecure-your-secret-key-here-change-this
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1

# Google OAuth Credentials
GOOGLE_CLIENT_ID=your-client-id-here.apps.googleusercontent.com
GOOGLE_CLIENT_SECRET=your-client-secret-here
```

Replace the values with your actual credentials.

## Facebook OAuth Configuration (Optional)

### Step 1: Create Facebook App

1. Go to [Facebook Developers](https://developers.facebook.com/)
2. Click **My Apps** > **Create App**
3. Choose **Consumer** as the app type
4. Fill in the app details

### Step 2: Configure Facebook Login

1. In your app dashboard, click **Add Product**
2. Find **Facebook Login** and click **Set Up**
3. Choose **Web**
4. Site URL: `http://localhost:8000` (for development)
5. Go to **Facebook Login** > **Settings**
6. Add Valid OAuth Redirect URIs:
   - `http://localhost:8000/oauth/facebook/callback/`
   - `https://yourdomain.com/oauth/facebook/callback/`

### Step 3: Add Credentials to .env

Add these lines to your `.env` file:

```env
# Facebook OAuth Credentials
FACEBOOK_APP_ID=your-facebook-app-id
FACEBOOK_APP_SECRET=your-facebook-app-secret
```

## Testing OAuth Login

1. Make sure your `.env` file is configured correctly
2. Run the Django development server:
   ```bash
   python manage.py runserver
   ```
3. Navigate to `http://localhost:8000/login/`
4. Click "Continue with Google" or "Continue with Facebook"
5. You should be redirected to the OAuth provider
6. After authorization, you'll be redirected back to the application

## Troubleshooting

### Common Issues

1. **"Google OAuth is not configured"**
   - Make sure `.env` file exists and contains `GOOGLE_CLIENT_ID` and `GOOGLE_CLIENT_SECRET`
   - Restart the Django server after adding environment variables

2. **"redirect_uri_mismatch" error**
   - Ensure the redirect URI in Google Console exactly matches: `http://localhost:8000/oauth/google/callback/`
   - Check for trailing slashes - they must match exactly

3. **"Invalid client" error**
   - Verify that your Client ID and Client Secret are correct
   - Check that the OAuth 2.0 client is not deleted or disabled

4. **Connection timeouts**
   - Check your internet connection
   - Verify that your firewall isn't blocking requests to Google/Facebook

### Security Notes

- Never commit your `.env` file to version control
- Add `.env` to your `.gitignore` file
- Use different credentials for development and production
- Regularly rotate your client secrets
- In production, use HTTPS for all OAuth redirect URIs

## Production Deployment

When deploying to production:

1. Update `ALLOWED_HOSTS` in `.env` to include your domain
2. Set `DEBUG=False`
3. Update all OAuth redirect URIs to use HTTPS and your domain
4. Use environment variables on your hosting platform instead of `.env` file
5. Ensure your domain is added to authorized domains in Google Console