# AI Travel Assistant Chat

A minimalistic chat application with an AI travel assistant built with Streamlit and OpenAI.

## Features

- **Left Panel**: Manage multiple conversations
- **Main Chat Area**: Interactive chat interface with the AI travel assistant
- **Backend**: OpenAI API integration with travel assistant role

## Local Setup

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. **Option A: Using `.env` file (recommended for local development)**
   ```bash
   # Create a .env file in the root directory
   OPENAI_API_KEY=your-actual-api-key-here
   APP_PASSWORD=your-secure-password-here
   ```

   **Option B: Using Streamlit secrets (mimics Cloud environment)**
   ```bash
   # Create .streamlit/secrets.toml
   mkdir .streamlit
   ```
   
   Add to `.streamlit/secrets.toml`:
   ```toml
   OPENAI_API_KEY = "your-actual-api-key-here"
   APP_PASSWORD = "your-secure-password-here"
   ```

   **Option C: Environment variables**
   ```bash
   # Windows PowerShell
   $env:OPENAI_API_KEY="your-api-key-here"
   $env:APP_PASSWORD="your-secure-password"
   
   # Windows CMD
   set OPENAI_API_KEY=your-api-key-here
   set APP_PASSWORD=your-secure-password
   
   # Linux/Mac
   export OPENAI_API_KEY=your-api-key-here
   export APP_PASSWORD=your-secure-password
   ```

3. Run the Streamlit app:
```bash
streamlit run app.py
```

## Deployment to Streamlit Cloud

1. Push your code to a GitHub repository (make sure `.env` is in `.gitignore`)

2. Go to [share.streamlit.io](https://share.streamlit.io) and deploy your app

3. In the Streamlit Cloud dashboard, go to **Settings** → **Secrets** and add:

```toml
OPENAI_API_KEY = "your-actual-api-key-here"
APP_PASSWORD = "your-secure-password-here"
```

4. Save and your app will automatically restart with the secrets loaded

## Security

- The app is password-protected. Set a strong `APP_PASSWORD` in your `.env` file (local) or Streamlit secrets (Cloud)
- Never commit your `.env` file to version control
- Conversation data is stored locally in `assets/conversations/` and excluded from git

## Project Structure

```
navan/
├── app.py               # Main Streamlit application
├── backend/
│   ├── chat.py          # OpenAI API integration
│   └── storage.py       # Conversation persistence
├── frontend/
│   └── utils.py         # UI utilities & authentication
├── assets/
│   └── conversations/   # Stored conversations (not in git)
├── .env                 # Environment variables (not in git)
├── .env.example         # Example environment file
├── requirements.txt     # Python dependencies
└── README.md            # This file
```

## Usage

1. Enter your password when prompted (set via `APP_PASSWORD` in `.env`)
2. Click "New Conversation" in the left panel to start a new chat
3. Type your travel-related questions in the chat input
4. The AI travel assistant will respond with helpful travel advice
5. Switch between conversations using the left panel
6. Delete unwanted conversations using the 🗑️ button

