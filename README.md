# AI Travel Assistant Chat

A minimalistic chat application with an AI travel assistant built with Streamlit and OpenAI.

## Features

- **Left Panel**: Manage multiple conversations
- **Main Chat Area**: Interactive chat interface with the AI travel assistant
- **Backend**: OpenAI API integration with travel assistant role

## Setup

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Create a `.env` file in the root directory and add your configuration:
```bash
# Copy the example file
cp .env.example .env

# Then edit .env and add your configuration
OPENAI_API_KEY=your-actual-api-key-here
APP_PASSWORD=your-secure-password-here
```

   Alternatively, you can set them as environment variables:
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

## Security

- The app is password-protected. Set a strong `APP_PASSWORD` in your `.env` file
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

