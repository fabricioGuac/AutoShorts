# Auto Shorts

## Description 

**Auto Shorts** is an AI-powered dynamic short video generator for social media automation.  
Built in **Python**, it automatically creates and posts short-form videos to **YouTube Shorts** and **TikTok**, combining AI tools for scriptwriting, voiceovers, image generation, and scheduling.

###  Features
-  **Script generation** using **Gemini AI Flash 2.5**
-  **Voice narration** via **ElevenLabs API**
-  **Image generation** with **Stability API** *(or a local fallback using `runwayml/stable-diffusion-v1-5`)*
-  **Video assembly** (images + narration) handled with **MoviePy**
-  **Auto posting** to:
    - TikTok via **Selenium automation** (session-based, cookie-driven)
    - YouTube via **YouTube Data API**
-  **Scheduling** handled via **Windows Task Scheduler** or **cron** (on Linux/Mac)
-  **Data persistence** with **PostgreSQL**, storing:
    - User profiles, voice IDs
    - Prompt settings (topic, tone, pace)
    - Encrypted social tokens (YouTube OAuth, TikTok cookies)
    - Posting schedule

## Instalation

1. Clone or download this repository.
2. Make sure you have:
    * **Python 3.10+**
    * **PostgreSQL** installed and running locally.
3. Open your terminal in the project and run the following:

```bash

# 1. Create the database
psql -U your_user -c "CREATE DATABASE autoshorts_db;"

# 2. Apply the schema
psql -U your_user -d autoshorts_db -f db/schema.sql

# 3. Create a virtual environment
# Windows & Linux & Mac
py -m venv venv

# 4. Activate the virtual environment

# Windows (Command Prompt)
venv\Scripts\activate.bat

# Windows (PowerShell)
venv\Scripts\Activate.ps1

# Windows (Git Bash / WSL)
source venv/Scripts/activate

# Linux / MacOS
source venv/bin/activate

# 5. Install dependencies
py -m pip install -r requirements.txt
```

## Usage

1. Create a .env file in the project root with the following variables:
```

GOOGLE_API_KEY=your_google_ai_key
ELEVENLABS_API_KEY= your_elevenlabs_key
STABILITY_API_KEY= your_stability_key_or_blank_if_local

DB_NAME=autoshorts_db
DB_PASSWORD=your_postgres_password
DB_USER=your_postgres_user
DB_HOST=localhost
DB_PORT=5432

ENCRYPTION_KEY=your_generated_fernet_key

```

To generate an encryption key: 

```
from cryptography.fernet import Fernet
print(Fernet.generate_key().decode())
```


2. (Optional) If using **local image generation**, make sure your system meets the minimun GPU requirements:

  * 4GB VRAM (NVIDIA recommended)
  * 8-16GB RAM
  * ~12GB of storage (preferably on an SSD for faster loading)

3. Run the CLI:

```

py main.py

```

From there, you can:

* Create users and configure their prompt, voice, social tokens, and schedule.
* View, edit or delete existing users
* Manually trigger video generation.

## License

MIT License

Copyright (c) 2024 fabricioGuac

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.

## Questions

If you have any questions or need help with the project, feel free to contact me through the following channels: - Connect with me on GitHub at [fabricioGuac](https://github.com/fabricioGuac)  - Drop me an email at [guacutofabricio@gmail.com](https://github.com/guacutofabricio@gmail.com)   Don't hesitate to reach out if you need any clarifications or want to share feedback. I'm here to assist you!
