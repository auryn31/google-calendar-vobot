import { OAuth2Client } from 'google-auth-library';
import { calendar_v3, google } from 'googleapis';
import jwt from 'jsonwebtoken';
import { createClient } from '@supabase/supabase-js';

const supabase = createClient(
    process.env.SUPABASE_URL!,
    process.env.SUPABASE_SERVICE_ROLE_KEY!
  );


interface UserAuth {
    id: string;
    email: string;
    googleTokens: {
        access_token: string;
        refresh_token: string;
        expiry_date: number;
    };
}

const JWT_SECRET = process.env.JWT_SECRET || 'your-secret-key';
const oauth2Client = () => new OAuth2Client(
    process.env.GOOGLE_CLIENT_ID,
    process.env.GOOGLE_CLIENT_SECRET,
    process.env.GOOGLE_REDIRECT_URI
);
const getAuthUrl = () => {
    const scopes = [
        'https://www.googleapis.com/auth/calendar.readonly',
        'https://www.googleapis.com/auth/userinfo.email'
    ];

    return oauth2Client().generateAuthUrl({
        access_type: 'offline',
        scope: scopes,
        prompt: 'consent'
    });
}

const getCalendarEvents = async (token: string): Promise<calendar_v3.Schema$Event[]> => {
    try {
        // Verify JWT token
        const decoded = jwt.verify(token, JWT_SECRET) as { userId: string };
        
        // Get user from Supabase
        const { data: userAuth, error } = await supabase
            .from('user_auth')
            .select('*')
            .eq('id', decoded.userId)
            .single();

        if (error || !userAuth) {
            throw new Error('User not found');
        }

        const client = oauth2Client();
        client.setCredentials(userAuth.google_tokens);

        // Check if token needs refresh
        if (client.credentials.expiry_date && client.credentials.expiry_date < Date.now()) {
            const { credentials } = await client.refreshAccessToken();
            // Update tokens in database
            const { error: updateError } = await supabase
                .from('user_auth')
                .update({
                    google_tokens: {
                        access_token: credentials.access_token,
                        refresh_token: credentials.refresh_token || userAuth.google_tokens.refresh_token, // preserve existing refresh token if not updated
                        expiry_date: credentials.expiry_date
                    }
                })
                .eq('id', decoded.userId);

            if (updateError) {
                throw new Error('Failed to update tokens');
            }
        }

        // Get calendar events
        const calendar = google.calendar({ version: 'v3', auth: client });
        const response = await calendar.events.list({
            calendarId: 'primary',
            timeMin: new Date().toISOString(),
            maxResults: 10,
            singleEvents: true,
            orderBy: 'startTime',
        });

        return response.data.items || [];
    } catch (error) {
        console.error('Calendar event error:', error);
        throw new Error('Failed to get calendar events');
    }
}

const handleCallback = async (code: string): Promise<string> => {
    const client = oauth2Client();
    const { tokens } = await client.getToken(code);
    client.setCredentials(tokens);

    // Get user info
    const userInfo = await google.oauth2('v2').userinfo.get({
        auth: client
    });

    const userAuth: UserAuth = {
        id: userInfo.data.id!,
        email: userInfo.data.email!,
        googleTokens: {
            access_token: tokens.access_token!,
            refresh_token: tokens.refresh_token!,
            expiry_date: tokens.expiry_date!
        }
    };

    // Store user auth info in Supabase
    const { error } = await supabase
        .from('user_auth')
        .upsert({
            id: userAuth.id,
            email: userAuth.email,
            google_tokens: userAuth.googleTokens
        }, {
            onConflict: 'id'
        });

    if (error) {
        throw new Error('Failed to store user authentication');
    }

    // Generate JWT token
    return jwt.sign({ userId: userAuth.id }, JWT_SECRET);
}

export { getAuthUrl, getCalendarEvents, handleCallback };
