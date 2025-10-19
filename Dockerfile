FROM python:3.13-slim

# Set the working directory inside the container
WORKDIR /app

# Copy the requirements file first to leverage Docker cache
COPY requirements.txt .

# Install the Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of your bot's code into the container
COPY . .

# Specify the command to run when the container starts
# This assumes your main Python file is named 'bot.py'
# Change 'bot.py' to whatever your script is named!
CMD ["python", "bot.py"]
