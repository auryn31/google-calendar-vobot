import dotenv from 'dotenv';
// Load environment variables
dotenv.config();

import express, { RequestHandler } from 'express';
import { getAuthUrl, handleCallback, getCalendarEvents } from './google_auth';


const app = express();

// Add middleware to parse JSON bodies
app.use(express.json());

// Add this before creating the OAuth2Client
process.env.NODE_TLS_REJECT_UNAUTHORIZED = '0';

// Define route handlers separately with explicit types
const handleGoogleAuth: RequestHandler = (req, res) => {
    const authUrl = getAuthUrl();
    res.redirect(authUrl);
};

const handleGoogleCallback: RequestHandler = async (req, res) => {
    const code = req.query.code as string;
    try {
        const token = await handleCallback(code);
        res.json({ token });
    } catch (error) {
        console.error('Authentication error:', error);
        res.status(500).json({ error: 'Authentication failed' });
    }
};

const handleCalendarEvents: RequestHandler = async (req, res) => {
    const token = req.headers.authorization?.split(' ')[1];
    if (!token) {
        res.status(401).json({ error: 'No token provided' });
        return;
    }

    try {
        const events = await getCalendarEvents(token);
        res.json(events);
    } catch (error) {
        console.error('Calendar error:', error);
        res.status(500).json({ error: 'Failed to fetch calendar events' });
    }
};

// Use the handlers
app.get('/auth/google', handleGoogleAuth);
app.get('/auth/google/callback', handleGoogleCallback);
app.get('/calendar/events', handleCalendarEvents);

const PORT = process.env.PORT || 3000;

app.listen(PORT, () => {
    console.log(`Server running on port ${PORT}`);
}); 