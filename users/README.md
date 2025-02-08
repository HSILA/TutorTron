# Handling Users

The current system relies on an authentication system to prevent unauthorized access to the chatbot, which would incur extra charges to the OpenAI API endpoint. Therefore, we need to allow only students enrolled in the course to access the chatbot.

## Inserting Users from CSV
The authentication system is based on the student's [MacID](https://uts.mcmaster.ca/services/accounts-and-passwords/macid/) and Student ID as the username and password respectively. The information about users should be provided as a CSV file, and the `user_handler.py` script extracts the users and their information from the CSV file and inserts them into a [Supabase](https://supabase.com/) database so the deployed chatbot can access. The CSV file for a course should have a specific structure and can be exported from [AvenueToLearn](https://avenue.cllmcmaster.ca/) by following the instructions below:

1. Go to the course page on Avenue.
2. Head to the **Assesment > Grades** section.
3. Click on the **Export** button.
4. In the opened page, leave **Export Grade Items For** as **All users**.
5. For the **Key Field**, select **Both**.
6. Under the **User Details**, select **Last Name**, **First Name** and **Email**.
7. Leave all the items in the **Grade Values** and **Choose Grades to Export** unchecked.
8. Click on the **Export to CSV** button, and when done, download the file.

The output file shoulde be something like this:
```csv
OrgDefinedId,Username,Last Name,First Name,Email,End-of-Line Indicator
#400123456,#doej,Doe,John,doej@avenue.cllmcmaster.ca,#
```
The number of columns, their order, and their format should exactly match the pattern above. If you are creating this file from scratch, you must ensure that the CSV file follows the same structure.

The next step is to create an account on the [Supabase](https://supabase.com/) platform and start a new project from the dashboard. On the **Create a New Project** page, enter a project name, set a secure database password, and select a region (US East is recommended). Once the project is created, you will see a page with details about your project. Use the following information in that page to populate necessary environment varialbes in a `.env` file (you can also find this information in the **Project Settings > Data API** section of the project dashboard):
- Project API Keys: `anon` or `public` as `SUPABASE_KEY` environment variable.
- Project URL as `SUPABASE_URL` environment variable.

The next step is to create a `users` table in the Supabase database. To do this, go to the **SQL Editor** in the left pane of your project and run the following SQL query:

```sql
CREATE TABLE users (
    macid TEXT PRIMARY KEY,
    first_name TEXT NOT NULL,
    last_name TEXT NOT NULL,
    student_number INT NOT NULL
);
```
Once the table is ready, you can use the following command to insert the users from the CSV file into the `users` table:

```bash
python users/user_handler.py --users-path path/to/users.csv
```

If you see the message **Users inserted successfully.**, it means the users have been successfully added to the database. You can also confirm this by checking the `users` table in the Table Editor section of your Supabase dashboard.

## Inserting a Single User
Instead of inserting all users from a CSV file, you have the option to insert a single user manually. To do this, you can use the following command:
```bash
python users/user_handler.py --macid <macid> --first-name <first_name> --last-name <last_name> --student-number <student_number>
```
A **User inserted successfully.** message means the user has been successfully added to the database.

## Setting up the Chatbot
To get the chatbot to work with the authentication system, you need to set up the environment variables in the `src/.streamlit/secrets.toml` file. The following environment variables are required:
```toml
SUPABASE_KEY="<your_supabase_key>"
SUPABASE_URL="<your_supabase_url>"
```