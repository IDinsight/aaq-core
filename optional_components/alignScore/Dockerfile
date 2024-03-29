# Use python:3.10 as the base image
FROM python:3.10

# Install git
RUN apt-get update && apt-get install -y git

# Set working directory
WORKDIR /app

# Clone and install the alignscore package
RUN git clone https://github.com/IDinsight/AlignScore.git
WORKDIR /app/AlignScore
RUN pip install .

# Download the Spacy en_core_web_sm model
RUN python -m spacy download en_core_web_sm

# Download the AlignScore base checkpoint
RUN curl -OL https://huggingface.co/yzha/AlignScore/resolve/main/AlignScore-base.ckpt

# Uncomment the line below to also download the large model
# RUN curl -OL https://huggingface.co/yzha/AlignScore/resolve/main/AlignScore-large.ckpt

# Switch
WORKDIR /app

# Copy the source code
COPY . /app

# Install the minimal set of requirements for AlignScore Server
RUN pip install -r requirements.txt

# Download the punkt model to speed up start time
RUN python -c "import nltk; nltk.download('punkt')"

# Set the ALIGN_SCORE_PATH environment variable
ENV ALIGN_SCORE_PATH=/app/AlignScore

# Set the device on which the model should load e.g., "cpu", "cuda:0", etc.
ENV ALIGN_SCORE_DEVICE=cpu

# Initialize the models
RUN python server.py --initialize-only

# Expose a port for the server
EXPOSE 5001

# Start the AlignScore server as the default command
CMD ["/usr/local/bin/python", "server.py", "--port=5001", "--models=base"]

HEALTHCHECK CMD curl -f http://localhost:5001/healthcheck || exit 1
