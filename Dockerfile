# Use the Python 3.10.4 version of the Docker base image
FROM python:3.10.4-bullseye

# Copy the requirements file for Python dependencies
COPY requirements.txt ./

# Install and upgrade pip, then install the Python modules listed in requirements.txt
RUN pip install --no-cache-dir --upgrade pip && \
pip install --no-cache-dir -r ./requirements.txt

# Copy application files for the Flask server into the Docker image
COPY ./app /usr/src/app

# Set the working directory
WORKDIR /usr/src/app

# Set group write permissions on the instance directory 
# so the running app can modify the sqlite database file in it
# Note1: This approach is specific to running Docker on OpenShift.
#        It works because OpenShift creates a dedicated user to runs the server, 
#        and makes that user a member of the 'root' group
# Note2: Any changes to the database will be lost if the container is rerun.
#        To keep data between different container runs, use a separate persistent database like mysql
RUN chmod -R g+w /usr/src/app/instance

# Define the command to run when the container starts
CMD python app.py

