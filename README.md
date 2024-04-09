
# TutorTron

## Your Round-the-Clock AI-Powered Assistant for Instant Academic Support and Interactive Learning

TutorTron is designed to offer seamless support and an interactive learning experience. Follow these instructions to set up and run the application.

### Prerequisites

Before you begin, ensure you have the following:

- Python installed on your system
- A `users.csv` file prepared with your user data
- A `data` folder populated with your PDF files for academic resources
- Setup .env with your openai API

### Installation
Open your terminal or command prompt and navigate to the directory where you have TutorTron. Install the required Python packages by running:

```shell
pip install -r requirements.txt
```
### Prepare Your Files and Folders

Before running the application, ensure that your files and folders are properly set up.
Create or update the `users.csv` file in the project directory. This file should contain all the necessary user data.
Ensure that your `data` folder is ready. Fill it with the PDF files that you plan to use within TutorTron. This folder should be in the project directory.

### Running the Application

After preparing your files and folders, you can proceed to run the application.
To set up your database, run the following command in your terminal or command prompt:

```shell
python create_db.py
```
### Launch the Application
Open your terminal or command prompt and execute the following command:

```shell
streamlit run app.py
```

### Admin/Instructor Panel and Settings

One can: 
- Manage academic files (upload/delete) via the admin panel
- Adjust the document path
- Adjust generation temperature
through the admin panel. The `assistant_config.json` file is updated with the change in document path and/or the change in temperature. To access the panel, open your terminal or command prompt and execute the following command:

```shell
streamlit run admin.py
```
**Please note** that after changing assistant configurations, you'll need to clear streamlit's cache and session state, and reload the application for the change to be properly applied and reflected in the assistant.

