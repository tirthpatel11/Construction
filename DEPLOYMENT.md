# Deployment Instructions for Render

## Database Setup

The application requires a PostgreSQL database. On Render, you need to:

1. **Create the database service first:**
   - Go to your Render dashboard
   - Create a new PostgreSQL database
   - Name it `erp-db` (or update the name in `render.yaml`)
   - Wait for it to be fully provisioned

2. **Deploy the web service:**
   - The `render.yaml` file will automatically link the database
   - The `DATABASE_URL` environment variable will be set automatically
   - The web service will run migrations on startup

## Troubleshooting

If you see "Name or service not known" error:

1. **Check if the database exists:**
   - Go to Render dashboard → Databases
   - Ensure `erp-db` exists and is running

2. **Check the database link:**
   - Go to your web service settings
   - Check "Environment" tab
   - Verify `DATABASE_URL` is set

3. **Manual database link:**
   - If automatic linking fails, manually add the database:
     - Go to web service → Environment
     - Add environment variable: `DATABASE_URL`
     - Copy the "Internal Database URL" from your database service

## Local Development

For local development, the app will automatically use SQLite if `DATABASE_URL` is not set.

